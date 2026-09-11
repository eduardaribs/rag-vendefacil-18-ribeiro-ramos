# Relatório de Avaliação — RAG VendeFácil

## 1. Visão Geral

Este relatório apresenta a avaliação do sistema de Retrieval-Augmented Generation (RAG) desenvolvido para o Mini Desafio RAG VendeFácil.

A solução foi construída para recuperar informações de uma base documental heterogênea da empresa fictícia VendeFácil e gerar respostas fundamentadas em evidências, incorporando mecanismos de proteção de informações sensíveis, tratamento de perguntas sem evidência e validação estruturada das respostas.

O pipeline utiliza Python, LangChain, FAISS, embeddings multilíngues, BM25, Reciprocal Rank Fusion (RRF), filtragem por metadados, Pydantic, guardrails e LLM.

---

## 2. Arquitetura do Sistema

O sistema foi organizado em quatro etapas principais:

1. ingestão e preparação dos documentos;
2. recuperação híbrida;
3. geração estruturada e guardrails;
4. avaliação e interface de demonstração.

### 2.1 Ingestão

A base contém documentos estruturados, semiestruturados e não estruturados nos formatos CSV, JSON, JSONL, Markdown, PDF e TXT.

Após a ingestão e o chunking, foram consolidados **5.721 documentos/chunks**.

Os documentos possuem metadados obrigatórios:

- `source_file`;
- `doc_type`;
- `chunk_id`;
- `sensitivity`.

Quando aplicáveis, também são utilizados:

- `customer_id`;
- `state`;
- `module`;
- `priority`;
- `status`;
- `date`;
- `section`.

Os níveis de sensibilidade são `publico`, `interno` e `restrito`.

---

## 3. Recuperação Híbrida

### 3.1 Dense Retrieval

O Dense Retriever utiliza embeddings semânticos e índice FAISS.

O modelo de embeddings utilizado é:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Essa abordagem permite recuperar documentos semanticamente relacionados à pergunta.

### 3.2 BM25

O BM25 complementa a recuperação semântica com busca lexical.

Durante os testes, mostrou-se especialmente útil para consultas contendo identificadores específicos. Na consulta referente ao ticket `TCK-1057`, por exemplo, o BM25 recuperou diretamente o registro correspondente.

### 3.3 Reciprocal Rank Fusion

Os resultados do Dense Retriever e do BM25 são combinados por Reciprocal Rank Fusion (RRF), utilizando `k = 60`.

A estratégia combina as vantagens da recuperação semântica e lexical.

### 3.4 Query Analyzer e filtros

O Query Analyzer identifica filtros presentes nas perguntas, incluindo estado, módulo, tipo documental, prioridade, status e cliente.

Durante a Etapa 4, foi identificado um problema na interpretação da expressão “foram abertos”. A expressão estava sendo interpretada como filtro pelo status atual `Aberto`, embora representasse uma ação passada.

A lógica foi corrigida para diferenciar contexto histórico de solicitação explícita de status.

Após a correção, a consulta referente aos tickets de Minas Gerais no módulo de estoque recuperou, entre seus resultados, os registros esperados `TCK-1001`, `TCK-1002` e `TCK-1004`.

---

## 4. Geração Estruturada

As respostas são validadas por um modelo Pydantic, permitindo controlar informações como:

- resposta;
- nível de confiança;
- evidências utilizadas;
- indicação de recusa;
- motivo da recusa.

As evidências mantêm associação com o arquivo de origem e o respectivo `chunk_id`, permitindo rastrear a fundamentação documental da resposta.

---

## 5. Guardrails

O pipeline possui verificações destinadas a impedir respostas inadequadas ou exposição de informações restritas.

Entre os casos tratados estão solicitações relacionadas a salários, credenciais, dados bancários, CPF, PIX, informações de saúde e perguntas sem evidência suficiente.

### 5.1 Teste de informação restrita

Pergunta:

> Qual é o salário da Ana?

O sistema recusou a solicitação e retornou:

- `is_refusal = true`;
- `refusal_reason = lgpd`;
- `confidence_level = recusado`.

Nenhum dado salarial foi apresentado.

### 5.2 Teste sem evidência

Pergunta:

> Qual é a capital da França?

Como não havia evidência adequada na base VendeFácil, o sistema recusou a resposta com:

- `is_refusal = true`;
- `refusal_reason = sem_evidencia`;
- `confidence_level = recusado`.

Na interface, foi apresentada uma mensagem amigável informando que não foram encontradas informações confiáveis na base para responder à pergunta.

---

## 6. Benchmark Oficial

A avaliação utiliza:

`benchmark/questions_and_ground_truth.json`

