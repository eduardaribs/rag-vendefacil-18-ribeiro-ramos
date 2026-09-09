
import re
import unicodedata
from typing import Optional


# ============================================================
# VOCABULÁRIO PERMITIDO
# ============================================================

VALID_DOC_TYPES = {
    "customer",
    "employee",
    "product",
    "store",
    "ticket",
    "log",
    "manual",
    "ata",
    "policy",
    "email",
    "sale",
}

VALID_STATES = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES",
    "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
    "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}

VALID_MODULES = {
    "estoque",
    "pdv",
    "pay",
    "ecommerce",
    "analytics",
}

VALID_PRIORITIES = {
    "baixa",
    "media",
    "alta",
    "critica",
}


# ============================================================
# SINÔNIMOS DE ESTADOS
# ============================================================

STATE_SYNONYMS = {
    "acre": "AC",
    "ac": "AC",

    "alagoas": "AL",
    "al": "AL",

    "amapa": "AP",
    "ap": "AP",

    "amazonas": "AM",
    "am": "AM",

    "bahia": "BA",
    "ba": "BA",

    "ceara": "CE",
    "ce": "CE",

    "distrito federal": "DF",
    "df": "DF",

    "espirito santo": "ES",
    "es": "ES",

    "goias": "GO",
    "go": "GO",

    "maranhao": "MA",
    "ma": "MA",

    "mato grosso": "MT",
    "mt": "MT",

    "mato grosso do sul": "MS",
    "ms": "MS",

    "minas gerais": "MG",
    "mg": "MG",

    # Não usamos "para" como sinônimo textual de Pará,
    # pois conflita com a preposição "para".
    "pa": "PA",

    "paraiba": "PB",
    "pb": "PB",

    "parana": "PR",
    "pr": "PR",

    "pernambuco": "PE",
    "pe": "PE",

    "piaui": "PI",
    "pi": "PI",

    "rio de janeiro": "RJ",
    "rj": "RJ",

    "rio grande do norte": "RN",
    "rn": "RN",

    "rio grande do sul": "RS",
    "rs": "RS",

    "rondonia": "RO",
    "ro": "RO",

    "roraima": "RR",
    "rr": "RR",

    "santa catarina": "SC",
    "sc": "SC",

    "sao paulo": "SP",
    "sp": "SP",

    "sergipe": "SE",
    "se": "SE",

    "tocantins": "TO",
    "to": "TO",
}


# ============================================================
# SINÔNIMOS DE MÓDULOS
# ============================================================

MODULE_SYNONYMS = {
    "controle de estoque": "estoque",
    "gestao de estoque": "estoque",
    "estoque": "estoque",

    "ponto de venda": "pdv",
    "frente de caixa": "pdv",
    "pdv": "pdv",

    "pagamentos": "pay",
    "pagamento": "pay",
    "vendefacil pay": "pay",
    "vende facil pay": "pay",
    "pay": "pay",

    "e-commerce": "ecommerce",
    "e commerce": "ecommerce",
    "loja virtual": "ecommerce",
    "comercio eletronico": "ecommerce",
    "ecommerce": "ecommerce",

    "analise de dados": "analytics",
    "analises": "analytics",
    "analise": "analytics",
    "relatorios": "analytics",
    "analytics": "analytics",
}


# ============================================================
# SINÔNIMOS DE PRIORIDADE
# ============================================================

PRIORITY_SYNONYMS = {
    "baixa prioridade": "baixa",
    "prioridade baixa": "baixa",
    "baixas": "baixa",
    "baixos": "baixa",
    "baixa": "baixa",
    "baixo": "baixa",

    "media prioridade": "media",
    "prioridade media": "media",
    "medias": "media",
    "medios": "media",
    "media": "media",
    "medio": "media",

    "alta prioridade": "alta",
    "prioridade alta": "alta",
    "altas": "alta",
    "altos": "alta",
    "alta": "alta",
    "alto": "alta",

    "prioridade critica": "critica",
    "critica prioridade": "critica",
    "criticas": "critica",
    "criticos": "critica",
    "critica": "critica",
    "critico": "critica",
}


# ============================================================
# SINÔNIMOS DE STATUS
# ============================================================

