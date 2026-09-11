# Mini Desafio RAG — VendeFácil Knowledge Base

Assistente de Inteligência Artificial baseado em **Retrieval-Augmented Generation (RAG)** desenvolvido para consultar a base de conhecimento da empresa fictícia **VendeFácil Tecnologia Ltda.**

O sistema processa documentos heterogêneos, realiza recuperação híbrida com filtros por metadados, gera respostas estruturadas e fundamentadas em evidências e aplica mecanismos de segurança para proteção de informações sensíveis.

---

## Integrantes

- Maria Eduarda Ribeiro da Silva
- Eridalgo Ramos da Silva

---

## Objetivo

O objetivo do projeto é desenvolver um assistente capaz de:

- processar documentos CSV, JSON, JSONL, Markdown, PDF e TXT;
- aplicar chunking adequado às diferentes fontes;
- armazenar e recuperar representações vetoriais utilizando FAISS;
- combinar recuperação semântica e lexical;
- aplicar filtros por metadados;
- gerar respostas estruturadas e fundamentadas;
- citar arquivo de origem e `chunk_id`;
- aplicar guardrails para proteção de informações restritas;
- recusar perguntas sem evidência adequada;
- avaliar o sistema por meio da RAG Triad;
- disponibilizar uma interface funcional para demonstração.

---

## Arquitetura

O fluxo principal do sistema é:

    Pergunta do usuário
            ↓
    Query Analyzer
            ↓
    Extração de filtros por metadados
            ↓
    Dense Retrieval + BM25
            ↓
    Reciprocal Rank Fusion (RRF)
            ↓
    Contextos recuperados
            ↓
    Guardrails
            ↓
    LLM
            ↓
    Validação Pydantic
            ↓
    Resposta + confiança + evidências + citações

---

## Tecnologias

O projeto utiliza principalmente:

- Python
- LangChain
- FAISS
- Pydantic
- Sentence Transformers
- BM25 (`rank-bm25`)
- Groq
- Streamlit

O modelo utilizado para embeddings é:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

---

## Base de Conhecimento

A base VendeFácil contém documentos estruturados, semiestruturados e não estruturados.

### Formatos processados

- CSV
- JSON
- JSONL
- Markdown
- PDF
- TXT

Após a ingestão e o chunking, o pipeline consolidou **5.721 documentos/chunks**.

### Metadados

Os documentos possuem os metadados obrigatórios:

- `source_file`
- `doc_type`
- `chunk_id`
- `sensitivity`

Quando aplicáveis, também são utilizados:

- `customer_id`
- `state`
- `module`
- `priority`
- `status`
- `date`
- `section`

Os níveis de sensibilidade utilizados são `publico`, `interno` e `restrito`.

---

## Recuperação Híbrida

O sistema combina recuperação semântica e lexical.

### Dense Retriever

O Dense Retriever utiliza embeddings semânticos e índice FAISS para localizar documentos semanticamente relacionados à pergunta.

Essa abordagem permite recuperar informações mesmo quando a consulta utiliza palavras diferentes das encontradas originalmente nos documentos.

### BM25

O BM25 realiza recuperação lexical e complementa a busca vetorial.

Esse mecanismo é especialmente útil para termos exatos, códigos e identificadores.

Durante os testes, uma consulta relacionada ao ticket `TCK-1057` mostrou vantagem do BM25 na localização direta do registro correspondente.

### Reciprocal Rank Fusion

Os rankings produzidos pelo Dense Retriever e pelo BM25 são combinados utilizando **Reciprocal Rank Fusion (RRF)**.

O parâmetro utilizado é `k = 60`.

Essa estratégia combina as vantagens da recuperação semântica e lexical.

---

## Query Analyzer

Antes da recuperação, a pergunta é analisada para identificar filtros por metadados.

Entre os filtros suportados estão:

- estado;
- módulo;
- tipo documental;
- prioridade;
- status;
- cliente.

Os filtros identificados são validados antes da execução da recuperação.

Durante a Etapa 4, foi identificado um problema relacionado à interpretação da expressão `foram abertos`.

A expressão estava sendo interpretada como se representasse obrigatoriamente o status atual `Aberto`. A lógica foi corrigida para distinguir uma ação histórica de uma solicitação explícita de filtro pelo status atual.

Após a correção, a consulta relacionada aos tickets de Minas Gerais no módulo de estoque recuperou, entre seus resultados, os tickets esperados:

- `TCK-1001`
- `TCK-1002`
- `TCK-1004`

---

## Geração Estruturada

A geração das respostas utiliza um LLM integrado ao pipeline RAG.

A saída é validada por meio de um modelo Pydantic.

A resposta estruturada contém informações como:

- resposta;
- nível de confiança;
- evidências utilizadas;
- indicação de recusa;
- motivo da recusa.

As evidências mantêm referência ao arquivo de origem e ao respectivo `chunk_id`, permitindo rastrear as informações utilizadas pelo modelo.

