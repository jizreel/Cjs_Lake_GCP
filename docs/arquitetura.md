# Arquitetura do Projeto `cjs_lake_gcp_base`

## 1. Objetivo

Este projeto foi estruturado para estudar e evoluir um ambiente de dados no GCP com uma abordagem próxima do mundo corporativo, mas com foco em simplicidade operacional para ambiente de desenvolvimento.

A arquitetura recomendada para este momento é:

```text
Fonte de dados
  -> Ingestão (Python)
  -> Cloud Storage (RAW / Bronze físico)
  -> Dataproc (Spark)
  -> BigQuery (Bronze lógico / Silver / Gold)
  -> Superset
```

O objetivo é evitar, no ambiente de estudo, a complexidade operacional de manter um engine distribuído como o Trino em GKE, concentrando o esforço no desenho do ETL, no versionamento e na modelagem analítica.

---

## 2. Princípios da arquitetura

### 2.1. Tudo começa localmente

O desenvolvimento deve acontecer na sua máquina local ou IDE, onde você escreve:

- código Python
- arquivos Terraform
- scripts SQL
- documentação
- pipelines GitHub Actions

### 2.2. O repositório é a fonte da verdade

Mesmo que você tenha criado itens manualmente no GCP, a direção correta é fazer com que o repositório passe a ser o ponto central de controle.

Regra prática:

- **local**: desenvolvimento e testes iniciais
- **GitHub**: versionamento, histórico e automação
- **Terraform**: provisão de infraestrutura
- **GCP**: execução dos recursos

### 2.3. Separação por camadas

O projeto deve separar claramente:

- infraestrutura
- ingestão
- processamento
- SQL analítico
- documentação
- automação de deploy

---

## 3. Leitura da estrutura atual

A sua estrutura atual já está bem organizada, com diretórios para configuração, documentação, workflows, infraestrutura, jobs e SQL fileciteturn1file0.

### 3.1. `conf/`

Contém arquivos de configuração por ambiente.

Exemplo esperado:

- `dev.yaml`
- `hml.yaml`
- `prd.yaml`

Esses arquivos guardam parâmetros como:

- `project_id`
- `region`
- `bucket_raw`
- `bucket_staging`
- `dataset_bronze`
- `dataset_silver`
- `dataset_gold`

### 3.2. `docs/`

Contém a documentação viva do projeto.

Arquivos principais:

- `arquitetura.md`
- `modelo_medalhao.md`
- `runbook_operacional.md`

### 3.3. `github/workflows/`

Contém automações do GitHub Actions.

Exemplos:

- validação Terraform
- plan de Terraform
- apply em `dev`
- deploy de jobs Python
- promoção `hml` -> `prd`

### 3.4. `infra/`

Contém toda a infraestrutura como código.

#### `infra/modules/`

Módulos reutilizáveis, como:

- rede
- IAM
- buckets
- GKE
- metastore

#### `infra/envs/`

Composição por ambiente.

Cada ambiente consome módulos e define seus próprios valores.

### 3.5. `jobs/`

Contém os programas de ETL.

#### `jobs/ingestion/`

Responsável por trazer dado bruto para o lake.

Exemplo:

- `rais_bronze.py`

#### `jobs/processing/`

Responsável por transformar os dados.

Exemplos:

- `bronze_to_silver.py`
- `silver_to_gold.py`

### 3.6. `sql/`

Contém SQL de apoio ao ambiente analítico.

Como a recomendação atual é seguir com BigQuery em vez de Trino no ambiente de estudo, a evolução natural é substituir gradualmente a pasta `sql/trino` por algo como:

```text
sql/
  bigquery/
    bronze/
    silver/
    gold/
```

---

## 4. Arquitetura física recomendada no GCP

## 4.1. Projeto

Projeto já existente:

- `cjs-lake-dev-base`

Sugestão futura:

- `cjs-lake-dev-base`
- `cjs-lake-hml-base`
- `cjs-lake-prd-base`

Para estudo, pode começar só com `dev`.

## 4.2. Região

Padronizar uma região, por exemplo:

- `us-central1`

## 4.3. Cloud Storage

Buckets sugeridos para `dev`:

- `gs://cjs-lake-dev-base-raw`
- `gs://cjs-lake-dev-base-staging`
- `gs://cjs-lake-dev-base-artifacts`
- `gs://cjs-lake-dev-base-logs`

