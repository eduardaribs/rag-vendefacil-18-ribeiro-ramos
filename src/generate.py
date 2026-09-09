
import os
import re
from difflib import SequenceMatcher
from typing import Callable, Optional

from pydantic import ValidationError
from langchain_groq import ChatGroq

from src.schema import RAGResponse, SourceEvidence
from src.retrieve import buscar_hibrido
from src.guardrails import (
    aplicar_guardrails_lgpd,
    verificar_fora_de_escopo,
)


# ============================================================
# CONFIGURAÇÃO DO LLM
# ============================================================

MODELO_LLM = "openai/gpt-oss-20b"

llm = ChatGroq(
    model=MODELO_LLM,
    temperature=0,
)

# Usa Structured Outputs nativo do Groq em vez de
# function calling. Isso evita erros como:
#
# - functions.RAGResponse
# - malformed tool-call JSON
# - Failed to parse tool call arguments
#
# O modelo openai/gpt-oss-20b suporta JSON Schema nativamente.
llm_estruturado = llm.with_structured_output(
    RAGResponse,
    method="json_schema",
    strict=True,
)


# ============================================================
# HELPERS DE METADADOS
# ============================================================

def obter_filepath(doc) -> str:
    """
    Obtém o caminho do arquivo de origem do documento.
    """

    return str(
        doc.metadata.get(
            "source_file",
            "desconhecido"
        )
    )


def obter_chunk_id(doc) -> str:
    """
    Obtém o identificador único do chunk.
    """

    return str(
        doc.metadata.get(
            "chunk_id",
            "desconhecido"
        )
    )


# ============================================================
# CITAÇÕES LITERAIS AUTORIZADAS
# ============================================================

def gerar_citacoes_autorizadas(
    doc,
    tamanho: int = 220,
    sobreposicao: int = 40,
) -> list[str]:
    """
    Divide o conteúdo do documento em trechos literais menores.

    Esses trechos são disponibilizados ao LLM para evitar
    citações inventadas ou citações maiores que o limite
    definido no schema.

    Citações que contenham dados que precisariam ser
    mascarados ou recusados pelo guardrail são evitadas.
    """

    texto = str(
        doc.page_content
    ).strip()

    if not texto:
        return []

    citacoes = []

    inicio = 0

    while inicio < len(texto):

        fim = min(
            inicio + tamanho,
            len(texto)
        )

        trecho = texto[
            inicio:fim
        ].strip()

        if trecho:

            resultado_guardrail = aplicar_guardrails_lgpd(
                trecho
            )

            # Só disponibilizamos como evidência literal
            # trechos que podem ser exibidos sem mascaramento.
            if (
                resultado_guardrail.get("status")
                == "permitido"
            ):
                citacoes.append(
                    trecho
                )

        if fim >= len(texto):
            break

        inicio = max(
            fim - sobreposicao,
            inicio + 1
        )

    # Caso nenhuma citação segura tenha sido encontrada,
    # tenta trechos menores.
    if not citacoes:

        tamanho_reduzido = 140
        inicio = 0

        while inicio < len(texto):

            fim = min(
                inicio + tamanho_reduzido,
                len(texto)
            )

            trecho = texto[
                inicio:fim
            ].strip()

            if trecho:

                resultado_guardrail = aplicar_guardrails_lgpd(
                    trecho
                )

                if (
                    resultado_guardrail.get("status")
                    == "permitido"
                ):
                    citacoes.append(
                        trecho
                    )

            if fim >= len(texto):
                break

            inicio = fim

    return citacoes


def construir_catalogo_citacoes(
    documentos
) -> dict:
    """
    Cria catálogo:

    chunk_id -> lista de citações literais autorizadas.
    """

    catalogo = {}

    for doc in documentos:

        chunk_id = obter_chunk_id(
            doc
        )

        catalogo[
            chunk_id
        ] = gerar_citacoes_autorizadas(
            doc
        )

    return catalogo