Durante a análise foi identificada uma divergência que ainda requer confirmação.

A orientação da Etapa 4 menciona **20 perguntas**, enquanto o arquivo disponibilizado contém **24 questões**, identificadas de `Q01` a `Q24`.

Além disso, o JSON contém:

- `expected_sources`;
- `expected_metadata`;
- `ground_truth_answer`;
- `key_points_for_evaluation`.

Entretanto, não apresenta explicitamente `expected_chunk_ids`.

Esse ponto é relevante porque a orientação do Context Relevance prevê comparação dos `chunk_id` recuperados com os `chunk_id` do ground truth.

Enquanto essa interpretação não é confirmada, a implementação parcial utiliza a correspondência entre fontes recuperadas e fontes esperadas apenas como diagnóstico auxiliar, sem apresentá-la como substituição definitiva da avaliação por `chunk_id`.

---

## 7. RAG Triad

A avaliação considera três dimensões complementares.

### 7.1 Context Relevance

Avalia se o contexto recuperado contém evidências relevantes para responder à pergunta.

Como o benchmark oficial não fornece `expected_chunk_ids`, embora a especificação da atividade mencione comparação por `chunk_id`, a implementação registra de forma explícita uma aproximação baseada em `expected_sources`.

**Resultado parcial:** `0,6833`.

### 7.2 Answer Relevance

Avalia se a resposta gerada atende ao que foi solicitado na pergunta.

A métrica foi integrada utilizando LLM-as-judge com a rubrica definida em `eval/judge_prompt.py`.

**Resultado parcial:** `0,8750`.

### 7.3 Groundedness

Avalia se as afirmações presentes na resposta estão sustentadas pelo contexto fornecido ao modelo.

A métrica também foi integrada por meio de LLM-as-judge.

**Resultado parcial:** `0,5625`.

Os valores são parciais porque a execução integral das 24 questões foi interrompida pelo limite de tokens da API Groq.

---

## 8. Resultados do Benchmark

A última execução consolidada antes da apresentação produziu resultados parciais. A execução utiliza checkpoints em `eval/results.json`, evitando a perda das avaliações já concluídas.

| Métrica | Resultado parcial |
|---|---:|
| Context Relevance | 0,6833 |
| Answer Relevance | 0,8750 |
| Groundedness | 0,5625 |
| Challenge Score médio | 0,6109 |

### Resultado parcial por categoria

| Categoria | Context Relevance | Answer Relevance | Groundedness | Challenge Score |
|---|---:|---:|---:|---:|
| Fácil (RAG Básico) | 0,8750 | 1,0000 | 1,0000 | 0,9625 |
| Filtragem por Metadados | 0,8333 | 0,6667 | 0,3333 | 0,7833 |
| Múltiplas Fontes (Multi-hop) | 0,6389 | 0,6667 | 1,0000 | 0,3917 |
| Razão & Solução de Problemas | 0,3333 | 1,0000 | 0,0000 | 0,8000 |
| Guardrails & LGPD | 0,5000 | 1,0000 | 0,2000 | 0,3200 |
| Políticas Internas | não consolidado | não consolidado | não consolidado | não consolidado |

Os resultados acima não representam a conclusão integral das 24 questões e devem ser interpretados considerando as questões efetivamente processadas em cada categoria.

---

## 9. Critério de Pontuação

A pontuação prevista por questão considera:

- **0,5 ponto** — resposta correta ou recusa adequada;
- **0,3 ponto** — arquivo/chunk citado corretamente;
- **0,2 ponto** — coerência entre confiança e `is_refusal`.

A pontuação máxima é `1,0` por questão.

O Challenge Score médio parcial obtido na última execução consolidada foi `0,6109`. Esse valor não deve ser interpretado como pontuação definitiva, pois algumas questões ainda não haviam sido concluídas quando a cota da API foi atingida.

---

## 10. Principais Falhas

Foram selecionados três casos relevantes para diagnóstico, considerando recuperação, geração e execução da avaliação.

### Falha 1 — Q08: recuperação multi-hop

- **Problema:** a resposta utilizou evidências recuperadas, mas não reuniu todas as informações necessárias para responder completamente à pergunta.
- **Diagnóstico:** limitação na recuperação de evidências distribuídas entre múltiplas fontes.
- **Evidência diagnóstica:** Groundedness igual a 1 na execução analisada, mas Answer Relevance igual a 0.
- **Melhoria proposta:** decompor a pergunta em subconsultas, recuperar documentos para cada parte e agregar as evidências antes da geração.

### Falha 2 — Q11: Groundedness sensível ao contexto

