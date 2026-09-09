
import re

from langchain_community.retrievers import BM25Retriever

from ingest import carregar_todos_documentos
from load_index import carregar_indice
try:
    from .query_analyzer import analisar_e_validar
except ImportError:
    from query_analyzer import analisar_e_validar


# ============================================================
# TOKENIZAÇÃO DO BM25
# ============================================================

def tokenizar_bm25(texto: str):
    """
    Tokenização lexical para o BM25.

    - converte para minúsculas;
    - remove pontuação externa;
    - preserva códigos com hífen.

    Exemplos preservados:
    TCK-1057
    PAY-200
    PDV-500
    """

    if texto is None:
        return []

    return re.findall(
        r"[a-zA-ZÀ-ÿ0-9]+(?:-[a-zA-ZÀ-ÿ0-9]+)*",
        str(texto).lower()
    )


# ============================================================
# CARREGAMENTO INICIAL
# ============================================================

print("1. Carregando documentos...")

documentos = carregar_todos_documentos()

print(
    f"Total de documentos: {len(documentos)}"
)


print("2. Carregando índice FAISS...")

db_denso = carregar_indice()


print("3. Configurando BM25...")

retriever_esparso = BM25Retriever.from_documents(
    documentos,
    preprocess_func=tokenizar_bm25
)

retriever_esparso.k = 5


# ============================================================
# FILTRO DE METADADOS
# ============================================================

def documento_atende_filtros(
    doc,
    filtros: dict
) -> bool:
    """
    Verifica se um documento satisfaz todos
    os filtros de metadados.
    """

    if not filtros:
        return True

    for campo, valor_esperado in filtros.items():

        valor_documento = doc.metadata.get(
            campo
        )

        if valor_documento is None:
            return False

        if (
            str(valor_documento).strip().lower()
            != str(valor_esperado).strip().lower()
        ):
            return False

    return True


def filtrar_documentos(
    documentos,
    filtros: dict
):
    """
    Pré-filtra os documentos antes da busca BM25.

    Isso evita que documentos incompatíveis
    com os filtros retornem no ranking lexical.
    """

    if not filtros:
        return documentos

    return [
        doc
        for doc in documentos
        if documento_atende_filtros(
            doc,
            filtros
        )
    ]


# ============================================================
# RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    dense_results,
    sparse_results,
    k=60
):
    """
    Combina os rankings Dense e BM25 usando
    Reciprocal Rank Fusion.

    score_RRF =
        soma de 1 / (k + posição)

    O chunk_id é utilizado como identificador
    principal do documento.
    """

    fused_scores = {}

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    for rank, doc in enumerate(
        dense_results,
        start=1
    ):

        doc_id = doc.metadata.get(
            "chunk_id",
            doc.page_content
        )

        if doc_id not in fused_scores:

            fused_scores[doc_id] = {
                "doc": doc,
                "score": 0.0
            }

        fused_scores[doc_id]["score"] += (
            1.0 / (k + rank)
        )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    for rank, doc in enumerate(
        sparse_results,
        start=1
    ):

        doc_id = doc.metadata.get(
            "chunk_id",
            doc.page_content
        )

        if doc_id not in fused_scores:

            fused_scores[doc_id] = {
                "doc": doc,
                "score": 0.0
            }

        fused_scores[doc_id]["score"] += (
            1.0 / (k + rank)
        )

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------

    ordenados = sorted(
        fused_scores.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        (
            item["doc"],
            item["score"]
        )
        for item in ordenados
    ]


# ============================================================
# BUSCA DENSA
# ============================================================

def buscar_denso(
    pergunta: str,
    filtros: dict = None,
    k: int = 5,
    fetch_k: int = 500
):
    """
    Busca semântica com embeddings + FAISS.

    Quando existem filtros, usa fetch_k maior
    porque o FAISS recupera candidatos primeiro
    e o filtro é aplicado depois.
    """

    resultados = db_denso.similarity_search(
        pergunta,
        k=k,
        fetch_k=fetch_k,
        filter=(
            filtros
            if filtros
            else None
        )
    )

    return resultados


# ============================================================
# BUSCA BM25
# ============================================================