# ============================================================
# CONTEXTO PARA O LLM
# ============================================================

def construir_contexto(
    documentos
) -> str:
    """
    Constrói o contexto enviado ao LLM.

    O conteúdo original é apresentado junto das citações
    literais autorizadas para cada chunk.
    """

    blocos = []

    for indice, doc in enumerate(
        documentos,
        start=1
    ):

        filepath = obter_filepath(
            doc
        )

        chunk_id = obter_chunk_id(
            doc
        )

        citacoes = gerar_citacoes_autorizadas(
            doc
        )

        citacoes_formatadas = []

        for numero, citacao in enumerate(
            citacoes,
            start=1
        ):

            citacoes_formatadas.append(
                f"Citação {numero}: {citacao}"
            )

        bloco = f"""
DOCUMENTO {indice}

filepath:
{filepath}

chunk_id:
{chunk_id}

conteúdo:
{doc.page_content}

CITAÇÕES LITERAIS AUTORIZADAS:
{chr(10).join(citacoes_formatadas) if citacoes_formatadas else "Nenhuma citação segura disponível."}
"""

        blocos.append(
            bloco.strip()
        )

    return "\n\n" + "\n\n".join(
        blocos
    )


# ============================================================
# RESPOSTAS DE RECUSA
# ============================================================

def criar_recusa(
    motivo: str,
    reasoning: str,
    answer: Optional[str] = None,
) -> RAGResponse:
    """
    Cria uma RAGResponse válida de recusa.
    """

    mensagens = {
        "lgpd": (
            "Não posso fornecer essa informação porque "
            "ela envolve dados pessoais sensíveis ou restritos."
        ),
        "fora_de_escopo": (
            "Não posso responder essa pergunta porque ela "
            "está fora do escopo da VendeFácil."
        ),
        "sem_evidencia": (
            "Não encontrei evidências suficientes nos "
            "documentos disponíveis para responder com segurança."
        ),
    }

    return RAGResponse(
        answer=(
            answer
            or mensagens.get(
                motivo,
                "Não foi possível responder à solicitação."
            )
        ),
        confidence_level="recusado",
        sources_used=[],
        reasoning=reasoning,
        is_refusal=True,
        refusal_reason=motivo,
    )


# ============================================================
# RETRY GENÉRICO
# ============================================================

