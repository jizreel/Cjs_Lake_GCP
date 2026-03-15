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


logger = logging.getLogger("jobs.processing.bronze_to_silver")


def _build_silver_sql(
    *,
    source_fqtn: str,
    target_fqtn: str,
    where_sql: str,
    dedupe: bool,
    add_processed_ts: bool,
) -> str:
    processed_ts_expr = ", CURRENT_TIMESTAMP() AS processed_ts" if add_processed_ts else ""

    if dedupe:
        select_clause = f"SELECT DISTINCT t.*{processed_ts_expr}"
    else:
        select_clause = f"SELECT t.*{processed_ts_expr}"

    return f"""
    CREATE OR REPLACE TABLE `{target_fqtn}` AS
    {select_clause}
    FROM `{source_fqtn}` AS t
    WHERE {where_sql}
    """


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument(
        "--source-table",
        default="rais_microdados_vinculos_raw",
        help="Nome da tabela no dataset Bronze (sem dataset/projeto)",
    )
    parser.add_argument(
        "--target-table",
        default="rais_microdados_vinculos_tratado",
        help="Nome da tabela no dataset Silver (sem dataset/projeto)",
    )
    parser.add_argument(
        "--where",
        default="TRUE",
        help="Filtro SQL para processar apenas um recorte (ex: ano=2022)",
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Aplica DISTINCT (pode custar mais). Use com cuidado.",
    )
    parser.add_argument(
        "--add-processed-ts",
        action="store_true",
        help="Adiciona coluna técnica processed_ts na Silver.",
    )

    args = parser.parse_args()

    setup_logging()
    cfg = load_env_config(args.env)
    if not cfg.dataset_silver:
        raise ValueError("dataset_silver não definido no arquivo de config do ambiente.")

    source_fqtn = f"{cfg.project_id}.{cfg.dataset_bronze}.{args.source_table}"
    target_fqtn = f"{cfg.project_id}.{cfg.dataset_silver}.{args.target_table}"

    client = bigquery.Client(project=cfg.project_id)

    sql = _build_silver_sql(
        source_fqtn=source_fqtn,
        target_fqtn=target_fqtn,
        where_sql=args.where,
        dedupe=args.dedupe,
        add_processed_ts=args.add_processed_ts,
    )

    logger.info("Fonte Bronze: %s", source_fqtn)
    logger.info("Destino Silver: %s", target_fqtn)
    logger.info("Filtro: %s", args.where)
    logger.info("Dedupe: %s", args.dedupe)
    logger.info("processed_ts: %s", args.add_processed_ts)

    job = client.query(sql)
    job.result()

    logger.info("Tabela Silver criada/atualizada: %s", target_fqtn)


if __name__ == "__main__":
    main()
