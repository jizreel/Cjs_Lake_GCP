from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvConfig:
    project_id: str
    bucket_raw: str
    dataset_bronze: str
    dataset_silver: str | None = None
    dataset_gold: str | None = None
    location: str = "US"


def _parse_simple_yaml_map(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            data[key] = value
    return data


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env_config(env: str) -> EnvConfig:
    conf_path = _repo_root() / "conf" / f"{env}.yaml"
    if not conf_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {conf_path}")

    raw = conf_path.read_text(encoding="utf-8")
    cfg = _parse_simple_yaml_map(raw)

    missing = [k for k in ("project_id", "bucket_raw", "dataset_bronze") if not cfg.get(k)]
    if missing:
        raise ValueError(
            f"Campos obrigatórios ausentes em {conf_path.name}: {', '.join(missing)}"
        )

    return EnvConfig(
        project_id=cfg["project_id"],
        bucket_raw=cfg["bucket_raw"],
        dataset_bronze=cfg["dataset_bronze"],
        dataset_silver=cfg.get("dataset_silver") or None,
        dataset_gold=cfg.get("dataset_gold") or None,
        location=cfg.get("location") or "US",
    )
