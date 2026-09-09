import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
SRC_DIR = ROOT_DIR / "src"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

BENCHMARK_PATH = ROOT_DIR / "benchmark" / "questions_and_ground_truth.json"
RESULTS_PATH = ROOT_DIR / "eval" / "results.json"


# ============================================================
# UTILITÁRIOS
# ============================================================

def normalizar_caminho(valor: Any) -> str:
    """Normaliza caminhos para comparação."""
    if valor is None:
        return ""

    caminho = str(valor).strip().replace("\\", "/")

    while caminho.startswith("./"):
        caminho = caminho[2:]

    return caminho.lower()


def nome_arquivo(valor: Any) -> str:
    """Retorna somente o nome final de um caminho."""
    caminho = normalizar_caminho(valor)

    if not caminho:
        return ""

    return caminho.split("/")[-1]


def serializar_pydantic(objeto: Any) -> Any:
    """Converte modelos Pydantic para estruturas JSON."""
    if objeto is None:
        return None

    if hasattr(objeto, "model_dump"):
        return objeto.model_dump()

    if hasattr(objeto, "dict"):
        return objeto.dict()

    return objeto


def media(valores: List[float]) -> Optional[float]:
    """Calcula média ignorando listas vazias."""
    if not valores:
        return None

    return round(sum(valores) / len(valores), 4)


def obter_campo_resposta(
    resposta: Any,
    nomes: List[str],
    padrao: Any = None
) -> Any:
    """Obtém um campo tanto de dict quanto de objeto Pydantic."""

    if resposta is None:
        return padrao

    if isinstance(resposta, dict):
        for nome in nomes:
            if nome in resposta:
                return resposta[nome]

        return padrao

    for nome in nomes:
        if hasattr(resposta, nome):
            return getattr(resposta, nome)

    return padrao


def extrair_texto_resposta(resposta: Any) -> str:
    """Extrai o texto principal da resposta estruturada."""

    texto = obter_campo_resposta(
        resposta,
        ["answer", "resposta", "response"],
        ""
    )

    if texto is None:
        return ""

    return str(texto).strip()


# ============================================================
# LEITURA DO BENCHMARK
# ============================================================

def carregar_benchmark() -> List[Dict[str, Any]]:
    """Carrega o benchmark oficial da Etapa 4."""

    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            "Arquivo do benchmark não encontrado em:\n"
            f"{BENCHMARK_PATH}"
        )

    with BENCHMARK_PATH.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError(
            "O benchmark deve possuir um objeto JSON na raiz."
        )

    questoes = dados.get("questions")

    if not isinstance(questoes, list):
        raise ValueError(
            "Campo 'questions' não encontrado ou inválido."
        )

    print(f"Benchmark: {dados.get('benchmark_name', 'N/A')}")
    print(f"Versão: {dados.get('version', 'N/A')}")
    print(f"Quantidade real de questões: {len(questoes)}")

    if len(questoes) != 20:
        print(
            "⚠️ A orientação menciona 20 questões, "
            f"mas o arquivo oficial contém {len(questoes)}."
        )
        print("O script executará todas as questões presentes.")

    return questoes


# ============================================================
# EXTRAÇÃO DOS RESULTADOS DO RETRIEVER
# ============================================================

def extrair_documentos_rrf(
    resultado_busca: Dict[str, Any]
) -> List[Any]:
    """Extrai os Documents presentes no ranking RRF."""

    ranking = resultado_busca.get("rrf", [])
    documentos = []

    for item in ranking:
        if isinstance(item, (list, tuple)):
            if len(item) >= 1:
                documentos.append(item[0])
        else:
            documentos.append(item)

    return documentos


def extrair_chunk_ids(documentos: List[Any]) -> List[str]:
    """Extrai os chunk_id recuperados."""

    chunk_ids = []

    for documento in documentos:
        metadata = getattr(documento, "metadata", {}) or {}
        chunk_id = metadata.get("chunk_id")

        if chunk_id is not None:
            chunk_ids.append(str(chunk_id))

    return chunk_ids


def extrair_sources_recuperados(
    documentos: List[Any]
) -> List[str]:
    """Extrai source_file dos documentos recuperados."""

    fontes = []

    for documento in documentos:
        metadata = getattr(documento, "metadata", {}) or {}
        source_file = metadata.get("source_file")

        if source_file:
            fontes.append(str(source_file))

    return fontes


def documento_para_dict(documento: Any) -> Dict[str, Any]:
    """Serializa um Document do LangChain."""

    metadata = getattr(documento, "metadata", {}) or {}
    conteudo = getattr(documento, "page_content", "")

    return {
        "chunk_id": metadata.get("chunk_id"),
        "source_file": metadata.get("source_file"),
        "doc_type": metadata.get("doc_type"),
        "sensitivity": metadata.get("sensitivity"),
        "metadata": metadata,
        "content": conteudo
    }


