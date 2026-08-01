from pathlib import Path

import yaml

from deepticket.config.loader import load_app_config


def test_load_unified_yaml_config(tmp_path: Path, monkeypatch):
    config_path = tmp_path / "deepticket.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "llm": {
                    "api_key": "yaml-key",
                    "model": "openai/yaml-model",
                    "base_url": "http://yaml.example/v1",
                },
                "ingress": {
                    "routes": [
                        {
                            "type": "default",
                            "match": {"default": True},
                            "outbound": {"method": "store_only"},
                        }
                    ],
                },
                "knowledge": {
                    "repos": [
                        {
                            "id": "svc",
                            "url": "https://github.com/org/svc.git",
                            "key": "token",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(config_path))
    config = load_app_config()
    assert config.llm.api_key == "yaml-key"
    assert config.knowledge.repos[0].id == "svc"
    assert len(config.ingress.routes) == 1