def validar_com_retry(
    gerador: Callable,
    tentativas: int = 2,
) -> RAGResponse:
    """
    Executa uma função geradora e valida sua saída com Pydantic.

    Se a validação falhar, uma nova tentativa é feita.

    Não utiliza except: pass.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resultado = gerador()

            if isinstance(
                resultado,
                RAGResponse
            ):
                return resultado

            return RAGResponse.model_validate(
                resultado
            )

        except ValidationError as erro:

            ultimo_erro = erro

            print(
                f"Falha de validação Pydantic "
                f"na tentativa {tentativa}/{tentativas}."
            )

    raise RuntimeError(
        "Não foi possível produzir uma resposta válida "
        f"após {tentativas} tentativas. "
        f"Último erro: {ultimo_erro}"
    )


# ============================================================
# CORREÇÃO DETERMINÍSTICA DE QUOTATION
# ============================================================

def encontrar_trecho_literal_mais_proximo(
    quotation: str,
    conteudo: str,
    limite: int = 500,
):
    """
    Procura, dentro do próprio chunk recuperado, o trecho literal
    mais semelhante à quotation produzida pelo LLM.

    A função NÃO cria nem parafraseia evidências.
    O valor retornado sempre é substring literal do documento.

    Estratégia:
    1. tenta correspondência exata;
    2. tenta diferença apenas de espaços;
    3. compara linhas/parágrafos literais;
    4. compara janelas de sentenças;
    """

    quotation = str(
        quotation or ""
    ).strip()

    conteudo = str(
        conteudo or ""
    )

    if not quotation or not conteudo:
        return None

    # --------------------------------------------------------
    # 1. EXATO
    # --------------------------------------------------------

    if quotation in conteudo:
        return quotation

    # --------------------------------------------------------
    # 2. APENAS ESPAÇOS / QUEBRAS DE LINHA
    # --------------------------------------------------------

    tokens = quotation.split()

    if tokens:

        padrao = r"\s+".join(
            re.escape(token)
            for token in tokens
        )

        correspondencia = re.search(
            padrao,
            conteudo,
            flags=re.DOTALL
        )

        if correspondencia:

            trecho = correspondencia.group(
                0
            ).strip()

            if len(trecho) <= limite:
                return trecho

    # --------------------------------------------------------
    # NORMALIZAÇÃO APENAS PARA COMPARAR
    # --------------------------------------------------------

    def normalizar_comparacao(valor: str) -> str:

        valor = str(valor)

        # Markdown não altera conteúdo semântico.
        valor = valor.replace(
            "**",
            ""
        )

        valor = valor.replace(
            "__",
            ""
        )

        valor = valor.replace(
            "`",
            ""
        )

        valor = re.sub(
            r"\s+",
            " ",
            valor
        )

        return valor.strip().lower()

    quotation_normalizada = (
        normalizar_comparacao(
            quotation
        )
    )

    # --------------------------------------------------------
    # 3. CANDIDATOS LITERAIS
    # --------------------------------------------------------

    candidatos = []

    # Parágrafos / linhas
    blocos = re.split(
        r"\n\s*\n|\n",
        conteudo
    )

    for bloco in blocos:

        bloco = bloco.strip()

        if (
            bloco
            and len(bloco) <= limite
        ):
            candidatos.append(
                bloco
            )

    # Sentenças
    sentencas = re.split(
        r"(?<=[.!?;:])\s+",
        conteudo
    )

    sentencas = [
        s.strip()
        for s in sentencas
        if s.strip()
    ]

    for i, sentenca in enumerate(
        sentencas
    ):

        if len(sentenca) <= limite:
            candidatos.append(
                sentenca
            )

        # Janelas de 2 e 3 sentenças
        for tamanho in (2, 3):

            janela = " ".join(
                sentencas[
                    i:i + tamanho
                ]
            ).strip()

            if (
                janela
                and len(janela) <= limite
                and janela in conteudo
            ):
                candidatos.append(
                    janela
                )

    # Remove duplicados sem mudar ordem
    candidatos_unicos = []

    vistos = set()

    for candidato in candidatos:

        if candidato not in vistos:

            vistos.add(
                candidato
            )

            candidatos_unicos.append(
                candidato
            )

    # --------------------------------------------------------
    # 4. MELHOR CORRESPONDÊNCIA
    # --------------------------------------------------------

    melhor_trecho = None
    melhor_score = 0.0

    for candidato in candidatos_unicos:

        candidato_normalizado = (
            normalizar_comparacao(
                candidato
            )
        )

        if not candidato_normalizado:
            continue

        score = SequenceMatcher(
            None,
            quotation_normalizada,
            candidato_normalizado
        ).ratio()

        # Também considera sobreposição de palavras.
        palavras_q = set(
            quotation_normalizada.split()
        )

        palavras_c = set(
            candidato_normalizado.split()
        )

        if palavras_q:

            sobreposicao = (
                len(
                    palavras_q
                    & palavras_c
                )
                / len(palavras_q)
            )

        else:
            sobreposicao = 0.0

        score_final = max(
            score,
            sobreposicao
        )

        if score_final > melhor_score:

            melhor_score = score_final
            melhor_trecho = candidato

    # --------------------------------------------------------
    # LIMIAR CONSERVADOR
    # --------------------------------------------------------

    if (
        melhor_trecho
        and melhor_score >= 0.55
        and melhor_trecho in conteudo
    ):
        return melhor_trecho

    return None


# ============================================================
# VALIDAÇÃO DE EVIDÊNCIAS
# ============================================================

def validar_evidencias_da_resposta(
    resposta: RAGResponse,
    documentos,
) -> None:
    """
    Garante que cada evidência citada:

    - pertence a um chunk recuperado;
    - utiliza o filepath correto;
    - possui quotation literal;
    - possui no máximo 500 caracteres.
    """

    if resposta.is_refusal:
        return

    documentos_por_chunk = {
        obter_chunk_id(doc): doc
        for doc in documentos
    }

    if not resposta.sources_used:
        raise ValueError(
            "Resposta não recusada precisa apresentar evidências."
        )

    for evidencia in resposta.sources_used:

        if evidencia.chunk_id not in documentos_por_chunk:
            raise ValueError(
                f"Chunk citado não foi recuperado: "
                f"{evidencia.chunk_id}"
            )

        doc = documentos_por_chunk[
            evidencia.chunk_id
        ]

        filepath_real = obter_filepath(
            doc
        )

        if evidencia.filepath != filepath_real:
            raise ValueError(
                f"filepath incorreto para "
                f"{evidencia.chunk_id}. "
                f"Esperado: {filepath_real}"
            )

        quotation = evidencia.quotation.strip()

        if not quotation:
            raise ValueError(
                "A quotation não pode estar vazia."
            )

        if len(quotation) > 500:
            raise ValueError(
                "A quotation ultrapassa 500 caracteres."
            )

        if quotation not in doc.page_content:

            trecho_literal = (
                encontrar_trecho_literal_mais_proximo(
                    quotation=quotation,
                    conteudo=doc.page_content,
                    limite=500,
                )
            )

            if trecho_literal is None:

                raise ValueError(
                    f"A quotation do chunk "
                    f"{evidencia.chunk_id} "
                    "não corresponde de forma segura a um "
                    "trecho literal do documento."
                )

            # O objeto final passa a guardar exatamente
            # o trecho existente no documento.
            evidencia.quotation = trecho_literal
            quotation = trecho_literal

        # A citação não pode expor dados que deveriam
        # ser recusados ou mascarados.
        verificacao_lgpd = aplicar_guardrails_lgpd(
            quotation
        )

        if verificacao_lgpd.get("status") != "permitido":
            raise ValueError(
                f"A evidência do chunk "
                f"{evidencia.chunk_id} contém dado "
                "que não pode ser exibido diretamente."
            )


# ============================================================
# PROMPT
# ============================================================

def construir_prompt(
    pergunta: str,
    documentos,
    feedback_erro: Optional[str] = None,
) -> str:
    """
    Cria o prompt utilizado para geração estruturada.
    """

    contexto = construir_contexto(
        documentos
    )

    feedback = ""

    if feedback_erro:

        feedback = f"""
