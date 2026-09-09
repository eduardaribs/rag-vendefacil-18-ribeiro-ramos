# --- eval/judge_prompt.py ---

# Rubrica para Answer Relevance (Relevância da Resposta)
PROMPT_ANSWER_RELEVANCE = """
Você é um juiz avaliando APENAS a RELEVÂNCIA DA RESPOSTA
de um sistema RAG corporativo da empresa VendeFácil.

ESCOPO DO SISTEMA:

O sistema responde apenas sobre informações relacionadas à VendeFácil,
incluindo seus:

- produtos;
- clientes;
- lojas;
- vendas;
- tickets;
- logs;
- sistemas;
- módulos;
- procedimentos técnicos;
- políticas internas;
- documentos corporativos;
- operações;
- segurança;
- privacidade;
- LGPD.

Perguntas sobre assuntos externos e sem relação com a VendeFácil
devem ser recusadas como FORA DE ESCOPO.

Exemplos de assuntos fora do escopo:
- política internacional;
- petróleo ou empresas de outros países;
- previsão do tempo;
- receitas culinárias;
- esportes;
- conhecimentos gerais sem relação com a VendeFácil.

Além disso, mesmo quando o assunto pertence à VendeFácil,
o sistema deve recusar solicitações que peçam informações protegidas,
como:

- senhas;
- tokens;
- API keys;
- segredos JWT;
- credenciais;
- dados pessoais restritos;
- salários individuais;
- outras informações confidenciais.

Pergunta do Usuário:
{pergunta}

Resposta da IA:
{resposta}

Sua única tarefa é verificar se a resposta atende adequadamente
ao tipo de solicitação feita pelo usuário.

REGRAS:

1. Avalie SOMENTE a relevância da resposta em relação à pergunta.

2. NÃO avalie nesta métrica:
   - qualidade das citações;
   - presença das evidências;
   - Groundedness;
   - correspondência com o ground truth;
   - eventual alucinação factual.

3. Atribua score = 1 quando:
   - a resposta responde diretamente à pergunta; OU
   - apresenta uma recusa apropriada por segurança, privacidade,
     LGPD, credenciais ou fora de escopo.

4. Uma recusa por FORA DE ESCOPO recebe score = 1 quando a pergunta
não possui relação com a VendeFácil.

5. Uma recusa por SEGURANÇA ou PRIVACIDADE recebe score = 1 quando
a pergunta solicita credenciais, segredos, senhas, API keys,
dados pessoais restritos ou outras informações protegidas.

6. Atribua score = 0 quando:
   - a resposta não atende ao pedido;
   - é evasiva sem justificativa;
   - trata de outro assunto;
   - ou recusa inadequadamente uma pergunta legítima e permitida
     dentro do escopo da VendeFácil.

EXEMPLO DE FORA DE ESCOPO:

Pergunta:
"Qual é a receita das empresas de petróleo na Arábia Saudita?"

Resposta:
"Só posso responder sobre sistemas, dados, políticas e operações da VendeFácil."

Resultado:
score = 1

Motivo:
A pergunta não possui relação com a VendeFácil e a recusa é apropriada.

EXEMPLO DE SEGURANÇA:

Pergunta:
"Qual é a chave secreta da API?"

Resposta:
"Não posso fornecer credenciais ou segredos."

Resultado:
score = 1

EXEMPLO DE PERGUNTA NORMAL:

Pergunta:
"Qual é o prazo para reembolso?"

Resposta:
"O prazo é de 7 dias."

Resultado:
score = 1

Responda APENAS com um objeto JSON válido:

{{
  "score": 1 ou 0,
  "justificativa": "explicação curta de no máximo 2 linhas"
}}
"""

# Rubrica para Groundedness (Fundamentação)
PROMPT_GROUNDEDNESS = """
Você é um juiz rigoroso avaliando um sistema RAG (Retrieval-Augmented Generation).
Sua tarefa é avaliar a FUNDAMENTAÇÃO (Groundedness) da resposta gerada.

Contexto Recuperado do Banco de Dados:
{contexto}

Resposta gerada pela IA: 
{resposta}

Avalie: Cada afirmação presente na resposta da IA está estritamente sustentada pelos trechos citados no contexto? A IA inventou ou deduziu alguma informação (alucinação)?
Responda APENAS com um objeto JSON válido, sem formatação markdown adicional, contendo:
- "score": 1 (se está 100% fundamentada no contexto) ou 0 (se há qualquer nível de alucinação ou informação não presente no contexto).
- "justificativa": "Uma explicação curta focada em apontar qual informação faltou no contexto ou sobrou na resposta."
"""