---

## Guardrails e LGPD

O sistema possui mecanismos de proteção para evitar exposição de informações restritas ou inadequadas.

Entre os casos tratados estão:

- salários;
- credenciais;
- CPF;
- PIX;
- dados bancários;
- informações de saúde;
- perguntas sem evidência suficiente;
- solicitações incompatíveis com a base de conhecimento.

Quando uma pergunta não pode ser atendida de forma segura, o sistema retorna uma recusa estruturada.

### Exemplo de proteção de informação restrita

**Pergunta:** `Qual é o salário da Ana?`

O sistema recusa a solicitação, retornando `is_refusal = true`, `refusal_reason = lgpd` e `confidence_level = recusado`.

Nenhuma informação salarial é apresentada ao usuário.

### Exemplo de pergunta sem evidência

**Pergunta:** `Qual é a capital da França?`

Como a base VendeFácil não contém evidências capazes de responder à pergunta, o sistema retorna `is_refusal = true`, `refusal_reason = sem_evidencia` e `confidence_level = recusado`.

A interface apresenta ao usuário a mensagem: **Não encontrei informações confiáveis na base da VendeFácil para responder a essa pergunta.**

---

## Estrutura do Projeto

Estrutura principal do repositório:

    .
    ├── ACOMPANHAMENTO.md
    ├── README.md
    ├── RELATORIO.md
    ├── requirements.txt
    ├── benchmark/
    │   └── questions_and_ground_truth.json
    ├── data/
    │   ├── structured/
    │   ├── semi_structured/
    │   └── unstructured/
    ├── src/
    │   ├── ingest.py
    │   ├── ingest_structured.py
    │   ├── ingest_unstructured.py
    │   ├── build_index.py
    │   ├── load_index.py
    │   ├── query_analyzer.py
    │   ├── retrieve.py
    │   ├── generate.py
    │   ├── schema.py
    │   ├── guardrails.py
    │   ├── sanity_check.py
    │   ├── compare_search.py
    │   ├── compare_retrievers.py
    │   └── find_dense_case.py
    ├── eval/
    │   ├── run_benchmark.py
    │   ├── judge.py
    │   └── judge_prompt.py
    └── app/
        ├── app.py
        └── streamlit_app.py

---

## Instalação

### 1. Clonar o repositório

    git clone <URL_DO_REPOSITORIO>
    cd rag-vendefacil-18-ribeiro-ramos

### 2. Criar ambiente virtual

Linux/macOS:

    python3 -m venv .venv
    source .venv/bin/activate

Windows:

    python -m venv .venv
    .venv\Scripts\activate

### 3. Instalar dependências

    pip install -r requirements.txt

---

## Variáveis de Ambiente

As chaves de API não devem ser versionadas no Git.

A chave utilizada pelo pipeline de geração deve ser fornecida por variável de ambiente:

    GROQ_API_KEY=

Nunca devem ser enviados ao repositório:

- chave Groq;
- token GitHub;
- chave utilizada pelo LLM-as-judge;
- arquivo `.env` contendo credenciais;
- qualquer outro segredo utilizado pelo projeto.

---

## Construção do Índice FAISS

O índice vetorial é criado localmente e não precisa ser versionado.

Para construir o índice:

    python src/build_index.py

O pipeline processa os documentos e salva o índice FAISS localmente na estrutura configurada pelo projeto.

---

## Teste de Sanidade

Após a construção do índice, é possível executar:

    python src/sanity_check.py

O teste permite verificar o carregamento do índice e a recuperação de documentos.

---

## Executando a Interface Streamlit

A interface de demonstração está localizada em `app/streamlit_app.py`.

Execute:

    streamlit run app/streamlit_app.py

A interface permite:

- realizar perguntas em linguagem natural;
- visualizar respostas;
- verificar o nível de confiança;
- consultar evidências;
- identificar arquivo de origem;
- visualizar `chunk_id`;
- observar recusas;
- consultar o motivo da recusa;
- visualizar detalhes técnicos da resposta estruturada.

---

## Exemplos para Demonstração

### Consulta baseada na Knowledge Base

**Pergunta:** `Quais são os produtos oferecidos pela VendeFácil?`

Durante os testes, o sistema respondeu utilizando informações recuperadas de `data/structured/products.json` e apresentou os respectivos `chunk_id` como evidências.

### Proteção de informação restrita

**Pergunta:** `Qual é o salário da Ana?`

O sistema recusa a solicitação por envolver informação restrita.

### Pergunta sem evidência

**Pergunta:** `Qual é a capital da França?`

O sistema recusa a resposta por não possuir evidência adequada na base VendeFácil.

---

## Benchmark

O benchmark oficial está localizado em `benchmark/questions_and_ground_truth.json`.

A execução é realizada pelo script:

    python eval/run_benchmark.py

---

## RAG Triad

A avaliação da Etapa 4 considera três dimensões principais.

### Context Relevance

