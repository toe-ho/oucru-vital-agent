from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://oucru:oucru@db:5432/oucru"
    secret_key: str = "change-me"
    google_client_id: str = ""
    google_client_secret: str = ""

    storage_backend: str = "local"
    upload_dir: str = "/app/uploads"

    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"

    gcs_bucket_name: str = ""
    google_cloud_project: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class AgentConfig:
    def __init__(self, config_path: str = "config.yaml") -> None:
        path = Path(config_path)
        if not path.exists():
            path = Path(__file__).parent.parent / "config.yaml"
        with open(path) as f:
            raw = yaml.safe_load(f)

        llm = raw.get("llm", {})
        self.model: str = llm.get("model", "qwen3:8b")
        self.base_url: str = llm.get("base_url", "http://ollama:11434")
        self.temperature: float = llm.get("temperature", 0.1)
        self.max_tokens: int = llm.get("max_tokens", 4096)

        agent = raw.get("agent", {})
        self.max_steps: int = agent.get("max_steps", 15)
        self.verbose: bool = agent.get("verbose", True)
        self.timeout_seconds: int = 300

        sig = raw.get("signal", {})
        self.ppg_fs: int = sig.get("ppg_fs", 100)
        self.ecg_fs: int = sig.get("ecg_fs", 500)
        self.default_window_sec: int = sig.get("default_window_sec", 30)

        self.sqi_thresholds: dict = raw.get("thresholds", {
            "sqi_min": 0.5,
            "hr_min": 40,
            "hr_max": 200,
            "spo2_min": 88,
        })


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_agent_config() -> AgentConfig:
    config_path = os.getenv("CONFIG_YAML_PATH", "config.yaml")
    return AgentConfig(config_path)


settings = get_settings()
agent_config = get_agent_config()