def montar_contexto(documentos: List[Any]) -> str:
    """
    Monta o contexto enviado ao juiz de Groundedness.
    Inclui chunk_id e source_file para manter rastreabilidade.
    """

    partes = []

    for indice, documento in enumerate(documentos, start=1):
        metadata = getattr(documento, "metadata", {}) or {}
        conteudo = getattr(documento, "page_content", "")

        chunk_id = metadata.get("chunk_id", "N/A")
        source_file = metadata.get("source_file", "N/A")

        partes.append(
            f"[Trecho {indice}]\n"
            f"chunk_id: {chunk_id}\n"
            f"source_file: {source_file}\n"
            f"{conteudo}"
        )

    return "\n\n".join(partes)


# ============================================================
# CONTEXT RELEVANCE
# ============================================================

def fonte_corresponde(
    fonte_recuperada: str,
    fonte_esperada: str
) -> bool:
    """Compara source_file recuperado e expected_source."""

    recuperada = normalizar_caminho(fonte_recuperada)
    esperada = normalizar_caminho(fonte_esperada)

    if not recuperada or not esperada:
        return False

    if recuperada == esperada:
        return True

    if recuperada.endswith(esperada):
        return True

    if esperada.endswith(recuperada):
        return True

    return nome_arquivo(recuperada) == nome_arquivo(esperada)


def calcular_context_relevance(
    sources_recuperados: List[str],
    sources_esperados: List[str]
) -> Optional[float]:
    """
    Calcula um proxy de Context Relevance por expected_sources.

    IMPORTANTE:
    o benchmark oficial fornecido não contém expected_chunk_ids.
    Assim, esta métrica mede a proporção das fontes esperadas
    que apareceu nos documentos recuperados.

    Ela não deve ser descrita como correspondência de chunk_id.
    """

    if not sources_esperados:
        return None

    encontradas = 0

    for fonte_esperada in sources_esperados:
        encontrou = any(
            fonte_corresponde(
                fonte_recuperada,
                fonte_esperada
            )
            for fonte_recuperada in sources_recuperados
        )

        if encontrou:
            encontradas += 1

    score = encontradas / len(sources_esperados)

    return round(score, 4)


# ============================================================
# COERÊNCIA DA RESPOSTA ESTRUTURADA
# ============================================================

def calcular_coerencia_estrutural(resposta: Any) -> float:
    """
    Avalia a coerência básica entre texto, confidence e is_refusal.

    Essa pontuação é usada somente como apoio ao componente
    estrutural da avaliação do desafio.
    """

    is_refusal = bool(
        obter_campo_resposta(
            resposta,
            ["is_refusal"],
            False
        )
    )

    confidence = obter_campo_resposta(
        resposta,
        ["confidence_level", "confidence", "confianca"],
        None
    )

    refusal_reason = obter_campo_resposta(
        resposta,
        ["refusal_reason"],
        None
    )

    texto = extrair_texto_resposta(resposta)

    confidence_norm = (
        str(confidence).strip().lower()
        if confidence is not None
        else ""
    )

    if is_refusal:
        if refusal_reason or confidence_norm in {
            "recusado",
            "refusal",
            "refused"
        }:
            return 1.0

        return 0.0

    if texto:
        if confidence_norm not in {
            "recusado",
            "refusal",
            "refused"
        }:
            return 1.0

    return 0.0


# ============================================================
# EXECUÇÃO DE UMA QUESTÃO
# ============================================================

