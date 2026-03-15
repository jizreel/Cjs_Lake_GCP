# 2. Processamento — Bronze → Silver (RAIS microdados vínculos) no GCP

Este guia dá sequência ao documento **1. Ingestão** e cobre a etapa **Bronze → Silver** para a RAIS (`microdados_vinculos`), usando **BigQuery** como engine de transformação (mais simples para começar).

Objetivo:
- Ler a tabela Bronze no seu projeto (consulta “controlada”)
- Criar/atualizar uma tabela Silver com tratamento mínimo e rastreabilidade técnica

Escopo: execução no **Cloud Shell**.

---

## 1) Pré-requisitos

**Onde executar:** Cloud Shell

1.1) Projeto ativo:

```bash
gcloud config set project cjs-lake-dev-base
gcloud config list
```

1.2) Confirme que os datasets existem:

```bash
bq ls --project_id cjs-lake-dev-base
bq ls --project_id cjs-lake-dev-base bronze_dev
bq ls --project_id cjs-lake-dev-base silver_dev
```

1.3) Confirme que a tabela Bronze existe (gerada na etapa 1):

```bash
bq show --project_id cjs-lake-dev-base bronze_dev.rais_microdados_vinculos_raw
```

---

## 2) Instalar dependência do job (se ainda não instalou)

**Onde executar:** Cloud Shell

```bash
pip3 install --user google-cloud-bigquery
```

---

## 3) Executar o job Bronze → Silver

**Onde executar:** Cloud Shell, na raiz do repositório  
**Arquivo do job:** `jobs/processing/bronze_to_silver.py`

3.1) Entre no repositório:

```bash
cd cjs_lake_gcp_base
```

3.2) Execute um recorte pequeno primeiro (recomendado):

```bash
python3 jobs/processing/bronze_to_silver.py --env dev --where "ano=2022"
```

Observações:
- O `--where` deve usar uma coluna que exista na Bronze. Se você não tiver certeza do nome, rode:

```bash
bq query --use_legacy_sql=false "
SELECT *
FROM \`cjs-lake-dev-base.bronze_dev.rais_microdados_vinculos_raw\`
LIMIT 10
"
```

3.3) Opções úteis do job:

- Deduplicar por linha inteira (pode custar mais):

```bash
python3 jobs/processing/bronze_to_silver.py --env dev --where "ano=2022" --dedupe
```

- Adicionar `processed_ts` como coluna técnica:

```bash
python3 jobs/processing/bronze_to_silver.py --env dev --where "ano=2022" --add-processed-ts
```

---

## 4) Validar o resultado

**Onde executar:** Cloud Shell

4.1) Verifique que a tabela Silver foi criada:

```bash
bq ls --project_id cjs-lake-dev-base silver_dev
bq show --project_id cjs-lake-dev-base silver_dev.rais_microdados_vinculos_tratado
```

4.2) Verifique contagem:

```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) AS qtd
FROM \`cjs-lake-dev-base.silver_dev.rais_microdados_vinculos_tratado\`
"
```

4.3) Valide uma amostra:

```bash
bq query --use_legacy_sql=false "
SELECT *
FROM \`cjs-lake-dev-base.silver_dev.rais_microdados_vinculos_tratado\`
LIMIT 10
"
```

---

## 5) Troubleshooting rápido

### 5.1) Erro: “Not found: Dataset silver_dev”

Solução:
- Confirme que o Terraform criou `silver_dev`.
- Rode `bq ls --project_id cjs-lake-dev-base` e valide o nome.

### 5.2) Erro: coluna no `--where` não existe

Solução:
- Rode o `LIMIT 10` na Bronze e ajuste o filtro para uma coluna existente.

### 5.3) Erro: custo/tempo alto

Solução:
- Use um `--where` mais restritivo (um único ano/recorte menor).
- Evite `--dedupe` no início.

