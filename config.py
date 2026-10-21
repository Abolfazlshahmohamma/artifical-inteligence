import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "activation_phrase": "its time to wake up",
    "offline_mode": True,
    "tts_voice": "",
    "stt_backend": "windows_sapi",
    "llm": {
        "provider": "openrouter",
        "api_key": "",
        "model": "google/gemini-2.0-flash-exp:free",
        "base_url": "https://openrouter.ai/api/v1",
        "max_tokens": 8192,
        "temperature": 0.7,
        "timeout": 30
    },
    "github": {
        "token": "",
        "username": "",
        "auto_sync_repos": True,
        "watch_repos": []
    },
    "skills": {
        "auto_discover": True,
        "github_orgs": ["Kilo-Org"],
        "local_skills_dir": "skills_repo"
    },
    "voice": {
        "wake_word": "hey agent",
        "listen_timeout": 10,
        "language": "en-US"
    },
    "gui": {
        "theme": "dark",
        "always_on_top": True,
        "opacity": 0.95,
        "window_size": [480, 720]
    },
    "local_model": {
        "enabled": False,
        "model_path": "",
        "model_type": "gguf"
    },
    "web_search": {
        "enabled": True,
        "engine": "duckduckgo",
        "api_key": ""
    }
}

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = cls._load_config()
        return cls._instance
    
    @staticmethod
    def _load_config() -> dict:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(user_config)
                for key in DEFAULT_CONFIG:
                    if key in user_config and isinstance(DEFAULT_CONFIG[key], dict) and isinstance(user_config[key], dict):
                        merged[key] = {**DEFAULT_CONFIG[key], **user_config[key]}
                return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()
    
    @classmethod
    def get(cls, key: str = None, default=None):
        if cls._config is None:
            cls._config = cls._load_config()
        if key is None:
            return cls._config
        keys = key.split(".")
        value = cls._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    @classmethod
    def set(cls, key: str, value):
        if cls._config is None:
            cls._config = cls._load_config()
        keys = key.split(".")
        obj = cls._config
        for k in keys[:-1]:
            if k not in obj or not isinstance(obj[k], dict):
                obj[k] = {}
            obj = obj[k]
        obj[keys[-1]] = value
        cls._save_config()
    
    @classmethod
    def _save_config(cls):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cls._config, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def save(cls):
        cls._save_config()
    
    @classmethod
    def reload(cls):
        cls._config = cls._load_config()
        return cls._config
