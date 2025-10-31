import json
import yaml
from pathlib import Path

class Config:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._load_patterns()
            self._initialized = True

    def _load_config(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def _load_patterns(self):
        patterns_path = Path(__file__).parent.parent / "patterns.json"
        with open(patterns_path, "r") as f:
            self._patterns = json.load(f)

    @property
    def config(self):
        return self._config

    @property
    def patterns(self):
        return self._patterns

config = Config()