ATENÇÃO — A TENTATIVA ANTERIOR FOI INVÁLIDA.

Erro encontrado:
{feedback_erro}

Corrija obrigatoriamente esse problema nesta nova tentativa.
"""

    return f"""
Você é o assistente RAG interno da empresa VendeFácil.

Sua tarefa é responder SOMENTE com base nas evidências recuperadas.

REGRAS OBRIGATÓRIAS:

1. Não invente informações.

2. Se as evidências recuperadas não forem suficientes:
   - is_refusal = true
   - confidence_level = "recusado"
   - sources_used = []
   - refusal_reason = "sem_evidencia"

3. Se responder normalmente:
   - is_refusal = false
   - refusal_reason = null
   - sources_used deve possuir pelo menos uma evidência.

4. Toda evidência deve conter:
   - filepath
   - chunk_id
   - quotation

5. A quotation deve ser COPIADA LITERALMENTE de uma das
   "CITAÇÕES LITERAIS AUTORIZADAS" fornecidas no contexto.

6. NÃO reescreva, resuma, corrija nem adapte a quotation.

7. NÃO crie uma quotation por conta própria.

8. REGRAS RÍGIDAS PARA quotation:
   - cada quotation deve possuir NO MÁXIMO 300 caracteres;
   - copie EXATAMENTE UMA das "CITAÇÕES LITERAIS AUTORIZADAS";
   - nunca copie o conteúdo completo de um documento;
   - nunca junte duas ou mais citações autorizadas em uma única quotation;
   - nunca ultrapasse 300 caracteres, mesmo que o schema permita até 500.

