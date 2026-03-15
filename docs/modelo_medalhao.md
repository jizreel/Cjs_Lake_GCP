# Modelo Medalhão para o Projeto `cjs_lake_gcp_base`

## 1. Visão geral

O modelo medalhão organiza os dados em camadas de maturidade para reduzir complexidade, melhorar rastreabilidade e facilitar o consumo analítico.

Neste projeto, o modelo medalhão será aplicado assim:

```text
RAW (GCS)
  -> Bronze (BigQuery)
  -> Silver (BigQuery)
  -> Gold (BigQuery)
```

A estrutura do projeto já prevê jobs de ingestão e processamento adequados para esse fluxo, com `rais_bronze.py`, `bronze_to_silver.py` e `silver_to_gold.py` fileciteturn1file0.

---

## 2. Objetivo de cada camada

## 2.1. RAW

### O que é

É a zona de aterrissagem do dado, preservando o conteúdo o mais próximo possível da origem.

### Onde fica

No Cloud Storage.

### Para quê serve

- auditoria
- replay de carga
- rastreabilidade
- recuperação de processamento

### Como deve ser gravado

Preferencialmente em pastas particionadas por origem e data de ingestão.

Exemplo:

```text
gs://cjs-lake-dev-base/rais/ano=2024/mes=01/dia=15/rais_20240115.parquet
```

### Regras

- não sobrescrever sem necessidade
- manter metadados de ingestão
- registrar hash, tamanho e data quando possível

---

## 2.2. Bronze

### O que é

Primeira camada estruturada para consulta.

### Onde fica

No BigQuery, dataset `bronze_dev`.

### Para quê serve

- tipagem inicial
- leitura controlada
- padronização mínima
- isolamento entre bruto e transformado

### O que pode ser feito

- renomear colunas muito problemáticas
- converter tipos básicos
- adicionar colunas técnicas

### O que evitar

- regra de negócio complexa
- agregação de consumo
- deduplicação funcional agressiva

### Colunas técnicas sugeridas

- `ingestion_ts`
- `source_file_name`
- `source_system`
- `batch_id`
- `load_date`

---

## 2.3. Silver

### O que é

Camada tratada e confiável para integração e preparação analítica.

### Onde fica

No BigQuery, dataset `silver_dev`.

### Para quê serve

- limpeza de dados
- normalização
- conformidade
- enriquecimento leve
- chaves tratadas

### O que pode ser feito

- remover duplicidade técnica
- padronizar formatos de datas
- harmonizar códigos e descrições
- tratar registros inválidos
- aplicar regras de qualidade

### O que evitar

- visões finais de dashboard
- agregações excessivas

---

## 2.4. Gold

### O que é

Camada final de consumo, otimizada para analytics e BI.

### Onde fica

No BigQuery, dataset `gold_dev`.

### Para quê serve

- alimentar Superset
- disponibilizar fatos e dimensões
- simplificar consultas do usuário final

### O que pode ser feito

- criação de tabelas fato
- criação de dimensões
- criação de métricas derivadas
- agregações por período, unidade, produto etc.

---

## 3. Exemplo prático com RAIS

## 3.1. RAW

Arquivo bruto em GCS:

```text
gs://cjs-lake-dev-base/rais/ano=2024/mes=01/dia=15/rais.parquet
```

## 3.2. Bronze

Tabela:

```text
bronze_dev.rais_vinculos_raw
```

Conteúdo:

- colunas originais
- poucos ajustes técnicos
- metadados de ingestão

## 3.3. Silver

Tabela:

```text
silver_dev.rais_vinculos_tratado
```

Conteúdo:

- tipos consistentes
- datas padronizadas
- colunas relevantes renomeadas
- registros inválidos filtrados quando aplicável

## 3.4. Gold

Tabela:

```text
gold_dev.rais_empregos_por_municipio_mes
```

Conteúdo:

- agregação por município
- agregação por competência
- métricas prontas para dashboard

---

