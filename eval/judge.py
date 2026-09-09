import json
import re
from typing import Any, Dict

from langchain_groq import ChatGroq

from eval.judge_prompt import (
    PROMPT_ANSWER_RELEVANCE,
    PROMPT_GROUNDEDNESS,
)


MODEL_NAME = "openai/gpt-oss-20b"


def _get_llm():
    return ChatGroq(
        model=MODEL_NAME,
        temperature=0,
    )


def _extrair_texto_resposta(response: Any) -> str:
    """
    Extrai o texto retornado pelo modelo.
    """
    if hasattr(response, "content"):
        return str(response.content)

    return str(response)


def _extrair_json(texto: str) -> Dict[str, Any]:
    """
    Tenta converter a resposta do LLM em JSON,
    mesmo se vier envolvida por ```json ... ```.
    """
    texto = texto.strip()

    texto = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    try:
        return json.loads(texto)

    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")

        if inicio != -1 and fim != -1 and fim > inicio:
            trecho = texto[inicio: fim + 1]
            return json.loads(trecho)

        raise


def _normalizar_resultado(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Padroniza a saída do LLM-as-judge.
    """

    if not isinstance(resultado, dict):
        raise ValueError(
            "O LLM-as-judge não retornou um objeto JSON."
        )

    score = resultado.get("score")

    justificativa = resultado.get(
        "justificativa",
        resultado.get(
            "justification",
            ""
        )
    )

    if isinstance(score, bool):
        score = int(score)

    try:
        score = float(score)
    except (TypeError, ValueError):
        raise ValueError(
            f"Score inválido retornado pelo judge: {score!r}"
        )

    if score not in (0.0, 1.0):
        raise ValueError(
            f"O score esperado é 0 ou 1, mas veio: {score}"
        )

    return {
        "score": score,
        "justificativa": str(justificativa),
        "evaluation_error": False,
    }


def _avaliar_com_llm(prompt: str) -> Dict[str, Any]:
    """
    Executa o prompt no modelo da Groq.
    """

    llm = _get_llm()

    response = llm.invoke(prompt)

    texto = _extrair_texto_resposta(response)

    resultado = _extrair_json(texto)

    return _normalizar_resultado(resultado)


def evaluate_answer_relevance(
    pergunta: str,
    resposta: str,
) -> Dict[str, Any]:
    """
    Avalia se a resposta atende diretamente à pergunta.
    """

    prompt = PROMPT_ANSWER_RELEVANCE.format(
        pergunta=pergunta,
        resposta=resposta,
    )

    try:
        return _avaliar_com_llm(prompt)

    except Exception as e:
        print(
            "Erro no LLM-as-judge "
            f"(Answer Relevance): {e}"
        )

        return {
            "score": None,
            "justificativa": (
                "Avaliação não realizada devido a erro técnico."
            ),
            "evaluation_error": True,
            "error": str(e),
        }


def evaluate_groundedness(
    contexto: str,
    resposta: str,
) -> Dict[str, Any]:
    """
    Avalia se a resposta está fundamentada
    exclusivamente no contexto recuperado.
    """

    prompt = PROMPT_GROUNDEDNESS.format(
        contexto=contexto,
        resposta=resposta,
    )

    try:
        return _avaliar_com_llm(prompt)

    except Exception as e:
        print(
            "Erro no LLM-as-judge "
            f"(Groundedness): {e}"
        )

        return {
            "score": None,
            "justificativa": (
                "Avaliação não realizada devido a erro técnico."
            ),
            "evaluation_error": True,
            "error": str(e),
        }
