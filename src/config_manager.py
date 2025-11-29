import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    def __init__(self, filename: str = "config.json"):
        self.filename = filename
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.filename):
            return self._create_default_config()
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        default_config = {
            "token": None,
            "printer_settings": {
                "width": 576,
                "dither": "floyd"
            },
            "relay_url": "https://printerbot.dragnai.dev" 
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Optional[Dict[str, Any]] = None):
        if config:
            self.config = config
        with open(self.filename, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        # Prefer env var for relay_url
        if key == 'relay_url':
            env_url = os.getenv('RELAY_URL')
            if env_url:
                return env_url
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()

config_manager = ConfigManager()
