# 1. Ingestão — RAIS (`br_me_rais.microdados_vinculos`) no GCP

Este guia descreve o sequenciamento de execução para iniciar a ingestão da tabela **`br_me_rais.microdados_vinculos`** (BigQuery público, normalmente no projeto **`basedosdados`**) para o seu lake no GCP, seguindo o modelo medalhão:

- **RAW (GCS)**: snapshot em Parquet para auditoria e replay
- **BRONZE (BigQuery)**: primeira tabela consultável no seu projeto (com metadados técnicos)

Escopo: execução no **Cloud Shell** (recomendado para quem está começando).

---

## 1) Validar que o destino existe (infra já aplicada)

**Onde executar:** Cloud Shell  
**Conceito:** antes de ingerir, confirme que buckets e datasets existem.

1.1) Defina o projeto ativo:

```bash
gcloud config set project cjs-lake-dev-base
gcloud config list
```

1.2) Valide buckets e datasets:

```bash
gsutil ls -p cjs-lake-dev-base
bq ls --project_id cjs-lake-dev-base
bq ls --project_id cjs-lake-dev-base bronze_dev
```

Resultado esperado:
- bucket RAW existe (ex.: `gs://cjs-lake-dev-base`)
- dataset `bronze_dev` existe

---

## 2) Habilitar APIs necessárias

**Onde executar:** Cloud Shell  
**Conceito:** o job e os recursos dependem das APIs do BigQuery e do Storage.

```bash
gcloud services enable \
  bigquery.googleapis.com \
  storage.googleapis.com
```

---

## 3) Permissões para exportar do BigQuery para o GCS (RAW)

**Onde executar:** Cloud Shell  
**Conceito:** o comando `EXPORT DATA` do BigQuery grava arquivos no seu bucket; para isso, uma service account precisa ter permissão no bucket.

### 3.1) Identificar o Project Number

```bash
gcloud projects describe cjs-lake-dev-base --format="value(projectNumber)"
```

Guarde o valor retornado (ex.: `1234567890`).

### 3.2) Conceder permissão no bucket para o BigQuery Service Agent (recomendado)

Use o project number para montar a service account:

- `service-<PROJECT_NUMBER>@gcp-sa-bigquery.iam.gserviceaccount.com`

Comando:

```bash
gsutil iam ch \
  serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-bigquery.iam.gserviceaccount.com:objectAdmin \
  gs://cjs-lake-dev-base
```

Validação rápida:

```bash
gsutil iam get gs://cjs-lake-dev-base | head
```

### 3.3) Caso você já tenha uma conta existente e veja erro (observação importante)

Em alguns ambientes, você pode identificar que a conta já existente usada para executar operações no GCP é:

- `902691764768-compute@developer.gserviceaccount.com`

Se você receber erro de permissão ao exportar para o bucket (por exemplo, acesso negado ao gravar no GCS), faça:

1) Verifique em **IAM → Contas de serviço** qual conta está sendo usada/precisa de permissão.  
2) Se a conta existente for a `902691764768-compute@developer.gserviceaccount.com`, aplique a permissão no bucket para ela:

```bash
gsutil iam ch \
  serviceAccount:902691764768-compute@developer.gserviceaccount.com:objectAdmin \
  gs://cjs-lake-dev-base
```

---

## 4) Preparar o repositório e dependências para rodar o job

**Onde executar:** Cloud Shell  
**Conceito:** o job é Python e usa o SDK do BigQuery.

4.1) Acesse o repositório:

```bash
cd cjs_lake_gcp_base
```

4.2) Confira o arquivo de configuração do ambiente:

- `conf/dev.yaml`

Campos mínimos esperados:
- `project_id` (seu projeto no GCP)
- `bucket_raw` (bucket RAW)
- `dataset_bronze` (dataset Bronze)

4.3) Instale a dependência:

```bash
pip3 install --user google-cloud-bigquery
```

---

## 5) Escolher um filtro pequeno para o primeiro teste

**Onde executar:** Cloud Shell (via `bq`) ou BigQuery Console  
**Conceito:** `microdados_vinculos` pode ser muito grande. Comece pequeno para reduzir custo/tempo.

5.1) Inspecione 10 registros e descubra uma coluna boa para filtro (ex.: ano):

```bash
bq query --use_legacy_sql=false "
SELECT *
FROM \`basedosdados.br_me_rais.microdados_vinculos\`
LIMIT 10
"
```

5.2) Defina um filtro para usar no job (exemplo):

- `ano=2022`

Ajuste o nome da coluna conforme o que aparecer no `LIMIT 10`.

---

## 6) Executar a ingestão (RAW + BRONZE)

**Onde executar:** Cloud Shell, na raiz do repositório  
**Conceito:** o job faz:

- export do BigQuery público para o seu bucket RAW (Parquet)
- criação/atualização de uma tabela Bronze no seu projeto

6.1) Execute com filtro (exemplo):

```bash
python3 jobs/ingestion/rais_bronze.py --env dev --where "ano=2022"
```

O job imprime:
- fonte (`basedosdados.br_me_rais.microdados_vinculos`)
- destino Bronze (ex.: `cjs-lake-dev-base.bronze_dev.rais_microdados_vinculos_raw`)
- `batch_id` da carga

6.2) Se quiser testar apenas Bronze (sem exportar para o GCS):

```bash
python3 jobs/ingestion/rais_bronze.py --env dev --where "ano=2022" --skip-export
```

---

## 7) Validar o resultado

**Onde executar:** Cloud Shell

### 7.1) Validar arquivos no RAW (GCS)

```bash
gsutil ls gs://cjs-lake-dev-base/rais/microdados_vinculos/
```

Procure o caminho do `batch_id=...` criado na execução.

### 7.2) Validar tabela Bronze (BigQuery)

```bash
bq ls --project_id cjs-lake-dev-base bronze_dev
```

Verificar contagem:

```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) AS qtd
FROM \`cjs-lake-dev-base.bronze_dev.rais_microdados_vinculos_raw\`
"
```

---

## 8) Troubleshooting rápido

### 8.1) Erro: permissão ao gravar no bucket durante `EXPORT DATA`

Solução:
- Refaça o passo **3** e garanta que a conta correta tem `objectAdmin` no bucket RAW.
- Se você já tem a conta `902691764768-compute@developer.gserviceaccount.com` e ela for a conta em uso, aplique permissão para ela (passo **3.3**).

### 8.2) Erro: “Not found: Dataset bronze_dev”

Solução:
- Revalide o passo **1**.
- Se necessário, confirme no Terraform que o dataset `bronze_dev` existe no projeto `cjs-lake-dev-base`.

### 8.3) Erro: custo/tempo muito alto

Solução:
- Use um `--where` mais restritivo (por exemplo, filtrar um ano específico ou outro campo de partição natural).

