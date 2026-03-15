from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from google.cloud import bigquery

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jobs.common.config import load_env_config
from jobs.common.logger import setup_logging
from jobs.common.utils import gcs_prefix, new_batch_id


logger = logging.getLogger("jobs.ingestion.rais_bronze")


def _parse_source_ref(source: str, default_project: str) -> tuple[str, str, str]:
    parts = source.split(".")
    if len(parts) == 2:
        dataset, table = parts
        return default_project, dataset, table
    if len(parts) == 3:
        project, dataset, table = parts
        return project, dataset, table
    raise ValueError(
        "Fonte inválida. Use dataset.tabela ou projeto.dataset.tabela. "
        f"Recebido: {source}"
    )


def _export_to_gcs(
    *,
    client: bigquery.Client,
    source_fqtn: str,
    bucket_raw: str,
    export_prefix: str,
    where_sql: str,
) -> str:
    uri = f"gs://{bucket_raw}/{export_prefix}/*.parquet"
    sql = f"""
    EXPORT DATA OPTIONS(
      uri='{uri}',
      format='PARQUET',
      overwrite=true
    ) AS
    SELECT *
    FROM `{source_fqtn}`
    WHERE {where_sql}
    """
    job = client.query(sql)
    job.result()
    return uri.rsplit("/*.", 1)[0]


def _create_bronze_table(
    *,
    client: bigquery.Client,
    source_fqtn: str,
    target_fqtn: str,
    source_system: str,
    batch_id: str,
    where_sql: str,
) -> None:
    sql = f"""
    CREATE OR REPLACE TABLE `{target_fqtn}` AS
    SELECT
      t.*,
      CURRENT_TIMESTAMP() AS ingestion_ts,
      '{source_system}' AS source_system,
      '{batch_id}' AS batch_id,
      CURRENT_DATE() AS load_date
    FROM `{source_fqtn}` AS t
    WHERE {where_sql}
    """
    job = client.query(sql)
    job.result()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument(
        "--source",
        default="br_me_rais.microdados_vinculos",
        help="Fonte no BigQuery: dataset.tabela ou projeto.dataset.tabela",
    )
    parser.add_argument("--source-project", default="basedosdados")
    parser.add_argument(
        "--target-table",
        default="rais_microdados_vinculos_raw",
        help="Nome da tabela no dataset Bronze do projeto destino",
    )
    parser.add_argument(
        "--where",
        default="TRUE",
        help="Filtro SQL para reduzir volume/custo (ex: ano=2022)",
    )
    parser.add_argument("--skip-export", action="store_true")

    args = parser.parse_args()

    setup_logging()
    cfg = load_env_config(args.env)

    source_project, source_dataset, source_table = _parse_source_ref(
        args.source, args.source_project
    )
    source_fqtn = f"{source_project}.{source_dataset}.{source_table}"
    target_fqtn = f"{cfg.project_id}.{cfg.dataset_bronze}.{args.target_table}"
    batch_id = new_batch_id("rais_microdados_vinculos")

    client = bigquery.Client(project=cfg.project_id)

    logger.info("Fonte: %s", source_fqtn)
    logger.info("Destino Bronze: %s", target_fqtn)
    logger.info("Batch: %s", batch_id)
    logger.info("Filtro: %s", args.where)

    export_prefix = gcs_prefix(
        "rais",
        "microdados_vinculos",
        f"batch_id={batch_id}",
    )

    if not args.skip_export:
        prefix = _export_to_gcs(
            client=client,
            source_fqtn=source_fqtn,
            bucket_raw=cfg.bucket_raw,
            export_prefix=export_prefix,
            where_sql=args.where,
        )
        logger.info("Exportado para: %s", prefix)

    _create_bronze_table(
        client=client,
        source_fqtn=source_fqtn,
        target_fqtn=target_fqtn,
        source_system=source_fqtn,
        batch_id=batch_id,
        where_sql=args.where,
    )
    logger.info("Tabela Bronze criada/atualizada: %s", target_fqtn)


if __name__ == "__main__":
    main()