def executar_questao(
    item: Dict[str, Any],
    indice: int,
    usar_judge: bool = True
) -> Dict[str, Any]:
    """Executa retrieval, geração e RAG Triad para uma questão."""

    from src.retrieve import buscar_hibrido
    from src.generate import gerar_resposta

    if usar_judge:
        from eval.judge import (
            evaluate_answer_relevance,
            evaluate_groundedness
        )

    questao_id = item.get("id", f"Q{indice:02d}")
    categoria = item.get("category", "Sem categoria")
    pergunta = item.get("question", "")

    expected_sources = item.get("expected_sources", []) or []
    expected_metadata = item.get("expected_metadata", {}) or {}
    ground_truth_answer = item.get("ground_truth_answer", "")
    key_points = item.get("key_points_for_evaluation", []) or []

    if not pergunta:
        raise ValueError(
            f"Questão {questao_id} sem campo 'question'."
        )

    print(f"\n[{questao_id}] {pergunta}")

    # --------------------------------------------------------
    # 1. RETRIEVAL
    # --------------------------------------------------------

    busca = buscar_hibrido(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    documentos = extrair_documentos_rrf(busca)
    chunk_ids = extrair_chunk_ids(documentos)
    sources_recuperados = extrair_sources_recuperados(documentos)

    context_relevance = calcular_context_relevance(
        sources_recuperados,
        expected_sources
    )

    # --------------------------------------------------------
    # 2. GERAÇÃO RAG
    # --------------------------------------------------------

    resposta = gerar_resposta(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    resposta_serializada = serializar_pydantic(resposta)
    texto_resposta = extrair_texto_resposta(resposta)

    contexto_judge = montar_contexto(documentos)

    # --------------------------------------------------------
    # 3. LLM-AS-JUDGE
    # --------------------------------------------------------

    answer_relevance = None
    groundedness = None

    if usar_judge:
        print("   → Answer Relevance...")

        answer_relevance = evaluate_answer_relevance(
            pergunta=pergunta,
            resposta=texto_resposta
        )

        print(
            "      score:",
            answer_relevance.get("score")
        )

        print("   → Groundedness...")

        groundedness = evaluate_groundedness(
            contexto=contexto_judge,
            resposta=texto_resposta
        )

        print(
            "      score:",
            groundedness.get("score")
        )

    # --------------------------------------------------------
    # 4. PONTUAÇÃO OPERACIONAL
    # --------------------------------------------------------

    answer_score = None

    if isinstance(answer_relevance, dict):
        valor = answer_relevance.get("score")

        if isinstance(valor, (int, float)):
            answer_score = float(valor)

    citation_score = (
        float(context_relevance)
        if isinstance(context_relevance, (int, float))
        else None
    )

    coherence_score = calcular_coerencia_estrutural(
        resposta_serializada
    )

    componentes = {
        "answer_or_refusal": (
            round(answer_score * 0.5, 4)
            if answer_score is not None
            else None
        ),
        "citation_proxy": (
            round(citation_score * 0.3, 4)
            if citation_score is not None
            else None
        ),
        "confidence_refusal_coherence": round(
            coherence_score * 0.2,
            4
        )
    }

    valores_disponiveis = [
        valor
        for valor in componentes.values()
        if isinstance(valor, (int, float))
    ]

    score_desafio = (
        round(sum(valores_disponiveis), 4)
        if valores_disponiveis
        else None
    )

    # --------------------------------------------------------
    # 5. RESULTADO
    # --------------------------------------------------------

    resultado = {
        "id": questao_id,
        "type": categoria,
        "question": pergunta,

        "ground_truth": {
            "expected_sources": expected_sources,
            "expected_metadata": expected_metadata,
            "ground_truth_answer": ground_truth_answer,
            "key_points_for_evaluation": key_points
        },

        "retrieval": {
            "filters": busca.get("filtros", {}),
            "retrieved_chunk_ids": chunk_ids,
            "retrieved_sources": sources_recuperados,
            "documents": [
                documento_para_dict(doc)
                for doc in documentos
            ]
        },

        "response": resposta_serializada,

        "metrics": {
            "context_relevance": context_relevance,
            "context_relevance_basis": (
                "expected_sources_proxy_no_ground_truth_chunk_ids"
            ),
            "answer_relevance": answer_relevance,
            "groundedness": groundedness
        },

        "challenge_score": {
            "score": score_desafio,
            "components": componentes,
            "note": (
                "O componente de citação usa expected_sources como "
                "proxy porque o benchmark fornecido não contém "
                "expected_chunk_ids."
            )
        }
    }

    return resultado


# ============================================================
# RESUMO
# ============================================================

def gerar_resumo(
    resultados: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Gera médias globais e médias por categoria."""

    context_global = []
    answer_global = []
    grounded_global = []
    challenge_global = []

    erros_answer = 0
    erros_grounded = 0

    por_tipo = defaultdict(
        lambda: {
            "quantidade": 0,
            "context_relevance": [],
            "answer_relevance": [],
            "groundedness": [],
            "challenge_score": []
        }
    )

    for resultado in resultados:
        tipo = resultado.get("type", "Sem categoria")
        por_tipo[tipo]["quantidade"] += 1

        metricas = resultado.get("metrics", {})

        contexto = metricas.get("context_relevance")

        if isinstance(contexto, (int, float)):
            context_global.append(float(contexto))
            por_tipo[tipo]["context_relevance"].append(
                float(contexto)
            )

        answer = metricas.get("answer_relevance")

        if isinstance(answer, dict):
            if answer.get("evaluation_error"):
                erros_answer += 1
            else:
                score = answer.get("score")

                if isinstance(score, (int, float)):
                    answer_global.append(float(score))
                    por_tipo[tipo]["answer_relevance"].append(
                        float(score)
                    )

        grounded = metricas.get("groundedness")

        if isinstance(grounded, dict):
            if grounded.get("evaluation_error"):
                erros_grounded += 1
            else:
                score = grounded.get("score")

                if isinstance(score, (int, float)):
                    grounded_global.append(float(score))
                    por_tipo[tipo]["groundedness"].append(
                        float(score)
                    )

        challenge = (
            resultado.get("challenge_score", {}).get("score")
        )

        if isinstance(challenge, (int, float)):
            challenge_global.append(float(challenge))
            por_tipo[tipo]["challenge_score"].append(
                float(challenge)
            )

    resumo_por_tipo = {}

    for tipo, dados in por_tipo.items():
        resumo_por_tipo[tipo] = {
            "quantidade": dados["quantidade"],
            "context_relevance": media(
                dados["context_relevance"]
            ),
            "answer_relevance": media(
                dados["answer_relevance"]
            ),
            "groundedness": media(
                dados["groundedness"]
            ),
            "challenge_score": media(
                dados["challenge_score"]
            )
        }

    return {
        "total_questions": len(resultados),
        "evaluation_status": "completed_with_llm_judge",
        "judge_provider": "Groq",
        "judge_model": "openai/gpt-oss-20b",
        "context_relevance_basis": (
            "expected_sources_proxy_no_ground_truth_chunk_ids"
        ),
        "benchmark_warning": (
            "O arquivo oficial contém 24 questões, apesar de a "
            "orientação mencionar 20. O benchmark fornecido também "
            "não contém expected_chunk_ids."
        ),
        "rag_triad": {
            "context_relevance": media(context_global),
            "answer_relevance": media(answer_global),
            "groundedness": media(grounded_global)
        },
        "challenge_score_average": media(challenge_global),
        "judge_errors": {
            "answer_relevance": erros_answer,
            "groundedness": erros_grounded,
            "total": erros_answer + erros_grounded
        },
        "by_type": resumo_por_tipo
    }


# ============================================================
# SALVAR RESULTADOS
# ============================================================

def salvar_resultados(
    resultados: List[Dict[str, Any]],
    resumo: Dict[str, Any]
) -> None:

    payload = {
        "summary": resumo,
        "results": resultados
    }

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_PATH.open("w", encoding="utf-8") as arquivo:
        json.dump(
            payload,
            arquivo,
            ensure_ascii=False,
            indent=2,
            default=str
        )

    print("\n✅ Resultados salvos em:")
    print(RESULTS_PATH)


# ============================================================
# EXECUÇÃO DO BENCHMARK
# ============================================================

def executar_benchmark(
    usar_judge: bool = True,
    limite: Optional[int] = None
) -> Dict[str, Any]:
    """Executa o benchmark completo ou um subconjunto."""

    questoes = carregar_benchmark()

    if limite is not None:
        questoes = questoes[:limite]

    resultados = []
    total = len(questoes)

    print(f"\n🚀 Executando {total} questão(ões)...")
    print(f"LLM-as-judge: {'ATIVADO' if usar_judge else 'DESATIVADO'}")

    for indice, item in enumerate(questoes, start=1):
        questao_id = item.get("id", f"Q{indice:02d}")

        print("\n" + "=" * 70)
        print(f"Questão {indice}/{total} - {questao_id}")
        print("=" * 70)

        try:
            resultado = executar_questao(
                item=item,
                indice=indice,
                usar_judge=usar_judge
            )

            resultados.append(resultado)

        except Exception as erro:
            print(f"❌ Erro na questão {questao_id}: {erro}")

            resultados.append({
                "id": questao_id,
                "type": item.get("category", "Sem categoria"),
                "question": item.get("question", ""),
                "error": str(erro),
                "metrics": {
                    "context_relevance": None,
                    "context_relevance_basis": (
                        "expected_sources_proxy_no_ground_truth_chunk_ids"
                    ),
                    "answer_relevance": None,
                    "groundedness": None
                },
                "challenge_score": {
                    "score": None,
                    "components": {}
                }
            })

    resumo = gerar_resumo(resultados)

    salvar_resultados(
        resultados=resultados,
        resumo=resumo
    )

    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)

    print(
        "Context Relevance:",
        resumo["rag_triad"]["context_relevance"]
    )

    print(
        "Answer Relevance:",
        resumo["rag_triad"]["answer_relevance"]
    )

    print(
        "Groundedness:",
        resumo["rag_triad"]["groundedness"]
    )

    print(
        "Pontuação média operacional:",
        resumo["challenge_score_average"]
    )

    print(
        "Erros técnicos do judge:",
        resumo["judge_errors"]["total"]
    )

    return {
        "summary": resumo,
        "results": resultados
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    executar_benchmark(
        usar_judge=True
    )
