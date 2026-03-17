import yaml
import os
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value

# 读取配置文件
config_path = Path(__file__).parent.parent / "config" / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f)

# 邮箱配置
EMAIL_WORKER_URL = _env_str("EMAIL_WORKER_URL", _config["email"]["worker_url"])
EMAIL_DOMAIN = _env_str("EMAIL_DOMAIN", _config["email"]["domain"])
EMAIL_PREFIX_LENGTH = _env_int("EMAIL_PREFIX_LENGTH", _config["email"]["prefix_length"])
EMAIL_PREFIX_STYLE = _env_str("EMAIL_PREFIX_STYLE", _config["email"].get("prefix_style", "random"))
EMAIL_PREFIX_RANDOM_SUFFIX_LENGTH = _env_int("EMAIL_PREFIX_RANDOM_SUFFIX_LENGTH", _config["email"].get("prefix_random_suffix_length", 4))
EMAIL_PREFIX_SEPARATOR = _env_str("EMAIL_PREFIX_SEPARATOR", _config["email"].get("prefix_separator", "."))
EMAIL_WAIT_TIMEOUT = _env_int("EMAIL_WAIT_TIMEOUT", _config["email"]["wait_timeout"])
EMAIL_POLL_INTERVAL = _env_int("EMAIL_POLL_INTERVAL", _config["email"]["poll_interval"])
EMAIL_ADMIN_PASSWORD = _env_str("EMAIL_ADMIN_PASSWORD", _config["email"].get("admin_password", ""))

# 浏览器配置
HEADLESS = _env_bool("HEADLESS", _config["browser"]["headless"])
SLOW_MO = _env_int("SLOW_MO", _config["browser"]["slow_mo"])
BROWSER_TYPE = _env_str("BROWSER_TYPE", _config["browser"].get("type", "chrome"))  # chrome 或 edge
DRIVER_STRATEGY = _env_str("DRIVER_STRATEGY", _config["browser"].get("driver_strategy", "auto"))  # auto, manager, system, local
USE_UNDETECTED_CHROME = _env_bool("USE_UNDETECTED_CHROME", True)

# 地区配置
REGION_CURRENT = _env_str("REGION_CURRENT", _config["region"]["current"])
DEVICE_TYPE = _env_str("DEVICE_TYPE", _config["region"].get("device_type", "desktop"))
REGION_USE_PROXY = _env_bool("REGION_USE_PROXY", _config["region"].get("use_proxy", False))
REGION_PROXY_MODE = _env_str("REGION_PROXY_MODE", _config["region"].get("proxy_mode", "static"))
REGION_PROXY_URL = _env_str("REGION_PROXY_URL", _config["region"].get("proxy_url", ""))
REGION_PROXY_API = _config["region"].get("proxy_api", {})
REGION_PROFILES = _config["region"]["profiles"]



# HTTP 配置
HTTP_TIMEOUT = _env_int("HTTP_TIMEOUT", _config["http"]["timeout"])