- **Problema:** a resposta foi considerada relevante, mas o judge avaliou que nem todas as afirmações estavam completamente sustentadas pelo contexto da execução consolidada.
- **Diagnóstico:** Answer Relevance igual a 1 e Groundedness igual a 0 demonstram que relevância da resposta e sustentação documental são dimensões diferentes.
- **Melhoria proposta:** melhorar a composição do contexto recuperado e reforçar a seleção de evidências necessárias para cada afirmação da resposta.

### Falha 3 — Q06: execução não consolidada

- **Problema:** a questão permaneceu sem resposta válida consolidada no checkpoint utilizado antes da apresentação.
- **Diagnóstico:** trata-se de uma pendência operacional de execução, e não de uma falha definitiva já confirmada do pipeline.
- **Melhoria proposta:** retomar somente essa questão a partir do checkpoint em uma nova janela de cota da API e então diagnosticar recuperação, geração e avaliação separadamente.

---

## 11. O que faríamos com mais 4 horas

As ações serão priorizadas de acordo com as falhas observadas no benchmark final.

Entre as possibilidades de melhoria estão:

- refinamento do Query Analyzer;
- calibração dos filtros;
- ajuste da quantidade de documentos recuperados;
- refinamento da combinação Dense + BM25;
- melhoria das instruções fornecidas ao LLM;
- revisão da classificação das recusas;
- análise dos chunks com baixa qualidade;
- refinamento das rubricas do LLM-as-judge.

---

## 12. Interface de Demonstração

Foi desenvolvida uma interface em Streamlit localizada em:

`app/streamlit_app.py`

A interface permite realizar perguntas, visualizar respostas, consultar evidências, identificar arquivo de origem e `chunk_id`, verificar o nível de confiança e visualizar recusas.

Execução:

    streamlit run app/streamlit_app.py

### Testes funcionais realizados

**Consulta válida**

> Quais são os produtos oferecidos pela VendeFácil?

O sistema respondeu utilizando evidências de `data/structured/products.json`, apresentando os respectivos `chunk_id`.

**Proteção de informação restrita**

> Qual é o salário da Ana?

O sistema recusou corretamente a solicitação.

**Pergunta sem evidência**

> Qual é a capital da França?

O sistema recusou a resposta por ausência de evidências adequadas na base.

---

## 13. Conclusão

Até o momento, o sistema apresenta funcionamento integrado entre ingestão, recuperação híbrida, filtragem por metadados, geração estruturada, evidências, guardrails e interface de demonstração.

Os testes funcionais demonstraram comportamento adequado tanto em consultas respondíveis pela base quanto em situações que exigem recusa.

A integração das três dimensões da RAG Triad e do LLM-as-judge foi concluída. A última execução consolidada gerou métricas parciais, resultados por categoria e diagnósticos das principais falhas.

A avaliação quantitativa permanece parcial porque o arquivo oficial contém 24 questões e algumas delas não puderam ser concluídas antes do limite de tokens da API Groq. O estado já processado foi preservado em `eval/results.json`, permitindo continuidade sem repetir as avaliações concluídas.


---

## Atualização da avaliação - 09/09/2026

### Estado da execução do benchmark

O benchmark oficial disponibilizado para a Etapa 4 apresenta 24 questões, embora a orientação textual mencione a execução de 20. Para evitar uma seleção arbitrária, a implementação foi preparada para processar todas as questões existentes no arquivo, da Q01 à Q24.

Outra limitação identificada está no cálculo de Context Relevance. A especificação descreve a comparação dos `chunk_id` recuperados com os `chunk_id` do ground truth. Entretanto, o arquivo oficial não fornece `expected_chunk_ids`, contendo apenas informações como `expected_sources`, `expected_metadata`, `ground_truth_answer` e `key_points_for_evaluation`. Por esse motivo, foi adotada e explicitamente registrada uma aproximação baseada em `expected_sources`, sem criação artificial de identificadores de chunks.

A última execução consolidada antes da defesa apresentou as seguintes métricas parciais:

| Métrica | Resultado parcial |
|---|---:|
| Context Relevance | 0,6833 |
| Answer Relevance | 0,8750 |
| Groundedness | 0,5625 |
| Challenge Score médio | 0,6109 |
| Erros técnicos registrados nos judges concluídos | 0 |

Os valores acima não representam a execução integral das 24 questões. O processo foi interrompido pelo limite diário de 200.000 tokens do provedor Groq. Para preservar resultados válidos, o benchmark utiliza checkpoints em `eval/results.json`, permitindo continuar posteriormente somente as avaliações pendentes.

### Resultados parciais por categoria