### Finalidade de cada bucket

#### `raw`

Recebe o dado como chegou da origem.

#### `staging`

Recebe arquivos temporários, resultados intermediários e saídas de processamento.

#### `artifacts`

Guarda artefatos de jobs, scripts versionados para execução e dependências.

#### `logs`

Guarda logs exportados ou material de apoio operacional.

## 4.4. BigQuery

Datasets sugeridos para `dev`:

- `bronze_dev`
- `silver_dev`
- `gold_dev`
- `monitoring_dev`

### Finalidade

#### `bronze_dev`

Dados brutos tipados com mínima intervenção.

#### `silver_dev`

Dados tratados, padronizados e prontos para integração.

#### `gold_dev`

Camada analítica para consumo por BI.

#### `monitoring_dev`

Tabelas de log, reconciliação e controles de qualidade.

## 4.5. Dataproc

Para estudo, priorize:

- jobs Spark sob demanda
- cluster pequeno apenas quando realmente necessário

Papel do Dataproc:

- leitura de arquivos do GCS
- tratamento e padronização
- escrita no BigQuery

## 4.6. Superset

Papel:

- consumir a camada `gold_dev`
- criar datasets semânticos
- montar dashboards

---

## 5. Fluxo ponta a ponta

## 5.1. Origem

Pode ser:

- Open Data
- API
- SAP HANA
- CSV local
- base pública do BigQuery

## 5.2. Ingestão

A ingestão deve:

- capturar os dados
- registrar data/hora da carga
- salvar o bruto no GCS
- preservar o formato original sempre que fizer sentido

Saída típica:

```text
gs://cjs-lake-dev-base-raw/rais/ano=2024/mes=01/dia=15/arquivo.parquet
```

## 5.3. Bronze

Nesta arquitetura, a Bronze pode ser entendida de duas formas:

- **bronze física**: arquivo bruto no GCS
- **bronze lógica**: tabela inicial no BigQuery

## 5.4. Silver

Nesta etapa você:

- corrige tipos
- trata nulos
- padroniza nomes de colunas
- remove duplicidade técnica
- cria chaves técnicas quando necessário

## 5.5. Gold

Nesta etapa você:

- cria fatos e dimensões
- monta visões analíticas
- gera agregações prontas para BI

## 5.6. Consumo

O Superset deve se conectar preferencialmente na camada `gold_dev`.

---

## 6. O que deve ser feito manualmente e o que deve virar código

## 6.1. Pode ser manual no início

Em ambiente de estudo, pode ser aceitável criar manualmente uma vez:

- projeto GCP
- billing
- service account inicial
- instalação inicial do Superset

## 6.2. Deve virar código o quanto antes

Tudo o que for recorrente ou reprodutível:

- buckets
- datasets BigQuery
- permissões IAM
- rede
- variáveis por ambiente
- jobs de ETL

---

## 7. Sequência correta de evolução

### Fase 1

Estruturar o repositório local e subir no GitHub.

### Fase 2

Provisionar com Terraform:

- buckets
- datasets
- service accounts
- permissões mínimas

### Fase 3

Criar o primeiro job de ingestão.

### Fase 4

Criar o primeiro job Spark de transformação Bronze -> Silver.

### Fase 5

Criar as tabelas Gold no BigQuery.

### Fase 6

Conectar Superset ao BigQuery.

### Fase 7

Adicionar automação via GitHub Actions.

---

## 8. Decisão arquitetural recomendada para o momento

Para o seu contexto atual, a decisão recomendada é:

- manter o Superset
- usar BigQuery como camada analítica
- usar Dataproc para processamento
- usar Cloud Storage como landing/raw
- adiar Trino para uma fase posterior

### Motivo

Essa escolha reduz drasticamente a complexidade operacional e mantém o foco no objetivo real de estudo:

- construir pipeline
- entender ambientes
- versionar infraestrutura
- modelar dados
- disponibilizar consumo analítico

---

## 9. Próximos passos imediatos

1. Ajustar a estrutura do projeto para BigQuery como destino analítico principal.
2. Criar os módulos Terraform mínimos.
3. Criar os arquivos `main.tf` do ambiente `dev`.
4. Provisonar buckets, datasets e IAM.
5. Criar o primeiro pipeline de ingestão.
6. Criar o primeiro pipeline de processamento.
7. Conectar o Superset.
