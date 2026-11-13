"""Agent configuration (TOML file + environment overrides)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    node_id: str
    cluster: str = "m1"
    api_base: str = "https://api.melaps.system/v1"
    api_key: str = ""
    heartbeat_interval: int = 15
    telemetry_interval: int = 5
    workdir: str = "/var/lib/melaps/jobs"

    @classmethod
    def load(cls, path="/etc/melaps/agent.toml"):
        data = {}
        p = Path(path)
        if p.exists():
            with p.open("rb") as f:
                data = tomllib.load(f)
        import os
        data["api_key"] = os.environ.get("MELAPS_AGENT_KEY", data.get("api_key", ""))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