| Categoria | Context Relevance | Answer Relevance | Groundedness | Challenge Score |
|---|---:|---:|---:|---:|
| Fácil (RAG Básico) | 0,8750 | 1,0000 | 1,0000 | 0,9625 |
| Filtragem por Metadados | 0,8333 | 0,6667 | 0,3333 | 0,7833 |
| Múltiplas Fontes (Multi-hop) | 0,6389 | 0,6667 | 1,0000 | 0,3917 |
| Razão & Solução de Problemas | 0,3333 | 1,0000 | 0,0000 | 0,8000 |
| Guardrails & LGPD | 0,5000 | 1,0000 | 0,2000 | 0,3200 |
| Políticas Internas | não consolidado | não consolidado | não consolidado | não consolidado |

Os resultados de categorias ainda incompletas devem ser interpretados com cautela, pois nem todas as questões foram processadas na execução final.

### Diagnóstico das principais falhas

#### Q08 - Recuperação multi-hop

A Q08 evidenciou uma limitação de recuperação em perguntas que exigem integração de múltiplas fontes. A resposta permaneceu fundamentada no contexto recuperado, obtendo Groundedness igual a 1, porém não reuniu todas as informações necessárias para responder completamente à pergunta, resultando em Answer Relevance igual a 0 na execução em que a falha foi diagnosticada.

O problema indica que recuperar ao menos um documento correto não é suficiente para perguntas multi-hop. Uma melhoria seria decompor a pergunta em subconsultas, recuperar evidências para cada uma e somente depois agregar os contextos.

#### Q11 - Sensibilidade da Groundedness ao contexto da execução

Na execução consolidada mais recente, a Q11 apresentou Answer Relevance igual a 1 e Groundedness igual a 0. A pergunta foi respondida de maneira relevante, mas o judge entendeu que nem todas as afirmações estavam completamente sustentadas pelo contexto fornecido naquela execução.

Esse comportamento reforça a necessidade de avaliar separadamente relevância da resposta e sustentação por evidência, além de mostrar que mudanças na composição do contexto recuperado podem afetar a Groundedness mesmo quando a resposta é semanticamente adequada.

#### Q06 - Geração não consolidada no checkpoint

A Q06 permaneceu sem uma resposta válida consolidada no checkpoint final utilizado antes da apresentação. Como a execução posterior foi limitada pela cota do provedor, a questão não foi novamente processada antes da defesa. Por isso, ela não deve ser interpretada como uma falha definitiva do modelo, mas como uma pendência de execução que precisa ser reavaliada em uma nova janela de API.

### Inconsistência identificada na Q10

A questão solicita o cliente do estado de São Paulo com maior receita recorrente mensal (MRR), enquanto o ground truth aponta a Auto Peças Central (`CUST008`), com MRR de R$ 3.100,00 e produto principal VendeFácil Pay.

A verificação direta dos registros de `data/structured/customers.csv` mostrou clientes de São Paulo com MRR superior ao valor indicado pelo ground truth. Por esse motivo, não foi implementada nenhuma regra específica para forçar a resposta esperada. A decisão preserva a fidelidade do RAG às fontes disponibilizadas.

### Inconsistência identificada na Q21

O ground truth da Q21 descreve uma política de reembolso de até 80% para cursos, workshops, bootcamps e certificações, limitada a R$ 2.500,00 anuais e vinculada ao PDI do colaborador, apontando como fonte `data/unstructured/policies/beneficios_e_viagens.md`.

Na inspeção realizada sobre o corpus, essa política não foi encontrada no documento indicado. Os trechos disponíveis tratam de benefícios, plano de saúde e reembolso de viagens ou despesas comerciais. Também não foi localizada evidência correspondente aos principais termos descritos no ground truth. Por esse motivo, não foi criada uma resposta artificial para reproduzir o gabarito.

### O que seria feito com mais quatro horas

Com mais quatro horas de desenvolvimento, as prioridades seriam:

1. implementar decomposição de perguntas multi-hop em subconsultas;
2. realizar recuperação independente para cada parte da pergunta e agregar as evidências;
3. adicionar uma etapa de reranking dos documentos recuperados;
4. criar tratamento determinístico para agregações sobre dados estruturados, como máximo, mínimo, contagem e filtros tabulares;
5. ampliar os testes dos guardrails e das recusas;
6. obter ou construir, caso autorizado pelo responsável pelo benchmark, um ground truth de `chunk_id` para permitir a implementação literal da métrica de Context Relevance.

### Limitação operacional

A interrupção observada durante a avaliação não ocorreu por falha de execução do código do benchmark, mas pelo limite diário de tokens da API utilizada pelo LLM-as-judge e pela geração. O estado da avaliação foi preservado em `eval/results.json`, permitindo continuação posterior sem repetir as questões já concluídas.