9. Quando a resposta contiver vários fatos, etapas ou decisões:
   - utilize várias entradas em sources_used;
   - é permitido repetir o mesmo filepath e o mesmo chunk_id;
   - use uma quotation curta para sustentar cada fato;
   - prefira evidências pequenas e diretamente relacionadas à afirmação.

10. Não inclua nas citações dados pessoais que precisem
    ser mascarados.

11. O campo reasoning deve explicar resumidamente por que
    as evidências sustentam a resposta.

12. confidence_level deve ser:
    - "alta": evidência direta e clara;
    - "media": evidência suficiente, mas parcialmente indireta;
    - "baixa": evidência limitada;
    - "recusado": somente para recusas.

13. GROUNDEDNESS É OBRIGATÓRIO:
    - Cada afirmação factual presente em answer deve estar
      diretamente sustentada por uma ou mais evidências recuperadas.
    - Não acrescente conclusões, benefícios, consequências,
      interpretações ou generalizações que não estejam explicitamente
      sustentadas pelos documentos.

14. Ao redigir answer:
    - responda somente o que pode ser demonstrado pelas evidências;
    - prefira frases objetivas e verificáveis;
    - não use expressões como "garantindo", "assegurando",
      "portanto protege", "isso demonstra que" ou semelhantes,
      salvo quando essa conclusão aparecer claramente na fonte.

15. Antes de finalizar a resposta, verifique mentalmente cada frase:
    "Existe uma evidência recuperada que sustenta diretamente esta afirmação?"
    Se a resposta for não, remova ou reformule a afirmação.

16. NÃO transforme intenção, solicitação ou pedido em fato consumado:
    - Se um documento apenas solicita uma ação, não diga que a empresa executa essa ação.
    - Se um documento apenas menciona um direito previsto em lei, não diga que o sistema
      necessariamente cumpre, garante ou confirma esse direito, salvo quando houver
      evidência explícita disso.
    - Diferencie claramente "foi solicitado" de "foi realizado".

17. Em perguntas sobre políticas, LGPD ou segurança:
    - priorize afirmações normativas explicitamente presentes nas políticas recuperadas;
    - use e-mails, tickets ou solicitações apenas como evidência de que houve aquele pedido
      ou ocorrência, e não como prova de política ou cumprimento geral.

18. Em perguntas que solicitem solução, procedimento, configuração,
    correção ou passo a passo:
    - inclua SOMENTE ações explicitamente descritas nas evidências;
    - não acrescente etapas comuns de troubleshooting por conhecimento geral;
    - não acrescente reinicializações, testes, validações, comandos ou verificações
      se essas ações não estiverem presentes nos documentos recuperados;
    - se a fonte apresentar apenas uma ação, responda apenas com essa ação.

19. A decisão sobre LGPD da PERGUNTA já foi executada antes desta etapa
    por um guardrail determinístico.
    - Não invente uma recusa por LGPD.
    - Não classifique uma operação empresarial comum como dado pessoal.
    - Se houver evidência suficiente para uma pergunta operacional legítima,
      responda normalmente.
    - Use is_refusal=true apenas quando as evidências forem insuficientes
      para responder com segurança.

20. Antes de retornar uma resposta normal:
    - compare cada ação e cada afirmação de answer com o contexto;
    - remova qualquer detalhe que tenha vindo apenas do seu conhecimento geral;
    - sources_used deve apontar para os chunks que sustentam efetivamente a resposta.

