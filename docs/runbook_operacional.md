# Runbook Operacional do Projeto `cjs_lake_gcp_base`

## 1. Objetivo

Este runbook descreve a sequência operacional mínima para colocar o ambiente de desenvolvimento em funcionamento, com foco em:

- Git e GitHub
- Terraform
- GCP
- ingestão
- processamento
- BigQuery
- Superset

A ideia é responder sempre:

- o que executar
- onde executar
- em que ordem executar
- como validar

---

## 2. Premissas

Antes de começar, considere:

- projeto GCP já criado
- billing já vinculado
- Superset já existente
- ambiente local com Git instalado
- ambiente local com Python instalado
- ambiente local com Terraform instalado
- `gcloud` autenticado

Projeto de referência:

```text
cjs-lake-dev-base
```

Região sugerida:

```text
us-central1
```

---

## 3. Estrutura operacional por local de execução

## 3.1. Na máquina local / IDE

Executar localmente:

- edição de código
- versionamento Git
- Terraform
- criação de scripts Python
- criação de documentação

## 3.2. No GitHub

Manter:

- repositório central
- histórico de mudanças
- pipelines de CI/CD

## 3.3. No GCP

Executar recursos finais:

- buckets
- BigQuery
- Dataproc
- Superset

---

## 4. Etapa 1 - Criar e conectar o repositório Git

## 4.1. Onde executar

Na sua máquina local, no diretório raiz do projeto.

## 4.2. Comandos

```bash
git init
git branch -M main
git add .
git commit -m "chore: estrutura inicial do projeto lakehouse gcp"
```

Crie o repositório no GitHub e depois conecte o remoto:

```bash
git remote add origin https://github.com/SEU_USUARIO/cjs_lake_gcp_base.git
git push -u origin main
```

## 4.3. Validação

- repositório visível no GitHub
- branch `main` criada
- arquivos locais publicados

---

## 5. Etapa 2 - Preparar autenticação no GCP

## 5.1. Onde executar

Na máquina local ou no Cloud Shell.

## 5.2. Comandos

```bash
gcloud auth login
gcloud config set project cjs-lake-dev-base
gcloud auth application-default login
```

## 5.3. Validação

```bash
gcloud config list
```

Confirmar:

- projeto ativo correto
- conta autenticada correta

---

## 6. Etapa 3 - Criar service account de automação

## 6.1. Onde executar

Cloud Shell ou terminal com `gcloud` autenticado.

## 6.2. Comandos

```bash
gcloud iam service-accounts create sa-lake-dev \
  --display-name="Service Account Lake Dev"
```

Adicionar permissões mínimas iniciais:

```bash
gcloud projects add-iam-policy-binding cjs-lake-dev-base \
  --member="serviceAccount:sa-lake-dev@cjs-lake-dev-base.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding cjs-lake-dev-base \
  --member="serviceAccount:sa-lake-dev@cjs-lake-dev-base.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding cjs-lake-dev-base \
  --member="serviceAccount:sa-lake-dev@cjs-lake-dev-base.iam.gserviceaccount.com" \
  --role="roles/dataproc.editor"
```

## 6.3. Validação

```bash
gcloud iam service-accounts list
```

---

## 7. Etapa 4 - Ajustar arquivos de configuração do projeto

## 7.1. Onde editar

Na pasta local `conf/`.

## 7.2. Conteúdo sugerido para `conf/dev.yaml`

```yaml
project_id: cjs-lake-dev-base
region: us-central1
bucket_raw: cjs-lake-dev-base
bucket_staging: cjs-lake-dev-base-staging
bucket_artifacts: cjs-lake-dev-base-artifacts
bucket_logs: cjs-lake-dev-base-logs
dataset_bronze: bronze_dev
dataset_silver: silver_dev
dataset_gold: gold_dev
dataset_monitoring: monitoring_dev
```

## 7.3. Validação

- arquivo salvo em UTF-8
- nomes coerentes com o padrão do projeto

---

## 8. Etapa 5 - Criar a infraestrutura com Terraform

## 8.1. Onde editar

No projeto local, em `infra/modules/` e `infra/envs/dev/`.

## 8.2. O que criar agora

### 8.2.1. Criar módulo de BigQuery

Criar pasta:

```text
infra/modules/bigquery/
```

Criar arquivo `infra/modules/bigquery/main.tf` com:

```hcl
variable "project_id" {}
variable "location" {}
variable "datasets" {
  type = list(string)
}

resource "google_bigquery_dataset" "datasets" {
  for_each   = toset(var.datasets)
  project    = var.project_id
  dataset_id = each.value
  location   = var.location
}
```

### 8.2.2. Ajustar módulo de GCS

Arquivo `infra/modules/gcs/main.tf`:

```hcl
variable "project_id" {}
variable "location" {}
variable "bucket_names" {
  type = list(string)
}

resource "google_storage_bucket" "buckets" {
  for_each                    = toset(var.bucket_names)
  name                        = each.value
  location                    = var.location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = true
}
```

### 8.2.3. Criar ambiente `dev`