## 4. Exemplo prático com SAP HANA

## 4.1. Cenário

Suponha extração de tabelas de ERP, como pedidos e itens.

### RAW

Arquivos:

```text
gs://cjs-lake-dev-base/sap_hana/vbak/ano=2026/mes=03/dia=15/part-000.parquet
gs://cjs-lake-dev-base/sap_hana/vbap/ano=2026/mes=03/dia=15/part-000.parquet
```

### Bronze

Tabelas:

- `bronze_dev.sap_vbak_raw`
- `bronze_dev.sap_vbap_raw`

### Silver

Tabelas:

- `silver_dev.sap_pedidos`
- `silver_dev.sap_itens_pedido`

### Gold

Tabelas:

- `gold_dev.fato_vendas`
- `gold_dev.dim_cliente`
- `gold_dev.dim_produto`
- `gold_dev.dim_tempo`

---

## 5. Quem faz o quê no pipeline

## 5.1. Ingestão

Arquivo responsável:

```text
jobs/ingestion/rais_bronze.py
```

Responsabilidade:

- obter dados da origem
- gravar no GCS
- registrar metadados técnicos

## 5.2. Bronze -> Silver

Arquivo responsável:

```text
jobs/processing/bronze_to_silver.py
```

Responsabilidade:

- tratar tipos
- aplicar padronizações
- descartar sujeira técnica

## 5.3. Silver -> Gold

Arquivo responsável:

```text
jobs/processing/silver_to_gold.py
```

Responsabilidade:

- modelagem analítica
- métricas finais
- agregações de consumo

---

## 6. Convenções recomendadas

## 6.1. Nomes de datasets

- `bronze_dev`
- `silver_dev`
- `gold_dev`

Para outros ambientes:

- `bronze_hml`
- `silver_hml`
- `gold_hml`
- `bronze_prd`
- `silver_prd`
- `gold_prd`

## 6.2. Nomes de tabelas

Padrão sugerido:

```text
<dominio>_<entidade>_<granularidade>
```

Exemplos:

- `rais_vinculos_raw`
- `rais_vinculos_tratado`
- `empregos_por_municipio_mes`

## 6.3. Colunas técnicas

Em Bronze e Silver, sempre que possível:

- `batch_id`
- `load_date`
- `ingestion_ts`
- `source_file_name`
- `source_system`

---

## 7. Regras de passagem entre camadas

### RAW -> Bronze

Só avança se:

- arquivo existir
- schema mínimo for válido
- log técnico for gerado

### Bronze -> Silver

Só avança se:

- tipos principais estiverem válidos
- colunas obrigatórias existirem
- volume estiver dentro do esperado

### Silver -> Gold

Só avança se:

- regras de negócio estiverem aplicadas
- totais de controle estiverem coerentes
- métricas estiverem reproduzíveis

---

## 8. Qualidade de dados por camada

## RAW

Controles:

- arquivo chegou?
- tamanho não é zero?
- nome segue padrão?

## Bronze

Controles:

- schema compatível?
- tipos carregados?
- quantidade de linhas registrada?

## Silver

Controles:

- nulos indevidos
- chaves duplicadas
- datas inválidas
- códigos fora do domínio

## Gold

Controles:

- totais reconciliados
- métricas consistentes
- granularidade correta

---

## 9. Benefícios do modelo medalhão neste projeto

- separa claramente dado bruto de dado de consumo
- facilita debugging
- simplifica reprocessamento
- melhora governança
- permite evolução incremental do ambiente
- deixa o Superset mais estável ao consumir apenas Gold

---

## 10. Decisão recomendada

Para este projeto de estudo:

- manter RAW no GCS
- manter Bronze, Silver e Gold no BigQuery
- usar Dataproc para processamento
- usar Superset apenas na Gold

Esse desenho reduz complexidade, é fácil de explicar, fácil de demonstrar e suficientemente próximo do que várias empresas adotam em pipelines modernos de analytics.