def buscar_bm25(
    pergunta: str,
    filtros: dict = None,
    k: int = 5
):
    """
    Busca lexical com BM25.

    Para consultas filtradas, os documentos
    são pré-filtrados antes da criação
    do retriever.
    """

    documentos_filtrados = filtrar_documentos(
        documentos,
        filtros or {}
    )

    if not documentos_filtrados:
        return []

    retriever = BM25Retriever.from_documents(
        documentos_filtrados,
        preprocess_func=tokenizar_bm25
    )

    retriever.k = min(
        k,
        len(documentos_filtrados)
    )

    return retriever.invoke(
        pergunta
    )


# ============================================================
# BUSCA HÍBRIDA
# ============================================================

def buscar_hibrido(
    pergunta: str,
    usar_filtros: bool = True,
    k: int = 5,
    fetch_k: int = 500
):
    """
    Pipeline completo de recuperação:

    pergunta
        ↓
    Query Analyzer
        ↓
    filtros validados
        ↓
    Dense + BM25
        ↓
    RRF
        ↓
    expansão contextual de atas fragmentadas
        ↓
    ranking final

    A expansão contextual preserva os k resultados principais
    do RRF e, quando a pergunta solicita conteúdo global de uma
    reunião/retrospectiva, acrescenta chunks do mesmo documento.

    Isso evita perder informações que estejam em seções posteriores
    de uma ata dividida em múltiplos chunks.
    """

    import re
    import unicodedata

    # --------------------------------------------------------
    # FILTROS
    # --------------------------------------------------------

    if usar_filtros:

        filtros = analisar_e_validar(
            pergunta,
            documentos
        )

    else:

        filtros = {}

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    resultados_densos = buscar_denso(
        pergunta=pergunta,
        filtros=filtros,
        k=k,
        fetch_k=fetch_k
    )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    resultados_esparsos = buscar_bm25(
        pergunta=pergunta,
        filtros=filtros,
        k=k
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    ranking_final = reciprocal_rank_fusion(
        resultados_densos,
        resultados_esparsos,
        k=60
    )

    ranking_principal = ranking_final[:k]

    # ========================================================
    # EXPANSÃO CONTEXTUAL DE DOCUMENTOS FRAGMENTADOS
    # ========================================================
    #
    # Algumas atas possuem:
    #
    # arquivo_md_0000 -> título / participantes
    # arquivo_md_0001 -> resumo
    # arquivo_md_0002 -> causa
    # arquivo_md_0003 -> decisões
    #
    # O embedding pode recuperar corretamente o documento,
    # porém apenas o primeiro chunk. Para perguntas que pedem
    # decisões, ações ou conteúdo de uma retrospectiva/reunião,
    # acrescentamos os demais chunks da mesma ata.
    #
    # Os resultados principais NÃO são substituídos.
    # A expansão é acrescentada depois deles.
    # ========================================================

    def normalizar_local(valor: str) -> str:

        valor = str(
            valor or ""
        ).lower()

        valor = unicodedata.normalize(
            "NFD",
            valor
        )

        valor = "".join(
            c
            for c in valor
            if unicodedata.category(c) != "Mn"
        )

        return valor

    texto_pergunta = normalizar_local(
        pergunta
    )

    intencao_documento_completo = any(
        termo in texto_pergunta
        for termo in [
            "reuniao",
            "retrospectiva",
            "post-mortem",
            "post mortem",
            "decisoes",
            "acoes aprovadas",
            "decisoes aprovadas",
            "ata",
        ]
    )

    ranking_expandido = list(
        ranking_principal
    )

    ids_presentes = {
        doc.metadata.get("chunk_id")
        for doc, _ in ranking_expandido
    }

    if intencao_documento_completo:

        # Fontes de atas que já apareceram entre os resultados
        # principais.
        fontes_atas = []

        for doc, score in ranking_principal:

            if (
                doc.metadata.get("doc_type")
                == "ata"
            ):

                source_file = doc.metadata.get(
                    "source_file"
                )

                if (
                    source_file
                    and source_file not in fontes_atas
                ):
                    fontes_atas.append(
                        source_file
                    )

        # Expande prioritariamente a primeira ata recuperada,
        # que representa o documento mais relevante segundo RRF.
        if fontes_atas:

            fonte_principal = fontes_atas[0]

            chunks_mesma_ata = [
                doc
                for doc in documentos
                if (
                    doc.metadata.get("source_file")
                    == fonte_principal
                    and doc.metadata.get("doc_type")
                    == "ata"
                )
            ]

            # Ordenação natural pelo sufixo numérico do chunk.
            def numero_chunk(doc):

                chunk_id = str(
                    doc.metadata.get(
                        "chunk_id",
                        ""
                    )
                )

                match = re.search(
                    r"_(\\d+)$",
                    chunk_id
                )

                if match:
                    return int(
                        match.group(1)
                    )

                return 999999

            chunks_mesma_ata.sort(
                key=numero_chunk
            )

            # Limite pequeno para não inflar excessivamente
            # o contexto da geração.
            limite_extra = 4
            adicionados = 0

            for doc in chunks_mesma_ata:

                chunk_id = doc.metadata.get(
                    "chunk_id"
                )

                if chunk_id in ids_presentes:
                    continue

                # Score de expansão deliberadamente inferior
                # aos scores obtidos pelo RRF. Ele serve apenas
                # para manter compatibilidade com a estrutura
                # (Document, score).
                score_expansao = 0.0

                ranking_expandido.append(
                    (
                        doc,
                        score_expansao
                    )
                )

                ids_presentes.add(
                    chunk_id
                )

                adicionados += 1

                if adicionados >= limite_extra:
                    break

    return {
        "pergunta": pergunta,
        "filtros": filtros,
        "dense": resultados_densos,
        "bm25": resultados_esparsos,
        "rrf": ranking_expandido,
    }


# ============================================================
# EXIBIÇÃO AUXILIAR
# ============================================================

def mostrar_resultados(
    titulo,
    docs
):
    print("\n" + "=" * 90)

    print(titulo)

    print("=" * 90)

    if not docs:

        print(
            "Nenhum resultado encontrado."
        )

        return

    for posicao, doc in enumerate(
        docs,
        start=1
    ):

        print("\n" + "-" * 70)

        print(
            f"Resultado {posicao}"
        )

        print(
            "Chunk:",
            doc.metadata.get("chunk_id")
        )

        print(
            "Fonte:",
            doc.metadata.get("source_file")
        )

        print(
            "Tipo:",
            doc.metadata.get("doc_type")
        )

        print(
            "Estado:",
            doc.metadata.get("state")
        )

        print(
            "Módulo:",
            doc.metadata.get("module")
        )

        print(
            "Texto:",
            doc.page_content[:300]
        )


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    pergunta = (
        "Quais tickets de clientes de Minas Gerais "
        "estão relacionados ao módulo de estoque?"
    )

    resultado = buscar_hibrido(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    print("\n" + "#" * 90)

    print("PERGUNTA")

    print("#" * 90)

    print(
        resultado["pergunta"]
    )

    print("\nFILTROS:")

    print(
        resultado["filtros"]
    )

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    mostrar_resultados(
        "DENSE",
        resultado["dense"]
    )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    mostrar_resultados(
        "BM25",
        resultado["bm25"]
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    print("\n" + "=" * 90)

    print("RRF")

    print("=" * 90)

    if not resultado["rrf"]:

        print(
            "Nenhum resultado encontrado."
        )

    else:

        for posicao, (
            doc,
            score
        ) in enumerate(
            resultado["rrf"],
            start=1
        ):

            print("\n" + "-" * 70)

            print(
                f"Resultado {posicao}"
            )

            print(
                f"Score RRF: {score:.6f}"
            )

            print(
                "Chunk:",
                doc.metadata.get(
                    "chunk_id"
                )
            )

            print(
                "Fonte:",
                doc.metadata.get(
                    "source_file"
                )
            )

            print(
                "Tipo:",
                doc.metadata.get(
                    "doc_type"
                )
            )

            print(
                "Estado:",
                doc.metadata.get(
                    "state"
                )
            )

            print(
                "Módulo:",
                doc.metadata.get(
                    "module"
                )
            )

            print(
                "Texto:",
                doc.page_content[:300]
            )
