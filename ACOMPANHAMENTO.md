
# Acompanhamento - Mini Desafio RAG VendeFácil

**Integrante 1:** Maria Eduarda Ribeiro da Silva - [@eduardaribs](https://github.com/eduardaribs)  
**Integrante 2:** Eridalgo Ramos da Silva - [@EridalgoRamos](https://github.com/EridalgoRamos)

**Repositório:** `rag-vendefacil-18-ribeiro-ramos`

---

## Como preencher

- Um bloco por encontro, em **ordem cronológica** - o encontro mais recente vai no **fim** do arquivo.
- O relato individual é escrito **pelo próprio integrante**, em primeira pessoa. Não escreva pelo colega.
- Escrever entre **17:30 e 17:40**. `commit` + `push` até as **18:00**, mesmo que o dia não tenha fechado.
- Mensagem de commit: `acompanhamento: AAAA-MM-DD`

**Um relato útil responde:** o que eu implementei, qual decisão técnica eu tomei e por quê, onde travei, e como (ou se) resolvi.

<details>
<summary>Exemplo de relato individual bom × ruim</summary>

❌ *"Trabalhei na parte de ingestão junto com meu colega. Avançamos bastante e conseguimos carregar os arquivos."*

✅ *"Implementei os loaders de CSV e JSONL em `src/ingest.py`. Decidi serializar cada linha do `customers.csv` como frase em linguagem natural em vez de manter o formato separado por vírgula, porque nos primeiros testes de similaridade os chunks CSV crus não recuperavam nada - o embedding não separa campo de valor. Travei ~40 min no `tickets.jsonl`: o `state` estava indo para o texto do chunk mas não para os metadados, então o filtro voltava vazio. Resolvi movendo a extração para antes da criação do `Document`. Usei o Claude para gerar o esqueleto do parser de JSONL; ajustei o schema de metadados na mão."*

</details>

---

## Encontro 1 - 2026-08-24

**Etapa:** 1 - Ingestão heterogênea, metadados e indexação vetorial

### Relato individual - Maria Eduarda Ribeiro da Silva

Neste encontro, fiquei responsável pela ingestão dos dados estruturados e semiestruturados nos formatos CSV, JSON e JSONL. Inicialmente, inspecionei os arquivos disponíveis no repositório para compreender sua estrutura, os campos existentes e definir a estratégia de transformação dos registros em documentos para o pipeline RAG.

Implementei o arquivo `src/ingest_structured.py`, adotando a estratégia de um registro por chunk para os dados tabulares e um ticket por chunk para o arquivo JSONL. Na serialização, transformei os registros em textos descritivos em linguagem natural, buscando preservar as informações relevantes para a recuperação por embeddings.

Também implementei e padronizei os metadados obrigatórios `source_file`, `doc_type`, `chunk_id` e `sensitivity`. Quando aplicável, acrescentei metadados específicos, como `customer_id`, `state`, `module`, `priority`, `status` e `date`. Para os registros de funcionários, defini `sensitivity` como `restrito`, considerando a presença de informações sensíveis, como dados de identificação e remuneração.

Após finalizar meu loader, integrei os documentos estruturados e semiestruturados aos documentos não estruturados implementados pelo meu colega por meio do `src/ingest.py`. O pipeline integrado resultou em 5.721 chunks. Em seguida, validei a presença dos metadados obrigatórios e verifiquei a unicidade dos `chunk_id`.

Durante o desenvolvimento, utilizei o ChatGPT como apoio para estruturar inicialmente os loaders, compreender erros encontrados durante a execução e revisar a integração. As sugestões foram analisadas e ajustadas de acordo com a estrutura real dos arquivos do repositório e com os requisitos definidos no desafio.

### Relato individual - Eridalgo Ramos da Silva

Neste encontro, fiquei responsável pela ingestão dos documentos não estruturados nos formatos Markdown, PDF e TXT. Inicialmente, inspecionei os arquivos disponíveis no repositório para compreender a estrutura e definir uma estratégia de chunking adequada para cada formato.

Implementei o arquivo `src/ingest_unstructured.py`. Para os documentos Markdown, utilizei a estrutura de títulos e seções como referência para preservar a organização do conteúdo, com divisão adicional para seções maiores. Para os arquivos PDF, utilizei a extração do conteúdo textual e divisão respeitando a estrutura dos textos. Nos arquivos TXT, tratei as mensagens de e-mail de forma separada antes da divisão por tamanho.

Também apliquei aos documentos os metadados padronizados do projeto, incluindo `source_file`, `doc_type`, `chunk_id` e `sensitivity`, além de outros campos quando aplicáveis. Após os testes individuais, minha implementação foi integrada ao loader dos dados estruturados e semiestruturados desenvolvido pela Eduarda.

Na integração dos dois loaders, o pipeline completo resultou em 5.721 chunks. Também revisamos a presença dos metadados obrigatórios e a identificação dos chunks antes de avançar para a etapa de indexação vetorial.

Utilizei o ChatGPT como apoio durante a organização e revisão da implementação. As sugestões foram verificadas e adaptadas de acordo com a estrutura real dos documentos e com as estratégias de chunking exigidas no desafio.

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**

- Realizamos a inspeção inicial dos arquivos disponibilizados no repositório e dividimos as responsabilidades de implementação entre os integrantes.
- Implementamos os loaders para os seis formatos previstos na Etapa 1: CSV, JSON, JSONL, Markdown, PDF e TXT.
- Para os dados estruturados e semiestruturados, implementamos a ingestão de CSV, JSON e JSONL, adotando um registro por chunk e um ticket por chunk, conforme a natureza de cada fonte.
- Para os documentos não estruturados, implementamos estratégias específicas de processamento e chunking para Markdown, PDF e TXT, buscando preservar seções, parágrafos e mensagens.
- Padronizamos os metadados obrigatórios `source_file`, `doc_type`, `chunk_id` e `sensitivity`, acrescentando metadados específicos quando aplicáveis.
- Integramos os loaders estruturados, semiestruturados e não estruturados em um único fluxo de ingestão.
- O pipeline integrado gerou 5.721 chunks.
- Realizamos testes para verificar a presença dos metadados obrigatórios e a unicidade dos identificadores dos chunks.
- Cada integrante realizou commits próprios referentes à parte desenvolvida.

**Ficou pendente:**

- Gerar os embeddings dos documentos processados.
- Construir e popular o índice vetorial utilizando FAISS.
- Persistir o índice em disco utilizando `save_local`.
- Implementar e testar a recarga do índice com `load_local`, sem realizar nova indexação.
- Criar o script de sanidade da Etapa 1, contendo o total de chunks, a distribuição por `doc_type` e os cinco chunks mais similares para três perguntas de teste.
- Revisar as dependências do projeto e atualizar o `requirements.txt` conforme necessário.

**Bloqueios em aberto:**

- Não permanecemos com bloqueios técnicos relacionados à ingestão ao final das atividades.
- Durante o desenvolvimento, encontramos dificuldades relacionadas à instalação de dependências no Google Colab e à autenticação do GitHub para realização do `push`, mas esses problemas foram identificados e solucionados.
- A indexação vetorial ainda não foi concluída e será retomada na continuidade da Etapa 1.

**Próximo passo (início do encontro 2):**

- Finalizar os itens ainda pendentes da Etapa 1 antes de avançar para a Etapa 2.
- Gerar os embeddings dos 5.721 chunks, construir e persistir o índice FAISS e verificar sua recarga sem reindexação.
- Executar o script de sanidade com três perguntas de teste e analisar os cinco resultados mais similares retornados para cada consulta.
- Após validar o critério de pronto da Etapa 1, iniciar a implementação da busca híbrida, do Query Analyzer e da filtragem por metadados previstos para a Etapa 2.

**Uso de assistentes de IA:**

- Utilizamos o ChatGPT como ferramenta de apoio durante o desenvolvimento, principalmente na organização inicial dos loaders, interpretação de erros apresentados no Google Colab, revisão da integração entre os módulos e orientação sobre comandos Git.
- As sugestões geradas pela IA foram revisadas e adaptadas de acordo com a estrutura real dos arquivos disponibilizados no repositório e com os requisitos técnicos definidos no guia do desafio.
- Também utilizamos a IA como apoio para revisar a padronização dos metadados e organizar os testes de validação do pipeline integrado.

---

## Atividade complementar - 2026-08-25

**Continuidade da Etapa:** 1 - Ingestão heterogênea, metadados e indexação vetorial

### Relato individual - Maria Eduarda Ribeiro da Silva

Na continuidade da Etapa 1, trabalhei na finalização dos itens que haviam ficado pendentes no encontro anterior. Após a integração e validação dos 5.721 chunks, implementei e testei a geração dos embeddings utilizando o modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

Em seguida, implementei a construção do índice vetorial com FAISS e sua persistência em disco por meio de `save_local()`. Durante os testes no Google Colab, foi necessário reinstalar dependências em novas sessões e reconstruir o índice localmente, pois a pasta `index/` foi corretamente configurada no `.gitignore` e, portanto, não é versionada no repositório.

Também participei da integração e validação dos scripts responsáveis pela recarga do índice e pelos testes de sanidade. Confirmamos o carregamento do índice utilizando `load_local()` sem necessidade de reindexar novamente os 5.721 documentos. O script de sanidade foi utilizado para verificar o total de chunks, a distribuição por `doc_type` e os resultados de consultas por similaridade.

Durante essa atividade, utilizei o ChatGPT como apoio para interpretar erros de dependências no Google Colab, revisar a configuração dos embeddings e do FAISS, compreender a persistência e recarga do índice e organizar os testes necessários para validar o critério de pronto da Etapa 1. As sugestões foram executadas, verificadas e adaptadas ao código real do projeto.

### Relato individual - Eridalgo Ramos da Silva

Na Etapa 1, atuei ativamente junto à equipe no pipeline de ingestão heterogênea e na estruturação do armazenamento vetorial. Colaborei diretamente na geração e validação dos embeddings utilizando o modelo sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 para processar os chunks textuais. 

Também participei da implementação da persistência do índice vetorial gerado pelo FAISS em disco (`save_local()`) e da validação do fluxo de recarga (`load_local()`), garantindo que a recuperação do índice ocorresse de forma eficiente sem a necessidade de reprocessar toda a base de 5.721 fragmentos a cada nova sessão no Google Colab. Além disso, auxiliei na construção e execução dos scripts de sanidade para auditar o volume total de dados, conferir a distribuição correta por tipo de documento (`doc_type`) e validar as primeiras consultas por similaridade. Durante o processo, utilizei ferramentas de IA como apoio na resolução de conflitos de dependências de pacotes e no ajuste fino da indexação local.

### Resumo da atividade (escrito em conjunto)

**Entregamos:**

- Finalizamos os itens que haviam ficado pendentes no Encontro 1.
- Geramos os embeddings dos 5.721 chunks processados pelo pipeline de ingestão.
- Construímos e populamos o índice vetorial utilizando FAISS.
- Persistimos o índice em disco utilizando `save_local()`.
- Implementamos e testamos a recarga do índice utilizando `load_local()`, sem necessidade de reindexação.
- Implementamos o script de sanidade da Etapa 1.
- Validamos o total de 5.721 chunks.
- Verificamos a distribuição dos documentos por `doc_type`.
- Executamos consultas de similaridade para verificar o funcionamento do índice.
- Revisamos as dependências necessárias para a execução do projeto.
- Mantivemos a pasta `index/`, o arquivo `.env`, `__pycache__/` e arquivos temporários fora do versionamento.
- Com a finalização dessas atividades, todos os itens do critério de pronto da Etapa 1 foram atendidos.

**Ficou pendente:**

- Nenhuma pendência técnica referente ao critério de pronto da Etapa 1.

**Bloqueios em aberto:**

- Nenhum bloqueio técnico referente à Etapa 1 permaneceu em aberto.
- Durante a execução ocorreram dificuldades pontuais relacionadas às dependências do Google Colab, persistência do ambiente entre sessões e autenticação do GitHub, mas os problemas foram solucionados.

**Próximo passo:**

- Iniciar a Etapa 2.
- Implementar o Query Analyzer.
- Implementar a busca híbrida Dense + BM25.
- Aplicar filtros estruturados de metadados.
- Implementar a fusão dos rankings utilizando RRF.

**Uso de assistentes de IA:**

- Utilizamos o ChatGPT como apoio na revisão da indexação vetorial, solução de erros de dependências no Google Colab, persistência e recarga do índice FAISS e organização dos testes de sanidade.
- As sugestões foram testadas e adaptadas conforme a implementação real do projeto e os critérios de pronto estabelecidos para a Etapa 1.

---

## Encontro 2 - 2026-08-26

**Etapa:** 2 - Busca híbrida e filtragem por metadados

### Relato individual - Maria Eduarda Ribeiro da Silva

Neste encontro, fiquei responsável principalmente pela implementação do Query Analyzer e pela lógica de extração, normalização e validação dos filtros de metadados utilizados na recuperação.

Implementei o arquivo `src/query_analyzer.py` utilizando uma abordagem baseada em regras. Essa estratégia foi escolhida porque os principais campos de filtragem possuem vocabulário estruturado e relativamente limitado, permitindo uma solução determinística, rápida e sem dependência de chamadas externas a um LLM.

Implementei a normalização das perguntas, incluindo conversão para minúsculas, remoção de acentos e tratamento de espaços, além de dicionários de sinônimos para estados, módulos, tipos de documento, prioridades e status. Com isso, consultas como `Minas Gerais` e `MG`, ou `pagamento` e `pay`, passaram a produzir os mesmos valores estruturados.

Durante os testes, identifiquei uma ambiguidade no reconhecimento de `doc_type`, pois perguntas como “tickets de clientes” poderiam ser interpretadas incorretamente como consultas ao tipo `customer`. Ajustei a lógica para considerar o objeto principal solicitado na pergunta e tratar `customer` somente quando o cliente for efetivamente o objeto consultado.

Também implementei a validação dos filtros extraídos contra os valores realmente existentes nos metadados da base. Durante essa etapa, identifiquei que valores normalizados como `Critica` eram semanticamente equivalentes a `Crítica`, mas o filtro utilizado posteriormente exigia correspondência com o valor canônico armazenado. A validação foi então ajustada para comparar os valores de forma normalizada e devolver exatamente o valor existente nos documentos.

Após a integração do Query Analyzer com a implementação de recuperação, participei da revisão e dos testes da busca híbrida Dense + BM25 e da fusão dos rankings utilizando Reciprocal Rank Fusion (RRF). Também testamos a aplicação de filtros na busca vetorial com `fetch_k=500` e a pré-filtragem dos documentos utilizados pelo BM25.

Nos comparativos com e sem filtro, verificamos que consultas sem restrições poderiam recuperar documentos semanticamente próximos, mas pertencentes a outros estados, módulos ou tipos, enquanto a aplicação dos metadados direcionava a recuperação para os documentos efetivamente compatíveis com a pergunta.

Também realizamos testes específicos para demonstrar a complementaridade dos recuperadores. Na consulta pelo identificador exato `TCK-1057`, o BM25 recuperou o ticket correto na primeira posição, enquanto a busca densa não o apresentou no Top 5. Em outro teste formulado como paráfrase semântica, a busca densa recuperou em primeiro lugar o documento esperado, enquanto o BM25 não o apresentou no Top 5.

Utilizei o ChatGPT como apoio na estruturação e revisão do Query Analyzer, investigação de inconsistências na normalização dos metadados, depuração da integração entre Dense, BM25 e RRF e elaboração dos testes comparativos. As sugestões foram verificadas por meio da execução do código e ajustadas conforme os resultados reais obtidos na base.

### Relato individual - Eridalgo Ramos da Silva

* **Atividade Complementar:** 
  - Desenvolvi e validei o motor de busca híbrida combinando busca densa (FAISS com embeddings multilinguais) e busca esparsa (BM25Okapi).
  - Implementei o algoritmo de Fusão de Classificação Recíproca (RRF) com parâmetro $k=60$ para unificar e reordenar os resultados de forma equilibrada.

* **Encontro 2:**
  - Integração bem-sucedida do motor de recuperação (`retrieve.py`) com o módulo `query_analyzer.py` desenvolvido pela colega, garantindo o suporte a filtros dinâmicos de metadados (`state`, `module`, `doc_type`) nas buscas.
  - Testes de sanidade e validação cruzada no ambiente do Google Colab simulando consultas reais da plataforma VendeFácil.


### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**

- Implementamos o Query Analyzer baseado em regras para interpretação das consultas.
- Implementamos a normalização das perguntas e o tratamento de sinônimos.
- Implementamos a extração dos filtros `state`, `module`, `doc_type`, `priority` e `status`.
- Validamos os filtros extraídos contra os valores realmente existentes nos metadados da base.
- Ajustamos a validação para devolver os valores canônicos presentes nos documentos, evitando incompatibilidades como `Critica` e `Crítica`.
- Implementamos a busca densa utilizando embeddings e FAISS.
- Implementamos a busca lexical utilizando BM25.
- Ajustamos a tokenização do BM25 para preservar identificadores e códigos, como `TCK-1057`, `PAY-200` e `PDV-500`.
- Implementamos a fusão dos rankings Dense e BM25 utilizando Reciprocal Rank Fusion (RRF), com `k=60`.
- Aplicamos os filtros de metadados à busca densa utilizando `fetch_k=500`.
- Implementamos a pré-filtragem dos documentos utilizados pelo BM25 quando existem filtros estruturados.
- Realizamos o comparativo entre buscas com e sem filtro para três perguntas específicas.
- Confirmamos que a aplicação dos filtros evita resultados de estados, módulos e tipos de documento incompatíveis com a consulta.
- Demonstramos um caso em que o BM25 foi superior para recuperação por identificador exato: o ticket `TCK-1057` foi recuperado na primeira posição pelo BM25 e não apareceu no Top 5 da busca densa.
- Demonstramos um caso em que a busca densa foi superior para uma consulta por paráfrase: o documento esperado foi recuperado na primeira posição pelo Dense e não apareceu no Top 5 do BM25.
- Testamos o comportamento da fusão RRF na combinação dos rankings.
- Atualizamos o `requirements.txt` com a dependência necessária para utilização do BM25.

**Ficou pendente:**

- Iniciar a Etapa 3, referente à síntese estruturada das respostas, citação de evidências e implementação dos guardrails de LGPD.

**Bloqueios em aberto:**

- Nenhum bloqueio técnico da Etapa 2 permanece em aberto.
- Durante o desenvolvimento foram identificadas inconsistências relacionadas à interpretação de `doc_type`, normalização da prioridade, tokenização de identificadores no BM25 e persistência do índice entre sessões do Google Colab. Esses pontos foram investigados e corrigidos durante os testes.

**Próximo passo (início do encontro 3):**

- Implementar os modelos Pydantic exigidos para `SourceEvidence` e `RAGResponse`.
- Implementar o validador de consistência entre `is_refusal`, `sources_used`, `confidence_level` e `refusal_reason`.
- Implementar a política de LGPD com os três comportamentos exigidos: recusar, mascarar e responder.
- Implementar o tratamento de perguntas fora de escopo.
- Integrar recuperação, evidências e geração da resposta estruturada.

**Uso de assistentes de IA:**

- Utilizamos o ChatGPT como ferramenta de apoio para revisar o Query Analyzer, interpretar erros encontrados durante a integração, corrigir inconsistências de metadados, aprimorar a tokenização utilizada pelo BM25 e estruturar os testes comparativos entre Dense, BM25 e RRF.
- A IA também foi utilizada como apoio na análise dos resultados das buscas com e sem filtros e na identificação de casos adequados para demonstrar as diferenças entre recuperação lexical e semântica.
- Todas as sugestões foram testadas e adaptadas conforme o comportamento real da base e os requisitos técnicos definidos no guia do desafio.

---

## Encontro 3 - 2026-08-28

**Etapa:** 3 - Síntese estruturada, evidência e guardrails de LGPD

### Relato individual - Maria Eduarda Ribeiro da Silva

Neste encontro, fiquei responsável principalmente pela implementação da geração estruturada de respostas da Etapa 3. Implementei os modelos `SourceEvidence` e `RAGResponse` utilizando Pydantic, conforme o schema definido no desafio, e acrescentei um validador de consistência para garantir a relação correta entre `is_refusal`, `sources_used`, `confidence_level` e `refusal_reason`.

Também implementei o fluxo de geração estruturada com LLM, utilizando o modelo `openai/gpt-oss-120b` por meio da Groq. Para garantir a rastreabilidade das respostas, desenvolvi a lógica de evidências contendo `filepath`, `chunk_id` e `quotation`, com validação para confirmar que cada citação corresponde literalmente a um trecho do chunk recuperado e respeita o limite definido no schema.

Implementei ainda o mecanismo de retry para situações em que a resposta gerada não atende às validações do Pydantic ou apresenta evidências inválidas. Nesse fluxo, o erro identificado é utilizado como feedback para uma nova tentativa de geração, evitando que falhas de validação sejam simplesmente ignoradas.

Durante os testes da geração estruturada, identifiquei também um problema no Query Analyzer da etapa anterior: consultas contendo identificadores como `CUST001` não estavam sendo filtradas corretamente. Ajustei a extração de `customer_id` e corrigi a interpretação indevida da palavra “para” como o estado do Pará, validando novamente consultas por cliente, ticket e log.

Na integração com a implementação de guardrails desenvolvida pelo Eridalgo, participei da revisão das regras e dos testes do pipeline completo. Identificamos que valores monetários operacionais estavam sendo mascarados genericamente, o que impediria respostas permitidas envolvendo valores como MRR e totais de vendas. A regra foi ajustada para manter esses valores disponíveis quando não representam remuneração individual ou outro dado restrito.

Após a integração, executei testes de recusa por LGPD, mascaramento, respostas permitidas, perguntas fora de escopo e respostas com evidências literais. Foram validadas recusas para solicitações de salário e PIX, mascaramento de e-mail e telefone e respostas permitidas relacionadas a tickets e operações da VendeFácil. Também confirmei que respostas não recusadas apresentam as fontes utilizadas e que recusas não apresentam evidências.

Utilizei o ChatGPT como apoio na implementação e revisão da geração estruturada, na análise dos erros encontrados durante os testes, na integração entre o Pydantic, o LLM, as evidências e os guardrails e na organização da bateria final de testes. As sugestões foram revisadas e adaptadas à implementação existente e validadas no Google Colab antes dos commits e do envio ao repositório.

### Relato individual - Eridalgo Ramos da Silva

* **Frente de Atuação:** Segurança, LGPD e Guardrails.
* **Entregas Realizadas:**
  - Desenvolvimento do módulo `src/guardrails.py` para atuar como barreira de proteção antes da geração com LLM.
  - Implementação da função `verificar_fora_de_escopo` para identificação e recusa imediata de temas alheios à VendeFácil.
  - Implementação da função `aplicar_guardrails_lgpd` cobrindo as 3 diretrizes: **Recusar, Mascarar e Responder**.
  - Definição de regras de **Recusa Estrita**: Bloqueio categorizado para credenciais/senhas, termos de saúde, salário/remuneração individual, dados bancários e qualquer menção ou identificação de CPF e chave PIX.
  - Definição de regras de **Mascaramento**: Anonimização de dados de contato (e-mails, telefones, endereços), cartões de crédito e valores monetários genéricos através de expressões regulares (Regex).
  - Execução e validação da bateria de testes unitários adversariais no arquivo `notebooks/testes_guardrails.ipynb`, atestando a robustez dos filtros.

    
### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**

- Implementamos os modelos Pydantic `SourceEvidence` e `RAGResponse` exigidos para a saída estruturada do pipeline.
- Implementamos o validador de consistência entre `is_refusal`, `sources_used`, `confidence_level` e `refusal_reason`.
- Implementamos a geração estruturada de respostas utilizando LLM.
- Implementamos a citação obrigatória das evidências utilizadas por meio de `filepath`, `chunk_id` e `quotation`.
- Validamos que as citações utilizadas correspondem literalmente aos chunks recuperados e respeitam o limite definido no schema.
- Implementamos mecanismo de retry para respostas que não atendem às validações estruturais ou apresentam evidências inválidas.
- Implementamos e revisamos os guardrails de LGPD para os comportamentos de recusa, mascaramento e resposta permitida.
- Implementamos o tratamento de perguntas fora do escopo da VendeFácil.
- Integramos os guardrails ao pipeline de recuperação e geração estruturada.
- Ajustamos as regras de tratamento de valores monetários para não mascarar valores operacionais permitidos, mantendo a proteção de informações individuais restritas.
- Ajustamos o Query Analyzer para reconhecer identificadores `customer_id` e corrigimos uma ambiguidade que interpretava a palavra “para” como o estado do Pará.
- Executamos testes de recusa para dados restritos, incluindo salário e PIX.
- Executamos testes de mascaramento de dados pessoais, incluindo e-mail e telefone.
- Executamos testes de consultas permitidas relacionadas aos tickets e às operações da VendeFácil.
- Executamos testes de perguntas fora de escopo.
- Validamos a presença de evidências nas respostas permitidas e a ausência de evidências nas respostas recusadas.
- Concluímos a integração da Etapa 3 e enviamos as implementações para a branch `main`.

**Ficou pendente:**

- Nenhuma pendência técnica referente ao critério principal de pronto da Etapa 3.

**Bloqueios em aberto:**

- Nenhum bloqueio técnico da Etapa 3 permanece em aberto.
- Durante o desenvolvimento, foram identificados ajustes relacionados ao tratamento de valores monetários, citações contendo dados mascaráveis e interpretação de filtros pelo Query Analyzer. Os problemas identificados foram tratados durante a implementação e os testes.

**Próximo passo (início do encontro 4):**

- Iniciar a Etapa 4.
- Construir o benchmark com 20 perguntas representativas.
- Implementar a avaliação do pipeline utilizando os critérios da RAG Triad.
- Desenvolver a interface de utilização do sistema.
- Consolidar os resultados e preparar o relatório final.
- Revisar o projeto para preparação do Demo Day.

**Uso de assistentes de IA:**

- Utilizamos o ChatGPT como ferramenta de apoio durante a Etapa 3, principalmente na revisão dos modelos Pydantic, integração da geração estruturada com os guardrails, interpretação de erros, revisão das regras de LGPD e elaboração dos testes.
- A IA também foi utilizada como apoio na investigação de problemas encontrados no Query Analyzer, na validação das evidências literais e na organização da bateria final de testes.
- As sugestões produzidas pela IA foram analisadas, adaptadas ao código existente e validadas por meio da execução no Google Colab antes de serem incorporadas ao projeto.

---

## Encontro 4 - 2026-08-31

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual - Maria Eduarda Ribeiro da Silva

Neste encontro, implementei o arquivo `eval/run_benchmark.py` e preparei a lógica de **Context Relevance** conforme a especificação da atividade, que previa a comparação entre os `chunk_id` recuperados e os `chunk_id` esperados no ground truth. Também validei o funcionamento da estrutura da métrica com testes isolados e confirmei o funcionamento da recuperação híbrida com o índice FAISS. Posteriormente, após a disponibilização e inspeção do benchmark oficial, constatamos que o arquivo fornecido não contém `expected_chunk_ids`; por isso, a implementação final passou a registrar explicitamente `expected_sources` como proxy, sem criar identificadores inexistentes.

Utilizei o ChatGPT como apoio na estruturação do benchmark, revisão da lógica do Context Relevance e resolução de problemas de ambiente e importação no Google Colab. As sugestões foram testadas antes do envio ao repositório.

A execução completa das 20 questões ainda ficou pendente porque o arquivo oficial `benchmark/questions_and_ground_truth.json` ainda não está disponível no repositório.

### Relato individual - Eridalgo Ramos da Silva

Neste encontro, cumpri as minhas atribuições iniciais da Etapa 4, seguindo a divisão de tarefas:

* **Implementar Answer Relevance com LLM-as-judge** e **Implementar Groundedness com LLM-as-judge**: Atualizei o arquivo `judge.py` para utilizar a SDK moderna `google-genai` com o modelo Gemini 3.6 Flash.
* **Testar o judge com respostas reais**: Validei o funcionamento do juiz no Colab, obtendo sucesso nos testes de cenários com respostas corretas, evasivas, fundamentadas e alucinadas.
* **Criar a interface em app/** e **Testar a interface**: Construí o arquivo `app/app.py` utilizando a biblioteca Gradio para gerar a interface visual do chatbot. Testei a aplicação gerando um link público e deixei uma função *mock* (simulada) preparada para receber o motor de recuperação.
* **Fazer commit e push da implementação dele**: Adicionei as dependências `google-genai` e `gradio` ao `requirements.txt` sem afetar o trabalho da colega e fiz o envio de toda a minha estrutura (juiz e interface) para as respectivas pastas no GitHub.
* **Escrever o relato individual dele no ACOMPANHAMENTO.md**: Relato atualizado. Fico no aguardo da finalização do pipeline de recuperação para iniciarmos a etapa de "Integrar as métricas do Eridalgo ao run_benchmark.py".

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
- Implementação inicial da estrutura de avaliação da Etapa 4.
- Implementação e teste do Context Relevance.
- Estrutura inicial do LLM-as-judge e da interface do chatbot.

**Ficou pendente:**
- Executar as 20 questões do benchmark oficial.
- Gerar o `results.json` final e consolidar as métricas da RAG Triad.
- Finalizar o relatório e os testes da interface integrada ao pipeline.

**Bloqueios em aberto:**
- O arquivo oficial `benchmark/questions_and_ground_truth.json` ainda não está disponível no repositório.

**Preparação para o Demo Day:**
- Estrutura inicial da interface criada.
- Benchmark e relatório final serão concluídos após a disponibilização das questões oficiais.

**Uso de assistentes de IA:**
- Utilizamos o ChatGPT como apoio na implementação, revisão do código e interpretação de erros durante os testes.

---

*TIC em Trilhas · PUC-Rio · Instituto ECOA · MCTI Futuro · Softex*

---

## 02/09/2026 - Maria Eduarda Ribeiro da Silva

### Relato individual

Hoje concentrei minhas atividades na continuidade da Etapa 4 do Mini Desafio RAG VendeFácil, especialmente na preparação do benchmark oficial, correções no pipeline e desenvolvimento da interface de demonstração.

Inicialmente, trabalhei na adaptação do arquivo `eval/run_benchmark.py` para a estrutura do benchmark oficial disponibilizado. Durante essa etapa, identifiquei que o arquivo contém 24 questões, de Q01 a Q24, embora a orientação da atividade mencione 20 perguntas. Também observei que o JSON disponibiliza campos como `expected_sources`, `expected_metadata`, `ground_truth_answer` e `key_points_for_evaluation`, mas não apresenta `expected_chunk_ids`, apesar de a descrição do Context Relevance mencionar comparação por `chunk_id`. Por esse motivo, mantive no código uma avaliação parcial baseada nas fontes esperadas, deixando explícito que esse resultado ainda não corresponde à métrica final por chunk.

Durante os testes do benchmark, identifiquei um problema no Query Analyzer na questão relacionada aos tickets de Minas Gerais. A expressão “foram abertos” estava sendo interpretada como se o usuário solicitasse apenas tickets com status atual “Aberto”. Corrigi a função responsável pela identificação de status para diferenciar uma ação histórica de uma solicitação de filtro por status atual. Após a correção, a consulta passou a recuperar corretamente os tickets esperados, incluindo TCK-1001, TCK-1002 e TCK-1004.

Também corrigi problemas de importação entre os módulos do projeto que surgiram durante a execução da aplicação fora do contexto original dos scripts. Padronizei as importações utilizadas pelo módulo de geração e ajustei os caminhos utilizados pela interface para permitir a execução adequada do pipeline completo.

Em seguida, desenvolvi e testei uma interface em Streamlit para demonstração do RAG, mantendo separada a interface em Gradio desenvolvida pelo meu colega. A interface Streamlit foi integrada à função `gerar_resposta()` e permite realizar perguntas, visualizar a resposta, consultar as evidências utilizadas e acessar detalhes técnicos da saída estruturada.

Foram realizados testes funcionais com três cenários diferentes. Em uma pergunta sobre os produtos oferecidos pela VendeFácil, o sistema retornou uma resposta fundamentada nos documentos recuperados, apresentando arquivos de origem e `chunk_id`. Em uma pergunta solicitando o salário de uma funcionária, o sistema recusou corretamente a resposta por envolver informação pessoal restrita. Também foi testada uma pergunta fora da base de conhecimento, sobre a capital da França, e o sistema recusou a resposta por ausência de evidências. Foi ajustada a interface para que recusas com campo `answer` vazio também apresentem uma mensagem compreensível ao usuário.

Utilizei IA generativa como apoio para análise dos erros apresentados durante os testes, revisão da organização dos imports, elaboração de trechos de código, identificação da causa do filtro incorreto e estruturação da interface. As sugestões foram verificadas por meio de execução no Colab, testes de compilação, testes de importação em processo limpo e testes funcionais do chatbot. Foram mantidas apenas as alterações que passaram nesses testes.

### Pendências identificadas

Ainda é necessário integrar a avaliação com o LLM-as-judge desenvolvida pelo meu colega para calcular Answer Relevance e Groundedness. Também permanece necessária a confirmação sobre a quantidade oficial de questões do benchmark e sobre a ausência de `expected_chunk_ids` para o cálculo final do Context Relevance.



---

## 09/09/2026 - Maria Eduarda Ribeiro da Silva

### Relato individual

Hoje concentrei minhas atividades na integração, validação e fechamento da Etapa 4 do Mini Desafio RAG VendeFácil. Retomei a execução do benchmark oficial e acompanhei individualmente as questões que ainda apresentavam falhas de geração, recuperação ou avaliação.

Durante os testes, identifiquei situações em que o problema não estava diretamente no modelo de linguagem, mas na recuperação ou na interpretação dos filtros. A partir desse diagnóstico, revisei o comportamento do Query Analyzer, da recuperação híbrida e dos guardrails. Também trabalhei na geração estruturada para garantir respostas validadas pelo Pydantic e citações literais de evidências.

Um dos ajustes realizados foi no tratamento de credenciais. O sistema precisava diferenciar uma solicitação indevida de senha ou chave secreta de uma simples menção procedimental, como a instrução documentada para que um operador insira a senha do supervisor. Mantive a recusa para pedidos ou exposição de credenciais reais, sem bloquear procedimentos legítimos presentes nos manuais.

Também participei da revisão do benchmark e identifiquei duas limitações importantes no material fornecido. A orientação menciona 20 questões, porém o arquivo oficial contém 24 questões, da Q01 à Q24. Além disso, o arquivo de ground truth não fornece `expected_chunk_ids`, embora a métrica de Context Relevance seja descrita com base na comparação de chunks. Por esse motivo, a implementação registra de forma explícita o uso de `expected_sources` como proxy, sem criar identificadores inexistentes.

Na Q10, verifiquei diretamente os dados de clientes e encontrei divergência entre o ground truth e o arquivo `customers.csv` em relação ao cliente de São Paulo com maior MRR. Optei por preservar a fidelidade aos dados em vez de criar uma regra específica para reproduzir artificialmente o gabarito. Também foi identificada inconsistência semelhante na Q21, cuja política descrita no ground truth não foi localizada no corpus fornecido.

A execução final do benchmark foi realizada utilizando LLM-as-judge para Answer Relevance e Groundedness. O processo foi afetado pelo limite diário de 200.000 tokens da API Groq. Para evitar perda de progresso, utilizei execução por checkpoint no `eval/results.json`, permitindo retomar somente questões e métricas pendentes. O último estado consolidado antes da apresentação apresentou Context Relevance de 0,6833, Answer Relevance de 0,8750, Groundedness de 0,5625 e challenge score médio de 0,6109. Esses valores são parciais, pois algumas questões não puderam ser concluídas devido ao limite da API.

Também revisei a preparação para a defesa técnica, incluindo arquitetura, recuperação híbrida, filtros, guardrails, saída estruturada, limitações encontradas e exemplos seguros para a demonstração ao vivo.

### Uso de IA

Utilizei IA como apoio para análise de erros, revisão de código, interpretação dos logs do benchmark, elaboração de testes de regressão e organização da documentação. As sugestões geradas foram avaliadas antes de serem aplicadas. Entre as alterações que partiram dessa análise estão o refinamento da geração estruturada, o tratamento de credenciais nos guardrails, a retomada segura do benchmark por checkpoint e a revisão das rubricas do LLM-as-judge.

### Pendências

A execução integral das 24 questões do benchmark permanece dependente da liberação da cota diária da API Groq. Caso haja extensão do prazo, pretendo retomar o benchmark a partir do checkpoint existente, sem refazer as questões já concluídas.