21. CHECAGEM FINAL OBRIGATÓRIA DE SCHEMA:
    - examine cada item de sources_used;
    - confirme que quotation possui no máximo 300 caracteres;
    - se uma quotation estiver longa, substitua-a por uma CITAÇÃO LITERAL
      AUTORIZADA menor;
    - para listas com várias decisões, prefira várias evidências curtas
      em vez de uma evidência longa.


22. COMPLETUDE EM PERGUNTAS PROCEDIMENTAIS:
    - se a pergunta pedir "como", "como fazer", "como realizar",
      "procedimento", "passo a passo", "configuração", "solução"
      ou instruções operacionais, responda com o procedimento completo
      que estiver explicitamente presente nas evidências;
    - se o contexto apresentar uma lista numerada ou sequência de etapas,
      preserve TODAS as etapas relevantes e a ordem original;
    - não substitua um passo a passo disponível por apenas uma definição,
      explicação geral ou resumo parcial;
    - não omita atalhos, menus, campos, autenticações, confirmações,
      saídas ou ações finais quando eles estiverem explicitamente
      documentados e forem necessários para executar o procedimento;
    - não acrescente etapas que não estejam nas evidências.

23. EVIDÊNCIAS PARA PROCEDIMENTOS:
    - quando a resposta possuir várias etapas, sources_used deve conter
      evidências suficientes para sustentar o procedimento apresentado;
    - podem existir várias entradas em sources_used apontando para o
      mesmo chunk_id;
    - prefira quotations curtas que cubram diferentes partes do
      procedimento, em vez de uma única citação genérica.

{feedback}

PERGUNTA:
{pergunta}

CONTEXTO RECUPERADO:
{contexto}
""".strip()


# ============================================================
# GERAÇÃO COM LLM
# ============================================================

def gerar_com_llm(
    pergunta: str,
    documentos,
    feedback_erro: Optional[str] = None,
) -> RAGResponse:
    """
    Executa uma tentativa de geração estruturada.
    """

    prompt = construir_prompt(
        pergunta=pergunta,
        documentos=documentos,
        feedback_erro=feedback_erro,
    )

    resposta = llm_estruturado.invoke(
        prompt
    )

    if not isinstance(
        resposta,
        RAGResponse
    ):

        resposta = RAGResponse.model_validate(
            resposta
        )

    return resposta


def gerar_com_retry_llm(
    pergunta: str,
    documentos,
    tentativas: int = 3,
) -> RAGResponse:
    """
    Executa geração estruturada com retry real.

    Em caso de erro de Pydantic ou evidência inválida,
    o erro é devolvido ao LLM na tentativa seguinte.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            feedback = (
                str(ultimo_erro)
                if ultimo_erro
                else None
            )

            resposta = gerar_com_llm(
                pergunta=pergunta,
                documentos=documentos,
                feedback_erro=feedback,
            )

            validar_evidencias_da_resposta(
                resposta,
                documentos
            )

            return resposta

        except (
            ValidationError,
            ValueError,
            Exception,
        ) as erro:

            ultimo_erro = erro

            print(
                f"Falha na tentativa "
                f"{tentativa}/{tentativas}: "
                f"{type(erro).__name__}: {erro}"
            )

    raise RuntimeError(
        "Não foi possível gerar uma resposta estruturada "
        f"válida após {tentativas} tentativas. "
        f"Último erro: {ultimo_erro}"
    )


# ============================================================
# PÓS-PROCESSAMENTO LGPD
# ============================================================

def aplicar_guardrail_na_resposta(
    resposta: RAGResponse,
) -> RAGResponse:
    """
    Verifica a resposta final produzida pelo LLM.

    - Se houver dado proibido -> recusa LGPD.
    - Se houver dado mascarável -> mascara a resposta.
    - Caso contrário -> mantém resposta.
    """

    if resposta.is_refusal:
        return resposta

    resultado = aplicar_guardrails_lgpd(
        resposta.answer
    )

    status = resultado.get(
        "status"
    )

    # --------------------------------------------------------
    # RECUSA
    # --------------------------------------------------------

    if status == "recusado":

        return criar_recusa(
            motivo="lgpd",
            reasoning=(
                "A resposta recuperada continha informação "
                "classificada como restrita pelas regras de LGPD."
            ),
        )

    # --------------------------------------------------------
    # MASCARAMENTO
    # --------------------------------------------------------

    if status == "mascarado":

        resposta.answer = resultado.get(
            "resposta_segura",
            resposta.answer
        )

    return resposta


