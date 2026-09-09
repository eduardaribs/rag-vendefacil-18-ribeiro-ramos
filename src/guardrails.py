import re
import unicodedata


def _normalizar_texto(texto: str) -> str:
    """
    Normalização auxiliar apenas para classificação de intenção.
    Não altera o texto que será apresentado ao usuário.
    """

    texto = str(texto or "").lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return texto


# ============================================================
# FORA DE ESCOPO
# ============================================================

def verificar_fora_de_escopo(pergunta: str) -> dict:
    """
    Verifica se a pergunta pertence ao domínio da VendeFácil.

    Perguntas sobre clientes, políticas, contratos, LGPD,
    produtos e operações também pertencem ao domínio.
    """

    texto = _normalizar_texto(pergunta)

    termos_dominio = [
        "vendefacil",
        "vende facil",
        "cliente",
        "clientes",
        "ticket",
        "tickets",
        "chamado",
        "log",
        "logs",
        "estoque",
        "pdv",
        "ponto de venda",
        "pagamento",
        "pagamentos",
        "pay",
        "ecommerce",
        "e-commerce",
        "analytics",
        "loja",
        "lojas",
        "produto",
        "produtos",
        "reembolso",
        "cancelamento",
        "contrato",
        "politica",
        "lgpd",
        "mrr",
        "receita recorrente",
        "sangria",
        "sincronizacao",
        "inventory sync",
        "stk-",
        "funcionario",
        "funcionarios",
        "venda",
        "vendas",
        "tef",
        "pinpad",
        "firewall",
        "porta 6090",
        "retrospectiva",
        "post-mortem",
        "incidente",
        "outage",
    ]

    if any(
        termo in texto
        for termo in termos_dominio
    ):
        return {
            "permitido": True
        }

    termos_fora_escopo = [
        "capital da franca",
        "capital da espanha",
        "capital do brasil",
        "receita de bolo",
        "previsao do tempo",
        "clima hoje",
        "resultado do futebol",
        "campeonato brasileiro",
        "horoscopo",
    ]

    if any(
        termo in texto
        for termo in termos_fora_escopo
    ):
        return {
            "permitido": False,
            "mensagem": (
                "Desculpe, mas só posso responder dúvidas "
                "relacionadas aos sistemas, dados, políticas "
                "e operações da VendeFácil."
            )
        }

    # Na ausência de indícios do domínio, mantém comportamento
    # conservador e considera fora de escopo.
    return {
        "permitido": False,
        "mensagem": (
            "Desculpe, mas só posso responder dúvidas "
            "relacionadas aos sistemas, dados, políticas "
            "e operações da VendeFácil."
        )
    }


# ============================================================
# LGPD
# ============================================================

def aplicar_guardrails_lgpd(texto: str) -> dict:
    """
    Aplica guardrails de privacidade.

    Distingue:
    - discussão conceitual sobre CPF, salário, PIX etc.;
    - solicitação ou exposição efetiva de dado confidencial.

    Assim, uma política pode mencionar "CPF" sem ser bloqueada,
    desde que nenhum CPF real seja exposto.
    """

    texto = str(texto or "")
    texto_normalizado = _normalizar_texto(texto)

    # --------------------------------------------------------
    # 1. DADOS EFETIVAMENTE SENSÍVEIS PRESENTES NO TEXTO
    # --------------------------------------------------------

    # CPF real
    if re.search(
        r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        texto
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: CPF identificado "
                "diretamente no texto."
            ),
            "resposta_segura": None
        }

    # Dados bancários / chave PIX explicitamente informados
    if re.search(
        r"(?i)\b(?:pix|agência|agencia|conta bancária|conta bancaria)"
        r"\s*[:=-]\s*[\w.@+\-]+",
        texto
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: dado bancário ou "
                "chave PIX identificada diretamente."
            ),
            "resposta_segura": None
        }

    # Credenciais explicitamente apresentadas
    if re.search(
        r"(?i)\b(?:senha|password|token|credencial)"
        r"\s*[:=-]\s*\S+",
        texto
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: credencial "
                "identificada diretamente."
            ),
            "resposta_segura": None
        }

    # Salário/remuneração apresentado como valor individual
    if re.search(
        r"(?i)\b(?:salário|salario|remuneração|remuneracao)"
        r"\s*[:=-]\s*(?:r\$\s*)?\d",
        texto
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: remuneração individual "
                "identificada diretamente."
            ),
            "resposta_segura": None
        }

    # Dados médicos explicitamente associados a um campo
    if re.search(
        r"(?i)\b(?:diagnóstico|diagnostico|doença|doenca|prontuário|prontuario)"
        r"\s*[:=-]\s*\S+",
        texto
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: informação de saúde "
                "identificada diretamente."
            ),
            "resposta_segura": None
        }

    # --------------------------------------------------------
    # 2. INTENÇÃO EXPLÍCITA DE OBTER DADO RESTRITO
    # --------------------------------------------------------

    termos_sensiveis = (
        r"(?:senha|password|token|credencial|"
        r"diagnostico|doenca|prontuario|"
        r"salario|remuneracao|cpf|pix)"
    )

    verbos_solicitacao = (
        r"(?:qual|quais|informe|informar|mostre|mostrar|"
        r"forneca|fornecer|diga|revele|revelar|"
        r"quero|preciso|acesse|acessar|consulte|consultar)"
    )

    padrao_solicitacao = (
        rf"\b{verbos_solicitacao}\b"
        rf".{{0,80}}"
        rf"\b{termos_sensiveis}\b"
    )

    if re.search(
        padrao_solicitacao,
        texto_normalizado
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: tentativa de acesso "
                "a informação pessoal ou confidencial."
            ),
            "resposta_segura": None
        }

    # Também captura:
    # "salário da Ana", "CPF do cliente", "PIX de João" etc.
    padrao_posse_sensivel = (
        rf"\b{termos_sensiveis}\b"
        r"\s+(?:de|do|da|dos|das)\s+"
        r"[a-z0-9]"
    )

    if re.search(
        padrao_posse_sensivel,
        texto_normalizado
    ):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: solicitação ou exposição "
                "de informação individual restrita."
            ),
            "resposta_segura": None
        }

    # --------------------------------------------------------
    # 3. DADOS MASCARÁVEIS
    # --------------------------------------------------------

    texto_mascarado = texto

    # Cartão
    texto_mascarado = re.sub(
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "****.****.****.****",
        texto_mascarado
    )

    # E-mail
    texto_mascarado = re.sub(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "[E-MAIL_REMOVIDO]",
        texto_mascarado
    )

    # Telefone
    texto_mascarado = re.sub(
        r"\(\d{2}\)\s?\d{4,5}-\d{4}",
        "(__) _____-____",
        texto_mascarado
    )

    # Endereço
    texto_mascarado = re.sub(
        r"(?i)\b(rua|avenida|av\.)[ \t]+[A-Za-zÀ-ÿ0-9 .-]+",
        r"\1 [ENDEREÇO_OCULTO]",
        texto_mascarado
    )

    return {
        "status": (
            "mascarado"
            if texto_mascarado != texto
            else "permitido"
        ),
        "resposta_segura": texto_mascarado
    }
