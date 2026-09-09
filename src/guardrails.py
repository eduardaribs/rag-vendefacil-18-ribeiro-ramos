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


# === PATCH CREDENCIAIS ETAPA 4 ===
# Diferencia:
#   1) instrução procedural que apenas menciona autenticação;
#   2) solicitação de segredo;
#   3) exposição de segredo real.

_aplicar_guardrails_lgpd_base = aplicar_guardrails_lgpd


def _normalizar_credencial(texto: str) -> str:
    import unicodedata

    texto = str(texto or "")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return texto.lower().strip()


def _pedido_explicito_credencial(texto: str) -> bool:
    """
    Detecta quando alguém está pedindo o VALOR de uma credencial.
    Exemplos:
      - qual é a senha?
      - me informe a API key
      - forneça o token JWT
    """
    import re

    t = _normalizar_credencial(texto)

    credencial = (
        r"(?:"
        r"senha|password|"
        r"api\s*key|chave\s*(?:de|da)?\s*api|"
        r"token(?:\s+jwt)?|jwt(?:\s+secret)?|"
        r"secret(?:\s+key)?|client\s+secret"
        r")"
    )

    padroes = [
        rf"\bqual(?:\s+e|\s+eh)?\s+(?:a|o)?\s*{credencial}\b",

        rf"\b(?:me\s+)?"
        rf"(?:informe|forneca|revele|mostre|diga|envie|passe)"
        rf"\s+(?:a|o)?\s*{credencial}\b",

        rf"\bpreciso\s+(?:da|do|de)\s+{credencial}\b",

        rf"\bquero\s+(?:a|o)?\s*{credencial}\b",

        rf"\bdescubra\s+(?:a|o)?\s*{credencial}\b",
    ]

    return any(
        re.search(p, t, flags=re.IGNORECASE)
        for p in padroes
    )


def _exposicao_credencial(texto: str) -> bool:
    """
    Detecta texto que contém uma credencial seguida de um valor.

    Exemplos:
      - senha do admin = admin123
      - API key: sk-xxxxx
      - token JWT é abc123xyz
    """
    import re

    t = _normalizar_credencial(texto)

    credencial = (
        r"(?:"
        r"senha|password|"
        r"api\s*key|chave\s*(?:de|da)?\s*api|"
        r"token(?:\s+jwt)?|jwt(?:\s+secret)?|"
        r"secret(?:\s+key)?|client\s+secret"
        r")"
    )

    # Permite algumas palavras entre o nome da credencial e o separador.
    # Ex.: "senha do administrador é admin123"
    padrao_valor = (
        rf"\b{credencial}\b"
        rf"(?:\s+(?:do|da|de|para|producao|administrador|admin|sistema|cliente))*"
        rf"\s*(?:=|:|\be\b|\beh\b)"
        rf"\s*[\"']?"
        rf"[a-zA-Z0-9_\-./+=]{{4,}}"
    )

    if re.search(
        padrao_valor,
        t,
        flags=re.IGNORECASE
    ):
        return True

    # Formatos típicos de segredos técnicos
    formatos_secretos = [
        r"\bsk-[a-zA-Z0-9_\-]{8,}\b",
        r"\bghp_[a-zA-Z0-9]{8,}\b",
        r"\bAIza[a-zA-Z0-9_\-]{10,}\b",
        r"\beyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\b",
    ]

    return any(
        re.search(p, texto)
        for p in formatos_secretos
    )


def _mencao_procedural_de_senha(texto: str) -> bool:
    """
    Detecta instruções legítimas em que 'senha' representa apenas
    um requisito de autenticação e nenhum valor secreto é divulgado.

    Exemplos:
      - Insira a senha do supervisor.
      - Digite a senha do gerente.
      - O sistema solicita a senha do operador.
    """
    import re

    t = _normalizar_credencial(texto)

    if "senha" not in t and "password" not in t:
        return False

    if _pedido_explicito_credencial(texto):
        return False

    if _exposicao_credencial(texto):
        return False

    padroes = [
        r"\b(?:insira|digite|utilize|use)\s+(?:a\s+)?senha\b",
        r"\bsistema\s+(?:solicita|exige|pedira|pede)\s+(?:a\s+)?senha\b",
        r"\bsenha\s+(?:do|da)\s+(?:supervisor|gerente|operador)\b",
        r"\bautenticacao\s+(?:do|da)\s+(?:supervisor|gerente|operador)\b",
    ]

    return any(
        re.search(p, t)
        for p in padroes
    )


def aplicar_guardrails_lgpd(texto: str):
    """
    Camada refinada de proteção de credenciais.

    Regra:
      - pedido pelo VALOR de segredo -> recusa;
      - exposição de segredo -> recusa;
      - simples instrução de autenticação -> permitida;
      - demais dados continuam sob o guardrail original.
    """

    original = str(texto or "")

    # --------------------------------------------------------
    # 1. Solicitação de segredo
    # --------------------------------------------------------

    if _pedido_explicito_credencial(original):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: tentativa de acesso "
                "a credencial ou informação confidencial."
            ),
            "resposta_segura": None,
        }

    # --------------------------------------------------------
    # 2. Exposição de segredo
    # --------------------------------------------------------

    if _exposicao_credencial(original):
        return {
            "status": "recusado",
            "motivo": (
                "Violação de política: exposição de credencial "
                "ou informação confidencial."
            ),
            "resposta_segura": None,
        }

    # --------------------------------------------------------
    # 3. Menção procedural legítima
    # --------------------------------------------------------

    if _mencao_procedural_de_senha(original):

        # O guardrail antigo confundia a palavra "senha" com
        # exposição de credencial. Passamos uma versão neutra
        # somente para que as OUTRAS verificações continuem ativas.
        import re

        texto_neutro = re.sub(
            r"\bsenha\b",
            "autenticação",
            original,
            flags=re.IGNORECASE,
        )

        resultado = _aplicar_guardrails_lgpd_base(
            texto_neutro
        )

        # Se algum OUTRO dado sensível foi detectado,
        # preservamos a decisão do guardrail original.
        if resultado.get("status") != "permitido":
            return resultado

        # Como não havia valor de senha, podemos conservar
        # a frase original.
        return {
            "status": "permitido",
            "resposta_segura": original,
        }

    # --------------------------------------------------------
    # 4. Demais casos usam exatamente o guardrail anterior
    # --------------------------------------------------------

    return _aplicar_guardrails_lgpd_base(original)