STATUS_SYNONYMS = {
    "em andamento": "Em Andamento",

    "abertos": "Aberto",
    "abertas": "Aberto",
    "aberto": "Aberto",
    "aberta": "Aberto",

    "fechados": "Fechado",
    "fechadas": "Fechado",
    "fechado": "Fechado",
    "fechada": "Fechado",

    "resolvidos": "Resolvido",
    "resolvidas": "Resolvido",
    "resolvido": "Resolvido",
    "resolvida": "Resolvido",

    "pendentes": "Pendente",
    "pendente": "Pendente",

    "ativos": "Ativo",
    "ativas": "Ativo",
    "ativo": "Ativo",
    "ativa": "Ativo",

    "inativos": "Inativo",
    "inativas": "Inativo",
    "inativo": "Inativo",
    "inativa": "Inativo",
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para comparação:
    - converte para minúsculas;
    - remove acentos;
    - remove espaços duplicados.
    """

    if texto is None:
        return ""

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


# ============================================================
# BUSCA DE SINÔNIMOS
# ============================================================

def encontrar_sinonimo(
    texto: str,
    dicionario: dict
) -> Optional[str]:
    """
    Procura expressões maiores antes das menores.
    """

    termos = sorted(
        dicionario.keys(),
        key=len,
        reverse=True
    )

    for termo in termos:

        termo_normalizado = normalizar_texto(
            termo
        )

        padrao = (
            rf"(?<!\w)"
            rf"{re.escape(termo_normalizado)}"
            rf"(?!\w)"
        )

        if re.search(
            padrao,
            texto
        ):
            return dicionario[termo]

    return None


# ============================================================
# EXTRAÇÃO DE CUSTOMER_ID
# ============================================================

def extrair_customer_id(
    texto_original: str
) -> Optional[str]:
    """
    Extrai identificadores no formato CUST + números.

    Exemplos:
    - CUST001
    - cust001
    - CUST092
    - cliente CUST277

    O resultado é retornado em letras maiúsculas.
    """

    if not texto_original:
        return None

    correspondencia = re.search(
        r"\bCUST\d+\b",
        str(texto_original),
        flags=re.IGNORECASE
    )

    if not correspondencia:
        return None

    return correspondencia.group(0).upper()


# ============================================================
# EXTRAÇÃO DE STATE
# ============================================================

def extrair_state(
    texto: str
) -> Optional[str]:
    """
    Extrai estado da pergunta.

    A palavra "para" NÃO é interpretada como Pará,
    evitando falsos positivos em frases como:

    "Quais tickets existem para o CUST092?"
    """

    valor = encontrar_sinonimo(
        texto,
        STATE_SYNONYMS
    )

    if valor in VALID_STATES:
        return valor

    return None


# ============================================================
# EXTRAÇÃO DE MODULE
# ============================================================

def extrair_module(
    texto: str
) -> Optional[str]:

    valor = encontrar_sinonimo(
        texto,
        MODULE_SYNONYMS
    )

    if valor in VALID_MODULES:
        return valor

    return None


# ============================================================
# EXTRAÇÃO DE DOC_TYPE
# ============================================================

def extrair_doc_type(
    texto: str
) -> Optional[str]:
    """
    Identifica o tipo documental principal solicitado.

    Cliente/clientes não é transformado automaticamente
    em customer quando aparece apenas como complemento.

    Exemplos:

    tickets de clientes de MG
        -> ticket

    problemas para clientes de SP
        -> nenhum doc_type

    quais clientes de MG estão ativos
        -> customer
    """

    prioridades = [
        (
            "ticket",
            [
                "tickets",
                "ticket",
                "chamados",
                "chamado"
            ]
        ),
        (
            "log",
            [
                "logs",
                "log"
            ]
        ),
        (
            "policy",
            [
                "politicas",
                "politica"
            ]
        ),
        (
            "manual",
            [
                "manuais",
                "manual"
            ]
        ),
        (
            "ata",
            [
                "atas",
                "ata"
            ]
        ),
        (
            "email",
            [
                "emails",
                "email"
            ]
        ),
        (
            "product",
            [
                "produtos",
                "produto"
            ]
        ),
        (
            "store",
            [
                "lojas",
                "loja"
            ]
        ),
        (
            "employee",
            [
                "funcionarios",
                "funcionario"
            ]
        ),
        (
            "sale",
            [
                "vendas",
                "venda"
            ]
        ),
    ]

    for doc_type, termos in prioridades:

        for termo in termos:

            termo_normalizado = normalizar_texto(
                termo
            )

            padrao = (
                rf"(?<!\w)"
                rf"{re.escape(termo_normalizado)}"
                rf"(?!\w)"
            )

            if re.search(
                padrao,
                texto
            ):

                if doc_type in VALID_DOC_TYPES:
                    return doc_type

    # --------------------------------------------------------
    # CONSULTAS EXPLICITAMENTE SOBRE CLIENTES
    # --------------------------------------------------------

    padroes_customer = [
        r"\bquais clientes\b",
        r"\bqual cliente\b",

        r"\bliste os clientes\b",
        r"\blistar clientes\b",

        r"\bmostre os clientes\b",
        r"\bmostrar clientes\b",

        r"\bdados dos clientes\b",
        r"\binformacoes dos clientes\b",

        r"\bcadastro de clientes\b",

        r"\binformacoes do cliente\b",
        r"\binformacoes sobre o cliente\b",

        r"\bdados do cliente\b",
        r"\bdados sobre o cliente\b",

        r"\bcadastro do cliente\b",
    ]

    for padrao in padroes_customer:

        if re.search(
            padrao,
            texto
        ):
            return "customer"

    return None


# ============================================================
# EXTRAÇÃO DE PRIORITY
# ============================================================

def extrair_priority(
    texto: str
) -> Optional[str]:

    valor = encontrar_sinonimo(
        texto,
        PRIORITY_SYNONYMS
    )

    if valor in VALID_PRIORITIES:
        return valor.capitalize()

    return None


# ============================================================
# EXTRAÇÃO DE STATUS
# ============================================================

def extrair_status(
    texto: str
) -> Optional[str]:
    """
    Extrai status explícito da consulta.

    Diferencia o status atual de um registro de expressões
    que apenas descrevem uma ação passada.

    Exemplos:
    - "tickets estão abertos" -> status Aberto
    - "tickets abertos atualmente" -> status Aberto
    - "tickets foram abertos por clientes" -> sem filtro de status
    """

    texto = normalizar_texto(
        texto
    )

    # Expressões em que "aberto" indica uma ação histórica,
    # e não necessariamente o status atual do registro.
    padroes_abertura_historica = [
        r"\bfoi\s+aberto\b",
        r"\bfoi\s+aberta\b",
        r"\bforam\s+abertos\b",
        r"\bforam\s+abertas\b",
        r"\btinha\s+sido\s+aberto\b",
        r"\btinha\s+sido\s+aberta\b",
        r"\baberto\s+por\b",
        r"\baberta\s+por\b",
        r"\babertos\s+por\b",
        r"\babertas\s+por\b",
    ]

    for padrao in padroes_abertura_historica:
        if re.search(
            padrao,
            texto
        ):
            return None

    return encontrar_sinonimo(
        texto,
        STATUS_SYNONYMS
    )


# ============================================================
# QUERY ANALYZER
# ============================================================

def analisar_pergunta(
    pergunta: str
) -> dict:
    """
    Extrai filtros estruturados da pergunta.

    Filtros atualmente suportados:
    - customer_id
    - state
    - module
    - doc_type
    - priority
    - status
    """

    texto = normalizar_texto(
        pergunta
    )

    filtros = {}

    # --------------------------------------------------------
    # EXTRAÇÕES
    # --------------------------------------------------------

    customer_id = extrair_customer_id(
        pergunta
    )

    state = extrair_state(
        texto
    )

    module = extrair_module(
        texto
    )

    doc_type = extrair_doc_type(
        texto
    )

    priority = extrair_priority(
        texto
    )

    status = extrair_status(
        texto
    )

    # ========================================================
    # AJUSTES CONTEXTUAIS PARA CONSULTAS COMPLEXAS
    # ========================================================
    #
    # Alguns termos podem descrever o conteúdo da pergunta
    # sem significar que a recuperação deva ficar limitada
    # a um único doc_type.
    #
    # Exemplo:
    # "analise o e-mail e determine o reembolso"
    # precisa recuperar e-mail + política + cadastro.
    # ========================================================

    # --------------------------------------------------------
    # MULTI-HOP: CANCELAMENTO / REEMBOLSO
    # --------------------------------------------------------

    if (
        (
            "reembolso" in texto
            or "cancelamento" in texto
        )
        and (
            "e-mail" in texto
            or "email" in texto
            or "cliente" in texto
            or "contrato" in texto
        )
    ):
        # A resposta pode depender simultaneamente de
        # email, policy e customer.
        #
        # Também removemos state porque expressões como
        # "determine se ela..." não podem ser interpretadas
        # como o estado SE (Sergipe).
        state = None
        module = None
        doc_type = None

    # --------------------------------------------------------
    # CONSULTAS SOBRE TEF / PINPAD
    # --------------------------------------------------------
    #
    # O domínio TEF normalmente pertence ao VendeFácil Pay,
    # mas nem todas as fontes relevantes possuem module="pay".
    #
    # Atas e manuais não estruturados podem possuir module=None.
    # Por isso a estratégia varia conforme a intenção:
    #
    # 1) reunião / retrospectiva / post-mortem:
    #       prioriza atas, sem restringir módulo;
    #
    # 2) diagnóstico que pede causa + solução/procedimento:
    #       recuperação heterogênea, permitindo ticket,
    #       manual, ata, email e logs;
    #
    # 3) consulta TEF comum:
    #       prioriza module="pay".
    # --------------------------------------------------------

    termos_tef = [
        "tef",
        "pinpad",
        "porta 6090",
        "tcp 6090",
        "pay-504",
        "timeout de confirmacao",
        "timeout de comunicacao",
    ]

    consulta_tef = (
        any(
            termo in texto
            for termo in termos_tef
        )
        or re.search(
            r"\bpay-\d+\b",
            texto
        )
    )

    if consulta_tef:

        intencao_reuniao = any(
            termo in texto
            for termo in [
                "reuniao",
                "retrospectiva",
                "post-mortem",
                "post mortem",
                "decisoes aprovadas",
                "acoes aprovadas",
                "incidente de queda",
            ]
        )

        intencao_diagnostico = any(
            termo in texto
            for termo in [
                "por que",
                "causa",
                "causa raiz",
                "procedimento",
                "solucao",
                "resolver",
                "resolucao",
                "correcao",
                "como corrigir",
            ]
        )

        if intencao_reuniao:
            module = None
            doc_type = "ata"

        elif intencao_diagnostico:
            # Diagnósticos técnicos podem exigir múltiplas fontes:
            # ticket + manual + ata + log.
            module = None
            doc_type = None

        else:
            module = "pay"
            doc_type = None

    # --------------------------------------------------------
    # CONSULTAS PROCEDIMENTAIS EM MANUAIS
    # --------------------------------------------------------
    #
    # Alguns documentos não estruturados possuem module=None.
    # Portanto, quando a pergunta pede explicitamente um
    # procedimento/regra operacional documentada, é mais seguro
    # priorizar doc_type=manual sem exigir module.
    #
    # Isso evita excluir manuais apenas porque termos como
    # "PDV", "Loja" ou "Estoque" aparecem na pergunta.
    # --------------------------------------------------------

    intencao_procedimental = any(
        expressao in texto
        for expressao in [
            "como realizar",
            "como deve ser realizado",
            "como deve ser realizada",
            "passo a passo",
            "procedimento",
            "qual e a regra",
            "qual a regra",
        ]
    )

    assunto_manual = any(
        termo in texto
        for termo in [
            "sangria",
            "suprimento",
            "safety stock",
            "estoque de seguranca",
            "margem de seguranca",
        ]
    )

    if (
        intencao_procedimental
        and assunto_manual
    ):
        module = None
        doc_type = "manual"

    # --------------------------------------------------------
    # CONSULTAS ANALÍTICAS SOBRE MRR
    # --------------------------------------------------------

    if (
        "mrr" in texto
        or "receita recorrente mensal" in texto
    ):
        # customers.csv contém MRR e main_product.
        # Portanto "produto" na pergunta não deve
        # transformar a consulta em doc_type=product.
        doc_type = "customer"
        module = None

    # --------------------------------------------------------
    # ERROS TÉCNICOS DE SINCRONIZAÇÃO DE ESTOQUE
    # --------------------------------------------------------

    if (
        re.search(r"\bstk-\d+\b", texto)
        or "conflict during inventory sync" in texto
    ):
        module = None

        # O procedimento de solução está na documentação,
        # não em cadastro de loja.
        doc_type = "manual"

    # --------------------------------------------------------
    # CONSULTAS GENÉRICAS SOBRE CUSTOMER_ID
    # --------------------------------------------------------
    #
    # Exemplo:
    #
    # "Quais informações existem sobre o cliente CUST001?"
    #
    # deve produzir:
    #
    # customer_id = CUST001
    # doc_type = customer
    #
    # Mas:
    #
    # "Quais tickets existem para o CUST092?"
    #
    # continua sendo:
    #
    # customer_id = CUST092
    # doc_type = ticket
    # --------------------------------------------------------

    if (
        customer_id
        and not doc_type
    ):

        padroes_consulta_cliente = [
            r"\binformacoes\b.*\bcliente\b",
            r"\bdados\b.*\bcliente\b",
            r"\bcadastro\b.*\bcliente\b",

            r"\binformacoes\b.*\bcust\d+\b",
            r"\bdados\b.*\bcust\d+\b",
            r"\bcadastro\b.*\bcust\d+\b",
        ]

        for padrao in padroes_consulta_cliente:

            if re.search(
                padrao,
                texto
            ):
                doc_type = "customer"
                break

    # --------------------------------------------------------
    # MONTA FILTROS
    # --------------------------------------------------------

    if customer_id:
        filtros[
            "customer_id"
        ] = customer_id

    if state:
        filtros[
            "state"
        ] = state

    if module:
        filtros[
            "module"
        ] = module

    if doc_type:
        filtros[
            "doc_type"
        ] = doc_type

    if priority:
        filtros[
            "priority"
        ] = priority

    if status:
        filtros[
            "status"
        ] = status

    return filtros


# ============================================================
# VALIDAÇÃO DOS FILTROS
# ============================================================

def validar_filtros(
    filtros: dict,
    documentos
) -> dict:
    """
    Valida os filtros extraídos contra valores realmente
    existentes nos metadados dos documentos.

    A comparação é normalizada.

    O valor devolvido é o valor canônico presente na base.

    Exemplos:

    Critica
        -> Crítica

    cust001
        -> CUST001
    """

    filtros_validados = {}

    if not filtros:
        return filtros_validados

    for campo, valor_extraido in filtros.items():

        valor_normalizado = normalizar_texto(
            str(
                valor_extraido
            )
        )

        valores_reais = {
            str(
                doc.metadata[campo]
            ).strip()

            for doc in documentos

            if doc.metadata.get(
                campo
            )
            not in (
                None,
                ""
            )
        }

        for valor_real in valores_reais:

            if (
                normalizar_texto(
                    valor_real
                )
                ==
                valor_normalizado
            ):

                filtros_validados[
                    campo
                ] = valor_real

                break

    return filtros_validados


# ============================================================
# ANALISAR + VALIDAR
# ============================================================

def analisar_e_validar(
    pergunta: str,
    documentos
) -> dict:
    """
    Pipeline do Query Analyzer:

    pergunta
        ↓
    extração
        ↓
    normalização
        ↓
    validação nos metadados
        ↓
    filtros canônicos
    """

    filtros_extraidos = analisar_pergunta(
        pergunta
    )

    return validar_filtros(
        filtros_extraidos,
        documentos
    )


# ============================================================
# TESTES LOCAIS
# ============================================================

if __name__ == "__main__":

    perguntas = [

        (
            "Quais tickets de clientes de Minas Gerais "
            "estão relacionados ao módulo de estoque?"
        ),

        (
            "Quais problemas do módulo de pagamento "
            "aparecem para clientes de São Paulo?"
        ),

        (
            "Quais tickets críticos do módulo de pagamento "
            "existem para clientes do Rio de Janeiro?"
        ),

        (
            "Quais chamados de alta prioridade existem em MG?"
        ),

        (
            "Quais políticas falam sobre segurança?"
        ),

        (
            "Mostre os produtos relacionados ao estoque."
        ),

        (
            "Quais clientes de Minas Gerais estão ativos?"
        ),

        (
            "Quais informações existem sobre o cliente CUST001?"
        ),

        (
            "Quais tickets existem para o CUST092?"
        ),

        (
            "Mostre os logs do cliente CUST277."
        ),
    ]

    for pergunta in perguntas:

        print(
            "\n"
            + "=" * 80
        )

        print(
            "PERGUNTA:"
        )

        print(
            pergunta
        )

        print(
            "FILTROS EXTRAÍDOS:"
        )

        print(
            analisar_pergunta(
                pergunta
            )
        )