# ============================================================
# PIPELINE FINAL
# ============================================================

def gerar_resposta(
    pergunta: str,
    usar_filtros: bool = True,
    k: int = 5,
    fetch_k: int = 500,
    tentativas: int = 3,
    funcao_geradora: Optional[Callable] = None,
) -> RAGResponse:
    """
    Pipeline completo da Etapa 3:

    pergunta
        ↓
    fora de escopo
        ↓
    LGPD na pergunta
        ↓
    retrieval híbrido
        ↓
    geração estruturada
        ↓
    validação Pydantic
        ↓
    validação das evidências
        ↓
    guardrail LGPD na resposta
        ↓
    RAGResponse final
    """

    # ========================================================
    # 1. FORA DE ESCOPO
    # ========================================================

    verificacao_escopo = verificar_fora_de_escopo(
        pergunta
    )

    if not verificacao_escopo.get(
        "permitido",
        True
    ):

        return criar_recusa(
            motivo="fora_de_escopo",
            answer=verificacao_escopo.get(
                "mensagem"
            ),
            reasoning=(
                "A pergunta não pertence ao domínio "
                "operacional da VendeFácil."
            ),
        )

    # ========================================================
    # 2. LGPD NA PERGUNTA
    # ========================================================

    verificacao_lgpd = aplicar_guardrails_lgpd(
        pergunta
    )

    if verificacao_lgpd.get(
        "status"
    ) == "recusado":

        return criar_recusa(
            motivo="lgpd",
            reasoning=(
                verificacao_lgpd.get(
                    "motivo",
                    "A pergunta solicita dado restrito."
                )
            ),
        )

    # ========================================================
    # 3. RETRIEVAL
    # ========================================================

    resultado_busca = buscar_hibrido(
        pergunta,
        usar_filtros=usar_filtros,
        k=k,
        fetch_k=fetch_k,
    )

    ranking = resultado_busca.get(
        "rrf",
        []
    )

    documentos = [
        doc
        for doc, _score in ranking
    ]

    # ========================================================
    # 4. SEM EVIDÊNCIA
    # ========================================================

    if not documentos:

        return criar_recusa(
            motivo="sem_evidencia",
            reasoning=(
                "Nenhum documento relevante foi recuperado "
                "para responder à pergunta."
            ),
        )

    # ========================================================
    # 5. FUNÇÃO CUSTOMIZADA PARA TESTES
    # ========================================================

    if funcao_geradora is not None:

        resposta = validar_com_retry(
            gerador=funcao_geradora,
            tentativas=tentativas,
        )

        if not resposta.is_refusal:

            validar_evidencias_da_resposta(
                resposta,
                documentos
            )

    # ========================================================
    # 6. GERAÇÃO REAL COM LLM
    # ========================================================

    else:

        resposta = gerar_com_retry_llm(
            pergunta=pergunta,
            documentos=documentos,
            tentativas=tentativas,
        )

    # ========================================================
    # 7. GUARDRAIL NA RESPOSTA
    # ========================================================

    resposta = aplicar_guardrail_na_resposta(
        resposta
    )

    return resposta


# ============================================================
# TESTE MANUAL
# ============================================================

if __name__ == "__main__":

    pergunta = (
        "O que aconteceu no ticket TCK-1057?"
    )

    resposta = gerar_resposta(
        pergunta
    )

    print(
        resposta.model_dump_json(
            indent=2
        )
    )