Arquivo `infra/envs/dev/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "cjs-lake-dev-base"
  region  = "us-central1"
}

module "gcs" {
  source     = "../../modules/gcs"
  project_id = "cjs-lake-dev-base"
  location   = "US"
  bucket_names = [
    "cjs-lake-dev-base",
    "cjs-lake-dev-base-staging",
    "cjs-lake-dev-base-artifacts",
    "cjs-lake-dev-base-logs"
  ]
}

module "bigquery" {
  source     = "../../modules/bigquery"
  project_id = "cjs-lake-dev-base"
  location   = "US"
  datasets = [
    "bronze_dev",
    "silver_dev",
    "gold_dev",
    "monitoring_dev"
  ]
}
```

## 8.3. Executar Terraform

### Onde executar

No terminal, dentro da pasta:

```text
infra/envs/dev
```

### Comandos

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## 8.4. Validação

### Buckets

```bash
gsutil ls -p cjs-lake-dev-base
```

### BigQuery

```bash
bq ls --project_id cjs-lake-dev-base
```

---

## 9. Etapa 6 - Criar o job de ingestão

## 9.1. Onde editar

Arquivo:

```text
jobs/ingestion/rais_bronze.py
```

## 9.2. Exemplo mínimo

```python
from google.cloud import storage
from pathlib import Path

PROJECT_ID = "cjs-lake-dev-base"
BUCKET_NAME = "cjs-lake-dev-base"
LOCAL_FILE = "./tmp/rais_exemplo.parquet"
DESTINATION_BLOB = "rais/ano=2024/mes=01/dia=15/rais_exemplo.parquet"


def upload_file() -> None:
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(DESTINATION_BLOB)
    blob.upload_from_filename(LOCAL_FILE)
    print(f"Arquivo enviado para gs://{BUCKET_NAME}/{DESTINATION_BLOB}")


if __name__ == "__main__":
    if not Path(LOCAL_FILE).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {LOCAL_FILE}")
    upload_file()
```

## 9.3. Instalar dependência local

```bash
pip install google-cloud-storage
```

## 9.4. Executar

No diretório raiz do projeto:

```bash
python jobs/ingestion/rais_bronze.py
```

## 9.5. Validar

```bash
gsutil ls gs://cjs-lake-dev-base/rais/ano=2024/mes=01/dia=15/
```

---

## 10. Etapa 7 - Criar o processamento Bronze -> Silver

## 10.1. Onde editar

Arquivo:

```text
jobs/processing/bronze_to_silver.py
```

## 10.2. Exemplo mínimo conceitual

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("bronze_to_silver").getOrCreate()

input_path = "gs://cjs-lake-dev-base/rais/ano=2024/mes=01/dia=15/*.parquet"

df = spark.read.parquet(input_path)

df_silver = (
    df.dropDuplicates()
)

(
    df_silver.write
    .format("bigquery")
    .option("table", "cjs-lake-dev-base.silver_dev.rais_vinculos_tratado")
    .mode("overwrite")
    .save()
)
```

## 10.3. Observação

Esse script é conceitual. Para execução real no Dataproc você vai empacotar dependências e submeter como job Spark.

---

## 11. Etapa 8 - Criar o processamento Silver -> Gold

## 11.1. Onde editar

Arquivo:

```text
jobs/processing/silver_to_gold.py
```

## 11.2. Exemplo com SQL no BigQuery

Você pode fazer essa etapa com Python chamando query no BigQuery ou com SQL salvo no repositório.

Exemplo de SQL:

```sql
CREATE OR REPLACE TABLE `cjs-lake-dev-base.gold_dev.rais_empregos_por_municipio_mes` AS
SELECT
  municipio,
  competencia,
  COUNT(*) AS qtd_vinculos
FROM `cjs-lake-dev-base.silver_dev.rais_vinculos_tratado`
GROUP BY municipio, competencia;
```

---

## 12. Etapa 9 - Conectar o Superset ao BigQuery

## 12.1. Premissa

O Superset já está rodando.

## 12.2. Configurar conexão

No Superset, criar uma conexão com o projeto do BigQuery e apontar o consumo para o dataset `gold_dev`.

## 12.3. Validar

- listar tabelas do dataset `gold_dev`
- criar dataset semântico
- montar gráfico simples

---

## 13. Etapa 10 - Versionar tudo

Depois de validar cada passo:

```bash
git add .
git commit -m "feat: provisiona base dev com gcs e bigquery"
git push
```

---

## 14. Check-list mínimo de validação do ambiente

## Infra

- [ ] buckets criados
- [ ] datasets criados
- [ ] service account criada
- [ ] permissões aplicadas

## Dados

- [ ] arquivo enviado ao GCS
- [ ] tabela Bronze criada
- [ ] tabela Silver criada
- [ ] tabela Gold criada

## Consumo

- [ ] Superset conectado
- [ ] dataset visível
- [ ] dashboard básico criado

---

## 15. Troubleshooting rápido

## Erro de autenticação no Terraform

Verificar:

```bash
gcloud auth application-default login
```

## Erro de permissão em bucket

Verificar IAM da service account.

## Erro no `bq ls`

Verificar projeto ativo:

```bash
gcloud config get-value project
```

## Job Spark não grava no BigQuery

Verificar:

- conector BigQuery
- permissões da service account
- nome completo da tabela

---

## 16. Próxima evolução recomendada

Depois de estabilizar `dev`:

1. parametrizar Terraform com variáveis
2. criar `terraform.tfvars` por ambiente
3. criar GitHub Actions para `plan` e `apply`
4. adicionar testes de qualidade de dados
5. formalizar promoção para `hml` e `prd`