Avalia se o contexto recuperado é relevante para responder à pergunta.

### Answer Relevance

Avalia se a resposta gerada responde adequadamente à pergunta realizada.

A métrica é avaliada por LLM-as-judge.

### Groundedness

Avalia se as afirmações presentes na resposta são sustentadas pelas evidências recuperadas.

Também é avaliada por LLM-as-judge.

---

## Observação sobre o Benchmark Oficial

Durante a adaptação do benchmark foi identificada uma divergência entre a orientação da atividade e o arquivo disponibilizado.

A orientação menciona a execução de **20 perguntas**. Entretanto, o arquivo `benchmark/questions_and_ground_truth.json` contém **24 questões**, identificadas de `Q01` a `Q24`.

Além disso, o arquivo contém os campos:

- `expected_sources`;
- `expected_metadata`;
- `ground_truth_answer`;
- `key_points_for_evaluation`.

Porém, não fornece explicitamente `expected_chunk_ids`.

Esse ponto é relevante porque a descrição da métrica Context Relevance menciona a comparação dos `chunk_id` recuperados com os `chunk_id` presentes no ground truth.

Enquanto essa interpretação não for confirmada, a correspondência entre fontes recuperadas e fontes esperadas é utilizada apenas como diagnóstico auxiliar e não é apresentada como substituição definitiva da avaliação por `chunk_id`.

---

## Critério de Pontuação

A pontuação prevista para cada pergunta considera:

- **0,5 ponto** — resposta correta ou recusa adequada;
- **0,3 ponto** — arquivo/chunk citado corretamente;
- **0,2 ponto** — coerência entre confiança e `is_refusal`.

A pontuação máxima é de **1,0 ponto por questão**.

---

## Relatório

Os resultados da avaliação são documentados em `RELATORIO.md`.

O relatório contempla:

- metodologia de avaliação;
- RAG Triad;
- resultados gerais;
- resultados por categoria;
- pontuação;
- análise dos principais casos de falha;
- diagnóstico das falhas;
- possíveis melhorias;
- análise do que poderia ser realizado com mais quatro horas.

A integração com o LLM-as-judge foi concluída e há resultados parciais preservados em `eval/results.json`. A execução integral do benchmark não foi concluída devido ao limite de uso da API Groq, portanto as métricas atualmente documentadas devem ser interpretadas como parciais.

---

## Acompanhamento

O desenvolvimento da dupla é registrado em `ACOMPANHAMENTO.md`.

O documento reúne os relatos das atividades realizadas ao longo do desafio, incluindo decisões técnicas, dificuldades encontradas, correções efetuadas, uso de IA generativa e alterações efetivamente testadas.

---

## Segurança e Versionamento

Não devem ser versionados:

- chaves de API;
- tokens pessoais;
- arquivos `.env` com credenciais;
- índice FAISS gerado localmente;
- arquivos temporários;
- arquivos temporários de execução não necessários ao projeto.

O arquivo `eval/results.json` é mantido no repositório como checkpoint documentado da avaliação, permitindo preservar os resultados já concluídos e retomar somente as questões pendentes.

Os dados originais fornecidos para a atividade devem permanecer inalterados.

---

## Status do Projeto

### Implementado

- ingestão heterogênea;
- processamento de CSV;
- processamento de JSON;
- processamento de JSONL;
- processamento de Markdown;
- processamento de PDF;
- processamento de TXT;
- chunking;
- metadados;
- embeddings;
- FAISS;
- Dense Retrieval;
- BM25;
- Reciprocal Rank Fusion;
- Query Analyzer;
- filtros por metadados;
- geração estruturada;
- validação Pydantic;
- evidências e citações;
- guardrails;
- proteção de informações restritas;
- tratamento de perguntas sem evidência;
- interface Streamlit;
- estrutura de execução do benchmark.

### Estado atual da avaliação

- LLM-as-judge integrado ao pipeline de avaliação;
- Answer Relevance implementado;
- Groundedness implementado;
- Context Relevance calculado utilizando `expected_sources` como proxy explicitamente identificado, pois o benchmark fornecido não contém `expected_chunk_ids`;
- `eval/results.json` utilizado como checkpoint da execução;
- métricas parciais consolidadas no `RELATORIO.md`;
- três casos de falha analisados e diagnosticados;
- interface Streamlit integrada ao pipeline real e testada;
- execução integral das 24 questões ainda pendente devido ao limite de tokens da API Groq.

Último estado consolidado antes da apresentação:

| Métrica | Resultado parcial |
|---|---:|
| Context Relevance | 0,6833 |
| Answer Relevance | 0,8750 |
| Groundedness | 0,5625 |
| Challenge Score médio | 0,6109 |

Esses valores são parciais e não representam a conclusão integral das 24 questões existentes no arquivo oficial.

---

## Autores

**Maria Eduarda Ribeiro da Silva**  
**Eridalgo Ramos da Silva**

Mini Desafio RAG — VendeFácil Knowledge Base
