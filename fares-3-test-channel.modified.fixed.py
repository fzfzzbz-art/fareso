"""
╔══════════════════════════════════════════════════════════════╗
║           Telegram Notification Bot - Pro v4                 ║
║         بوت تيليجرام الاحترافي - النسخة الآمنة v4           ║
║  ✅ نظيف | آمن | لوجات دوّارة | واتساب احتياطي | systemd     ║
╠══════════════════════════════════════════════════════════════╣
║  👑 المطور: P_n_ij                                           ║
║  📢 القناة: @fz_z_Z                                          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os

import re

import sys

import json

import csv

import sqlite3

import time

import random

import atexit

import queue

import logging

import threading

import datetime

import tempfile

import faulthandler

import traceback

import subprocess

import ensurepip

import importlib.util

_DEPENDENCY_AUTO_INSTALL = str(os.getenv("AUTO_INSTALL_DEPS", "1") or "1").strip().lower() not in {"0", "false", "no", "off", "disable", "disabled"}

_REQUIRED_DEPENDENCIES = {
    "requests": "requests>=2.31.0",
    "bs4": "beautifulsoup4>=4.12.0",
    "phonenumbers": "phonenumbers>=8.13.0",
    "dotenv": "python-dotenv>=1.0.0",
    "telebot": "pyTelegramBotAPI>=4.18.0",
}

def _ensure_dependencies() -> None:
    if not _DEPENDENCY_AUTO_INSTALL:
        return
    missing_packages = []
    for module_name, package_name in _REQUIRED_DEPENDENCIES.items():
        try:
            if importlib.util.find_spec(module_name) is None:
                missing_packages.append(package_name)
        except Exception:
            missing_packages.append(package_name)

    if not missing_packages:
        return

    python_bin = sys.executable or "python3"
    install_cmd = [python_bin, "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir", *missing_packages]
    try:
        subprocess.check_call(install_cmd)
        return
    except Exception:
        try:
            ensurepip.bootstrap(upgrade=True)
            subprocess.check_call(install_cmd)
            return
        except Exception as install_err:
            raise RuntimeError(
                "فشل تثبيت المكتبات المطلوبة تلقائياً. ثبّت الحزم التالية في الاستضافة أو فعّل pip: "
                + ", ".join(missing_packages)
            ) from install_err

_ensure_dependencies()

import requests

from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:
    Retry = None

import urllib.parse

import html

import mimetypes

from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    wait,
    FIRST_COMPLETED,
    TimeoutError as FuturesTimeoutError,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from telebot import TeleBot, types
except ImportError as exc:
    raise RuntimeError(
        "Missing dependency: pyTelegramBotAPI. Install it with: pip install pyTelegramBotAPI"
    ) from exc

def _env_required(name: str):
    value = os.getenv(name, "").strip()
    return value

_DEFAULTS = {
    "BOT_TOKEN": os.environ.get("BOT_TOKEN"),
    "ADMIN_ID": int(os.environ.get("ADMIN_ID", 0)),
    "SITE_URL": "https://www.ivasms.com",
    "SITE_COOKIE": os.environ.get("SITE_COOKIE"),
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "SITE_COOKIE_FILE": "", 
    "SITE_EMAIL": "",
    "SITE_PASS": ""
}







EMBEDDED_SITE_COOKIES = [
    {
        "domain": "www.ivasms.com",
        "expirationDate": 1776031741.312787,
        "hostOnly": True,
        "httpOnly": False,
        "name": "XSRF-TOKEN",
        "path": "/",
        "sameSite": "lax",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "eyJpdiI6IkdvYW1LWmh2ZVBKMVVUSkZ6RE1qTnc9PSIsInZhbHVlIjoiZ2pkeDduSFdMZlVhVVZxWktySHEyeFpDZHNaajRrZUxNS3k0MUlGbmJjbWdmQ0tMY1JVeHBtL0FNUGcvM3NaellKS3FUQlRWNCs2WEgybzNrSWxHMys4VmM2UW5vRlpDNEtLNGh3VVk0Tm55Y283NGxpUHZvMU9jQUVPTzhwb08iLCJtYWMiOiI0YjY3Y2RkZDg4YmVkM2ExNjY0NDhlNmM4YjQxMGNkMDg2ZjI2ODZhYTQzYmUxZTNlNzZjOTY2MWM2M2M3YzFiIiwidGFnIjoiIn0=",
        "origin": "https://www.ivasms.com",
    },
    {
        "domain": "www.ivasms.com",
        "expirationDate": 1776031741.312871,
        "hostOnly": True,
        "httpOnly": True,
        "name": "ivas_sms_session",
        "path": "/",
        "sameSite": "lax",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "eyJpdiI6Ikk2OEEyV3laRUI1cXFUSGp1VGZKaHc9PSIsInZhbHVlIjoiRFdoeVN2VUNCeHJoaGRwa28vWEw1dUkxK0VjYUZTWmxkcHAraVhVM3BPMjdpaGF2WFA1a1hJeDBaU1FjRW1maEhYOEdtRDhlekp1cFUyTStaVzZrT0tjZUNSc0ZSVmJ1aFRseS9RRW55cUY5SWdlN0VlM1FSdjBicW14RFkyUmQiLCJtYWMiOiJhZTUwZmUyZmY4YjRhYmY0YjFkMjU3NTk5NmVkYmFmYTg0MDc2ZmYyNjY1YjI0MWQ2OGI1ODI2NDVkMTM3NTc2IiwidGFnIjoiIn0%3D",
        "origin": "https://www.ivasms.com",
    },
]

def _get(key: str, fallback: str = "") -> str:
    """يقرأ المتغير من البيئة أولاً، وإن لم يجده يرجع القيمة المدمجة."""
    return os.getenv(key, "").strip() or _DEFAULTS.get(key, fallback)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "")
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on", "enabled"}

def _default_worker_threads() -> int:
    """عدد ثريدات آمن للاستضافات الضعيفة افتراضياً مع إمكانية الرفع من البيئة."""
    cpu = os.cpu_count() or 2
    safe_cap = max(2, int(os.getenv("HOSTING_MAX_WORKERS", "4") or "4"))
    return max(2, min(safe_cap, cpu))

BOT_TOKEN        = _get("BOT_TOKEN")

ADMIN_ID         = int(_get("ADMIN_ID", "0") or "0")

SITE_URL         = _get("SITE_URL", "https://www.ivasms.com")

API_TOKEN        = _get("API_TOKEN", "")

SITE_COOKIE      = _get("SITE_COOKIE")

SITE_COOKIE_FILE = _get("SITE_COOKIE_FILE", "")

SITE_EMAIL       = _get("SITE_EMAIL")

SITE_PASS        = _get("SITE_PASS")

WA_NUMBER_1      = _get("WA_NUMBER_1", "")   # رقم أساسي

WA_APIKEY_1      = _get("WA_APIKEY_1", "")

WA_NUMBER_2      = _get("WA_NUMBER_2", "")   # رقم احتياطي

WA_APIKEY_2      = _get("WA_APIKEY_2", "")

SUPPORT_USERNAME = _get("SUPPORT_USERNAME", "@P_n_ij")

BOT_WORKER_THREADS = max(2, min(8, int(_get("BOT_WORKER_THREADS", str(_default_worker_threads())) or str(_default_worker_threads()))))
FAST_RESPONSE_MULTIPLIER = max(1.0, float(_get("FAST_RESPONSE_MULTIPLIER", "2") or "2"))
TEST_MODE_INTERVAL_SECONDS = max(180, int(_get("TEST_MODE_INTERVAL_SECONDS", "180") or "180"))
STORAGE_TARGET_GB = max(10240, int(_get("STORAGE_TARGET_GB", "10240") or "10240"))
MAX_NUMBERS_PER_COUNTRY_BUCKET = max(1000, int(_get("MAX_NUMBERS_PER_COUNTRY_BUCKET", "1000000") or "1000000"))

AUTO_SYNC_NUMBERS = _env_flag("AUTO_SYNC_NUMBERS", False)

BASE_DIR = Path(__file__).resolve().parent

def _resolve_storage_root() -> Path:
    """يختار مسار تخزين قابل للكتابة ليتوافق مع أغلب الاستضافات."""
    candidates = [
        os.getenv("APP_STORAGE_DIR", "").strip(),
        os.getenv("RENDER_DISK_PATH", "").strip(),
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip(),
        os.getenv("BOT_STORAGE_DIR", "").strip(),
        str(BASE_DIR),
        str(Path(tempfile.gettempdir()) / "telegram_bot_pro"),
    ]
    seen = set()
    for raw_path in candidates:
        path_text = str(raw_path or "").strip()
        if not path_text or path_text in seen:
            continue
        seen.add(path_text)
        try:
            candidate = Path(path_text).expanduser().resolve()
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    fallback = Path(tempfile.gettempdir()) / "telegram_bot_pro_fallback"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

STORAGE_DIR = _resolve_storage_root()

LOGS_DIR = STORAGE_DIR / "logs"

DATA_DIR = STORAGE_DIR / "data"

BACKUP_DIR = STORAGE_DIR / "backups"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"

NUMBERS_FILE = DATA_DIR / "numbers.json"

EVENTS_FILE = DATA_DIR / "events.json"

WA_QUEUE_FILE = DATA_DIR / "wa_queue.json"

BOT_LOCK_FILE = DATA_DIR / "bot.lock"

PAID_NUMBERS_FILE = DATA_DIR / "paid_numbers.json"

RUNTIME_COOKIES_FILE = DATA_DIR / "runtime_cookies.json"

NUMBERS_SQLITE_FILE = DATA_DIR / "numbers.sqlite3"

SYNC_REPORT_FILE = DATA_DIR / "sync_report.json"

NUMBERS_SYNC_SOURCE = _get("NUMBERS_SYNC_SOURCE", "site").strip().lower() or "site"

AUTHORIZED_SOURCE_URL = _get("AUTHORIZED_SOURCE_URL", "")

AUTHORIZED_SOURCE_FILE = _get("AUTHORIZED_SOURCE_FILE", "")

AUTHORIZED_SOURCE_TOKEN = _get("AUTHORIZED_SOURCE_TOKEN", "")

AUTHORIZED_SOURCE_TIMEOUT_SECONDS = max(5, int(_get("AUTHORIZED_SOURCE_TIMEOUT_SECONDS", "20") or "20"))

AUTHORIZED_SOURCE_RETRIES = max(1, int(_get("AUTHORIZED_SOURCE_RETRIES", "3") or "3"))

MIN_NUMBERS_PER_COUNTRY = 1  # قبول جميع الأرقام بدون حد أدنى

SYNC_ALLOWED_COUNTRIES = [item.strip() for item in _get("SYNC_ALLOWED_COUNTRIES", "").split(",") if item.strip()]

REQUIRE_AVAILABLE_STATUS = _env_flag("REQUIRE_AVAILABLE_STATUS", True)

STRICT_E164_VALIDATION = _env_flag("STRICT_E164_VALIDATION", True)

KEEP_BELOW_MIN_COUNTRIES = True  # قبول الأرقام بدون قيود

DEVELOPER_USERNAME        = "P_n_ij"

DEVELOPER_CHANNEL         = "@fz_z_Z"

CHANNEL_ID                = -1002249882059

REQUIRED_CHANNEL_USERNAME = "fz_z_Z"

TEST_CHANNEL_ID = int(_get("TEST_CHANNEL_ID", "0") or "0")

TEST_MODE_LABEL = _get("TEST_MODE_LABEL", "TEST/FAKE")

TEST_SENDER_NAME = _get("TEST_SENDER_NAME", "M.v_Nember 2")

TEST_REGION_FLAG = _get("TEST_REGION_FLAG", "🇻🇪")

TEST_REGION_TAG = _get("TEST_REGION_TAG", "#VE")

TEST_NUMBER_PREFIX = _get("TEST_NUMBER_PREFIX", "58VEN")

TEST_MAIN_CHANNEL_URL = _get("TEST_MAIN_CHANNEL_URL", f"https://t.me/{REQUIRED_CHANNEL_USERNAME}" if REQUIRED_CHANNEL_USERNAME else "")

TEST_GET_NUMBER_URL = _get("TEST_GET_NUMBER_URL", "")

TEST_MAIN_BUTTON_TEXT = _get("TEST_MAIN_BUTTON_TEXT", "Main Channel")

TEST_GET_BUTTON_TEXT = _get("TEST_GET_BUTTON_TEXT", "👍 Get Nember")

WELCOME_MESSAGE_FILE      = DATA_DIR / "welcome_message.txt"

DEFAULT_USER_WELCOME      = (
    "👋 أهلاً بك\n\n"
    "تم تحميل أقسام الموقع الحالية لك مباشرة.\n"
    "اختَر أي قسم من تحت، ولو القسم عليه أرقام هتقدر تغيّر الرقم وتفحص آخر كود."
)

_SECRET_ENV_KEYS = [
    "BOT_TOKEN",
    "API_TOKEN",
    "SITE_COOKIE",
    "SITE_EMAIL",
    "SITE_PASS",
    "WA_APIKEY_1",
    "WA_APIKEY_2",
]

def _collect_known_secret_values() -> List[str]:
    values: List[str] = []
    for key in _SECRET_ENV_KEYS:
        try:
            value = str(os.getenv(key, "") or _DEFAULTS.get(key, "") or "").strip()
        except Exception:
            value = ""
        if value and len(value) >= 6 and value not in values:
            values.append(value)
    return sorted(values, key=len, reverse=True)

def _redact_secret_text(value: Any) -> str:
    text_value = str(value or "")
    for secret in _collect_known_secret_values():
        if secret and secret in text_value:
            text_value = text_value.replace(secret, f"[REDACTED:{len(secret)}]")
    text_value = re.sub(
        r'(?i)((?:bot[_-]?token|token|api[_-]?key|apikey|password|pass|cookie|authorization)\s*[=:]\s*)([^\s,;]+)',
        r'\1[REDACTED]',
        text_value,
    )
    return text_value

class _SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = _redact_secret_text(record.getMessage())
            record.args = ()
        except Exception:
            pass
        return True

def setup_logging() -> logging.Logger:
    log_level_name = str(os.getenv("LOG_LEVEL", "INFO") or "INFO").strip().upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Handler 1: Console ---
    console_h = logging.StreamHandler()
    console_h.setFormatter(fmt)
    console_h.setLevel(logging.INFO)

    # --- Handler 2: ملف عام (دوران كل 5MB، يحتفظ بـ 10 نسخ) ---
    main_file_h = RotatingFileHandler(
        LOGS_DIR / "bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=10,
        encoding="utf-8",
    )
    main_file_h.setFormatter(fmt)
    main_file_h.setLevel(log_level)

    # --- Handler 3: ملف يومي منفصل (يحتفظ بـ 30 يوم) ---
    daily_h = TimedRotatingFileHandler(
        LOGS_DIR / "daily.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    daily_h.setFormatter(fmt)
    daily_h.setLevel(logging.INFO)

    # --- Handler 4: ملف أخطاء فقط ---
    error_h = RotatingFileHandler(
        LOGS_DIR / "errors.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_h.setFormatter(fmt)
    error_h.setLevel(logging.ERROR)

    redaction_filter = _SecretRedactionFilter()
    for handler in (console_h, main_file_h, daily_h, error_h):
        handler.addFilter(redaction_filter)

    # --- تطبيق على الـ root logger ---
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(log_level)
    root.addHandler(console_h)
    root.addHandler(main_file_h)
    root.addHandler(daily_h)
    root.addHandler(error_h)

    return logging.getLogger("BotPro")

logger = setup_logging()

def _install_runtime_guardrails_once() -> None:
    """يضمن ظهور الأخطاء في لوجات الاستضافة بدل اختفائها بصمت."""
    if getattr(_install_runtime_guardrails_once, "_installed", False):
        return
    _install_runtime_guardrails_once._installed = True

    try:
        faulthandler.enable(all_threads=True)
    except Exception:
        pass

    def _log_uncaught(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return sys.__excepthook__(exc_type, exc_value, exc_traceback)
        try:
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        except Exception:
            traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = _log_uncaught
    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            _log_uncaught(args.exc_type, args.exc_value, args.exc_traceback)
        threading.excepthook = _thread_hook

_HOSTING_HTTP_HOST = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"

try:
    _HOSTING_HTTP_PORT = int(str(os.getenv("PORT", "0") or "0").strip())
except ValueError:
    _HOSTING_HTTP_PORT = 0

_HOSTING_HTTP_ENABLED = str(os.getenv("HOSTING_HTTP_ENABLED", "1" if _HOSTING_HTTP_PORT else "0")).strip().lower() in {"1", "true", "yes", "on"}

_hosting_http_lock = threading.Lock()

_hosting_http_started = False

class _HostingHealthHandler(BaseHTTPRequestHandler):
    def _build_payload(self):
        return {
            "status": "ok",
            "service": "telegram-bot",
            "storage_dir": str(STORAGE_DIR),
            "storage_target_gb": STORAGE_TARGET_GB,
            "bot_worker_threads": BOT_WORKER_THREADS,
            "time": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def _send_health_response(self, include_body: bool = True):
        payload = self._build_payload()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self):
        self._send_health_response(include_body=True)

    def do_HEAD(self):
        self._send_health_response(include_body=False)

    def log_message(self, fmt, *args):
        logger.info("HTTP health | " + (fmt % args))

def _start_hosting_http_server_once() -> None:
    """يشغّل Health Check صغير لبعض الاستضافات التي تتطلب منفذ HTTP."""
    global _hosting_http_started
    if not _HOSTING_HTTP_ENABLED or _HOSTING_HTTP_PORT <= 0:
        return
    with _hosting_http_lock:
        if _hosting_http_started:
            return
        _hosting_http_started = True

    def _serve():
        try:
            server = ThreadingHTTPServer((_HOSTING_HTTP_HOST, _HOSTING_HTTP_PORT), _HostingHealthHandler)
            logger.info(f"✅ Hosting health server listening on {_HOSTING_HTTP_HOST}:{_HOSTING_HTTP_PORT}")
            server.serve_forever()
        except Exception as http_err:
            logger.exception(f"Health server failed: {http_err}")

    threading.Thread(target=_serve, daemon=True).start()

_install_runtime_guardrails_once()

_HOSTING_HEARTBEAT_INTERVAL_SECONDS = max(60, int(str(os.getenv("HOSTING_HEARTBEAT_INTERVAL", "300") or "300").strip() or "300"))
_hosting_heartbeat_started = False
_hosting_heartbeat_lock = threading.Lock()


def _start_hosting_heartbeat_once() -> None:
    global _hosting_heartbeat_started
    with _hosting_heartbeat_lock:
        if _hosting_heartbeat_started:
            return
        _hosting_heartbeat_started = True

    def _loop():
        while True:
            try:
                uptime_text = _get_uptime() if '_get_uptime' in globals() else 'starting'
                logger.info(f"💓 Hosting heartbeat | uptime={uptime_text} | threads={threading.active_count()}")
            except Exception as heartbeat_err:
                logger.warning(f"Hosting heartbeat warning: {heartbeat_err}")
            time.sleep(_HOSTING_HEARTBEAT_INTERVAL_SECONDS)

    threading.Thread(target=_loop, daemon=True).start()

def _cookie_host() -> str:
    return urllib.parse.urlparse(SITE_URL).hostname or "www.ivasms.com"

def _cookie_domain_rank(domain: str, host: str) -> int:
    domain = str(domain or "").strip().lstrip(".").lower()
    host = str(host or "").strip().lower()
    if not domain:
        return 0
    if domain == host:
        return 4
    if host.endswith("." + domain) or domain.endswith("." + host):
        return 3
    base_host = host.replace("www.", "", 1)
    if domain == base_host or domain.endswith("." + base_host):
        return 2
    return 1

def _pick_cookie_value(session: requests.Session, *names: str) -> str:
    host = _cookie_host()
    best_value = ""
    best_score = (-1, -1, -1)
    wanted = {str(name or "").strip() for name in names if str(name or "").strip()}
    for cookie in session.cookies:
        if cookie.name not in wanted or not cookie.value:
            continue
        score = (
            _cookie_domain_rank(getattr(cookie, "domain", ""), host),
            1 if (getattr(cookie, "path", "/") or "/") == "/" else 0,
            len(str(cookie.value)),
        )
        if score > best_score:
            best_score = score
            best_value = str(cookie.value)
    return best_value

def _refresh_xsrf_header(session: requests.Session):
    xsrf = _pick_cookie_value(session, "XSRF-TOKEN", "XSRF_TOKEN")
    if xsrf:
        session.headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf)
    else:
        session.headers.pop("X-XSRF-TOKEN", None)

def _cookie_file_candidates() -> List[Path]:
    seen = set()
    candidates = []
    raw = (SITE_COOKIE_FILE or "").strip()
    raw_candidates = []
    if raw:
        raw_candidates.extend([Path(raw), BASE_DIR / raw])
    raw_candidates.extend([
        BASE_DIR / "exported-cookies.json",
        BASE_DIR / "exported-cookies-5.json",
    ])
    for candidate in raw_candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            candidates.append(candidate)
    return candidates

def _load_cookie_items(session: requests.Session, items, source_label: str) -> bool:
    host = _cookie_host()
    if not isinstance(items, list):
        return False

    loaded = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        value = str(item.get("value") or "").strip()
        if not name or not value:
            continue
        domain = item.get("domain") or host
        path = item.get("path") or "/"
        session.cookies.set(name, value, domain=domain, path=path)
        loaded += 1

    if loaded:
        _refresh_xsrf_header(session)
        logger.info(f"🍪 تم تحميل {loaded} كوكي من {source_label}")
        return True
    return False

def _load_cookies_from_json_file(session: requests.Session) -> bool:
    for cookie_path in _cookie_file_candidates():
        try:
            if not cookie_path.exists() or not cookie_path.is_file():
                continue
            with open(cookie_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if _load_cookie_items(session, data, f"الملف: {cookie_path.name}"):
                return True
        except Exception as cookie_file_err:
            logger.warning(f"Cookie file warning ({cookie_path}): {cookie_file_err}")
    return False

def _apply_site_cookie(session: requests.Session, cookie_blob: str):
    """يضيف الكوكيز إلى الـ session سواء كانت key=value أو قيمة Session فقط."""
    host = _cookie_host()
    if not cookie_blob:
        return
    try:
        if "=" in cookie_blob and ";" in cookie_blob:
            for part in cookie_blob.split(";"):
                if "=" not in part:
                    continue
                name, value = part.split("=", 1)
                name = name.strip()
                value = value.strip()
                if name and value:
                    session.cookies.set(name, value, domain=host, path="/")
        else:
            session.cookies.set("ivas_sms_session", cookie_blob, domain=host, path="/")
        _refresh_xsrf_header(session)
    except Exception as cookie_err:
        logger.warning(f"SITE_COOKIE parse warning: {cookie_err}")

def _looks_like_guest_page(html: str) -> bool:
    page = (html or "").lower()
    guest_markers = [
        "start earning now - sign in",
        "create free account - register",
        "/login",
        "/register",
    ]
    return sum(marker in page for marker in guest_markers) >= 2

def _is_authenticated_response(resp: Optional[requests.Response]) -> bool:
    if not resp:
        return False
    final_url = (getattr(resp, "url", "") or "").lower()
    page = (getattr(resp, "text", "") or "").lower()
    auth_markers = [
        "logout",
        "account code",
        "my numbers",
        "client active sms",
        "my sms statistics",
        "portal/profile",
    ]
    if "/portal" in final_url or "/portal/profile" in final_url:
        return True
    return (not _looks_like_guest_page(page)) and sum(marker in page for marker in auth_markers) >= 2

def _login_site_with_credentials(session: requests.Session) -> bool:
    """محاولة تسجيل الدخول بالبريد/كلمة المرور وتحديث الكوكيز تلقائياً."""
    if not (SITE_EMAIL and SITE_PASS):
        return False
    try:
        login_url = f"{SITE_URL}/login"
        resp = session.get(login_url, timeout=15, allow_redirects=True)
        if _is_authenticated_response(resp):
            logger.info("✅ الجلسة الحالية مسجّلة دخول بالفعل")
            return True
        if resp.status_code != 200:
            logger.warning(f"Login page unavailable: {resp.status_code}")
            return False

        csrf_match = re.search(
            r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
            resp.text,
            flags=re.IGNORECASE,
        )
        if not csrf_match:
            csrf_match = re.search(
                r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
                resp.text,
                flags=re.IGNORECASE,
            )
        csrf = csrf_match.group(1) if csrf_match else ""

        payload = {
            "_token": csrf,
            "email": SITE_EMAIL,
            "password": SITE_PASS,
            "remember": "on",
        }
        headers = {
            "Referer": login_url,
            "Origin": SITE_URL,
        }
        post_resp = session.post(login_url, data=payload, headers=headers, timeout=20, allow_redirects=True)
        _refresh_xsrf_header(session)

        if post_resp.status_code == 200 and _is_authenticated_response(post_resp):
            logger.info("✅ تم تسجيل الدخول للموقع بنجاح عبر البريد/كلمة المرور")
            return True

        logger.warning("⚠️ تعذر تسجيل الدخول تلقائياً، سيُستخدم الـ cookie الموجود إن كان صالحاً")
        return False
    except Exception as login_err:
        logger.warning(f"Auto login failed: {login_err}")
        return False

_SITE_SESSION_BOOTSTRAP_TTL_SECONDS = max(15.0, float(str(_get("SITE_SESSION_BOOTSTRAP_TTL_SECONDS", "90") or "90").strip() or "90"))
_SITE_SESSION_POOL_SIZE = max(2, min(8, BOT_WORKER_THREADS))
_site_session_bootstrap_lock = threading.Lock()
_site_session_bootstrap_cache = {"ok_until": 0.0, "cookies": []}

def _mount_session_adapters(session: requests.Session) -> None:
    try:
        retries = Retry(
            total=1,
            connect=1,
            read=1,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "HEAD", "OPTIONS"}),
            raise_on_status=False,
        ) if Retry else 1
        adapter = HTTPAdapter(
            pool_connections=_SITE_SESSION_POOL_SIZE,
            pool_maxsize=_SITE_SESSION_POOL_SIZE,
            max_retries=retries,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except Exception as adapter_err:
        logger.debug(f"session adapter mount skipped: {adapter_err}")

def _session_cookie_snapshot(session: requests.Session) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for cookie in session.cookies:
        items.append({
            "domain": getattr(cookie, "domain", "") or "",
            "name": getattr(cookie, "name", "") or "",
            "value": getattr(cookie, "value", "") or "",
            "path": getattr(cookie, "path", "/") or "/",
            "secure": bool(getattr(cookie, "secure", False)),
            "expires": getattr(cookie, "expires", None),
            "rest": dict(getattr(cookie, "_rest", {}) or {}),
        })
    return items

def _store_site_session_bootstrap(session: requests.Session) -> None:
    if _SITE_SESSION_BOOTSTRAP_TTL_SECONDS <= 0:
        return
    try:
        items = _session_cookie_snapshot(session)
        if not items:
            return
        with _site_session_bootstrap_lock:
            _site_session_bootstrap_cache["cookies"] = items
            _site_session_bootstrap_cache["ok_until"] = time.time() + _SITE_SESSION_BOOTSTRAP_TTL_SECONDS
    except Exception as cache_err:
        logger.debug(f"site bootstrap cache store skipped: {cache_err}")

def _restore_site_session_bootstrap(session: requests.Session) -> bool:
    try:
        with _site_session_bootstrap_lock:
            ok_until = float(_site_session_bootstrap_cache.get("ok_until") or 0.0)
            items = list(_site_session_bootstrap_cache.get("cookies") or [])
        if not items or time.time() >= ok_until:
            return False
        restored = _load_cookie_items(session, items, "bootstrap_cache")
        if restored:
            _refresh_xsrf_header(session)
        return restored
    except Exception as cache_err:
        logger.debug(f"site bootstrap cache restore skipped: {cache_err}")
        return False

def _build_site_session() -> requests.Session:
    """يبني Session موحدة سريعة وتستخدم Connection Pool + bootstrap cache لتقليل التأخير."""
    session = requests.Session()
    _mount_session_adapters(session)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": SITE_URL,
        "Origin": SITE_URL,
    })

    if API_TOKEN:
        session.headers["Authorization"] = f"Bearer {API_TOKEN}"

    loaded_from_file = _load_site_cookies(session)
    restored_from_bootstrap = _restore_site_session_bootstrap(session)
    if not loaded_from_file and not restored_from_bootstrap:
        _apply_site_cookie(session, SITE_COOKIE or "")

    try:
        probe = session.get(f"{SITE_URL}/portal", timeout=12, allow_redirects=True)
        if _is_authenticated_response(probe):
            logger.info("✅ تم التحقق من جلسة الموقع بنجاح")
            _store_site_session_bootstrap(session)
            return session
    except Exception as probe_err:
        logger.warning(f"Site probe warning: {probe_err}")

    if SITE_EMAIL and SITE_PASS:
        if _login_site_with_credentials(session):
            _store_site_session_bootstrap(session)
            return session

    return session

_json_lock = threading.RLock()

def load_json(path: Path, default):
    try:
        with _json_lock:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception as e:
        logger.error(f"load_json({path}): {e}")
    return default

def save_json(path: Path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with _json_lock:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp_path, path)
    except Exception as e:
        logger.error(f"save_json({path}): {e}")

users_db        = load_json(USERS_FILE,        {"users": []})

numbers_db      = load_json(NUMBERS_FILE,      {"numbers": []})

events_db       = load_json(EVENTS_FILE,       {"events": []})

paid_numbers_db = load_json(PAID_NUMBERS_FILE, {"numbers": []})

wa_queue   = load_json(WA_QUEUE_FILE, {"pending": []})

def _get_welcome_message() -> str:
    """يقرأ رسالة الترحيب المخصصة من الملف، وإن لم تكن موجودة يرجع الرسالة الافتراضية."""
    try:
        if WELCOME_MESSAGE_FILE.exists():
            return WELCOME_MESSAGE_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return DEFAULT_USER_WELCOME

def _save_welcome_message(text: str):
    """يحفظ رسالة الترحيب المخصصة في ملف."""
    try:
        WELCOME_MESSAGE_FILE.write_text(text.strip(), encoding="utf-8")
    except Exception as e:
        logger.warning(f"تعذّر حفظ رسالة الترحيب: {e}")

def _mask_number(number: str) -> str:
    """يُعيد الرقم مع تشفير الأرقام الوسطى مع الإبقاء على البداية والنهاية."""
    raw = str(number or "").strip()
    digits_only = re.sub(r"\D", "", raw)
    if not digits_only:
        return raw or "غير متوفر"
    if len(digits_only) <= 4:
        return digits_only[:1] + "*" * max(1, len(digits_only) - 2) + digits_only[-1:]
    if len(digits_only) <= 8:
        return digits_only[:2] + "*" * max(1, len(digits_only) - 4) + digits_only[-2:]
    prefix = raw[:5]
    suffix = digits_only[-3:]
    hidden = max(3, len(digits_only) - 8)
    return prefix + "*" * hidden + suffix

def _save_new_welcome_step(message):
    if message.from_user.id != ADMIN_ID:
        return
    new_text = (message.text or "").strip()
    if not new_text:
        bot.reply_to(message, "❌ الرسالة فارغة، لم يتم الحفظ.")
        return
    if new_text in ("/reset", "reset"):
        try:
            if WELCOME_MESSAGE_FILE.exists():
                WELCOME_MESSAGE_FILE.unlink()
        except Exception as e:
            logger.warning(f"تعذّر حذف رسالة الترحيب المخصصة: {e}")
        bot.reply_to(message, f"✅ تم إعادة رسالة /start للوضع الافتراضي.\n\n{DEFAULT_USER_WELCOME}")
        return
    _save_welcome_message(new_text)
    bot.reply_to(message, f"✅ تم حفظ رسالة الترحيب الجديدة:\n\n{new_text}")
    log_event("WELCOME_UPDATED", {"by": message.from_user.id, "text": new_text[:100]})

def _handle_sync_from_panel(chat_id: int):
    _dev_fetch_from_site_and_report(chat_id)

user_number_state: Dict[int, Dict] = {}

admin_pending_platform: Dict[int, str] = {}

_wa_retry_queue: queue.Queue = queue.Queue()   # رسائل واتساب الفاشلة

def _send_whatsapp_single(phone: str, apikey: str, text: str) -> bool:
    """إرسال رسالة واتساب عبر CallMeBot لرقم واحد – يرجع True عند النجاح"""
    try:
        encoded = urllib.parse.quote(text)
        url = (
            f"https://api.callmebot.com/whatsapp.php"
            f"?phone={phone}&text={encoded}&apikey={apikey}"
        )
        r = requests.get(url, timeout=12)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"WA send error ({phone}): {e}")
        return False

def send_whatsapp(text: str, label: str = "") -> bool:
    """
    يحاول الإرسال للرقم الأساسي أولاً،
    عند الفشل يجرب الاحتياطي،
    عند الفشلين يضيف الرسالة لقائمة الإعادة.
    """
    tag = f"[{label}] " if label else ""
    log_prefix = f"WA{tag}"

    # محاولة الرقم الأساسي
    if WA_NUMBER_1 and WA_APIKEY_1:
        if _send_whatsapp_single(WA_NUMBER_1, WA_APIKEY_1, text):
            logger.info(f"{log_prefix}✅ أُرسلت عبر الرقم الأساسي")
            return True
        logger.warning(f"{log_prefix}⚠️ فشل الرقم الأساسي، جاري تجربة الاحتياطي…")

    # محاولة الرقم الاحتياطي
    if WA_NUMBER_2 and WA_APIKEY_2:
        if _send_whatsapp_single(WA_NUMBER_2, WA_APIKEY_2, text):
            logger.info(f"{log_prefix}✅ أُرسلت عبر الرقم الاحتياطي")
            return True
        logger.warning(f"{log_prefix}⚠️ فشل الرقم الاحتياطي أيضاً")

    # وضع في قائمة الإعادة
    _wa_retry_queue.put({"text": text, "timestamp": time.time(), "retries": 0})
    _save_wa_queue_to_disk()
    logger.error(f"{log_prefix}❌ فشل الإرسال – أُضيفت للقائمة الاحتياطية")
    return False

def _save_wa_queue_to_disk():
    """يحفظ قائمة إعادة الإرسال على القرص"""
    items = list(_wa_retry_queue.queue)
    save_json(WA_QUEUE_FILE, {"pending": items})

def _restore_wa_queue_from_disk():
    """يعيد تحميل رسائل واتساب المعلقة بعد إعادة التشغيل"""
    pending_items = wa_queue.get("pending", []) if isinstance(wa_queue, dict) else []
    restored = 0
    for item in pending_items:
        if isinstance(item, dict) and item.get("text"):
            _wa_retry_queue.put(item)
            restored += 1
    if restored:
        logger.info(f"📦 تم استرجاع {restored} رسالة واتساب معلقة من القرص")

def _wa_retry_worker():
    """خيط يعمل في الخلفية ويعيد إرسال الرسائل الفاشلة"""
    while True:
        time.sleep(60)  # كل دقيقة
        tmp = []
        while not _wa_retry_queue.empty():
            item = _wa_retry_queue.get()
            item["retries"] = item.get("retries", 0) + 1
            if item["retries"] > 5:
                logger.warning(f"WA retry: تجاوزت 5 محاولات – تم الحذف: {item['text'][:50]}")
                continue
            sent = False
            for phone, key in [
                (WA_NUMBER_1, WA_APIKEY_1),
                (WA_NUMBER_2, WA_APIKEY_2),
            ]:
                if phone and key:
                    if _send_whatsapp_single(phone, key, item["text"]):
                        logger.info(f"WA retry ✅ محاولة {item['retries']} نجحت")
                        sent = True
                        break
            if not sent:
                tmp.append(item)

        for item in tmp:
            _wa_retry_queue.put(item)

        _save_wa_queue_to_disk()

_wa_retry_worker_started = False
_wa_retry_worker_lock = threading.Lock()

def _start_wa_retry_worker_once() -> None:
    global _wa_retry_worker_started
    with _wa_retry_worker_lock:
        if _wa_retry_worker_started:
            return
        _wa_retry_worker_started = True
    threading.Thread(target=_wa_retry_worker, daemon=True, name="wa-retry-worker").start()

def log_event(event_type: str, details: dict):
    """يحفظ حدثاً في events.json ويضمن حد أقصى 500 حدث"""
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type":      event_type,
        **details,
    }
    events_db["events"].append(entry)
    if len(events_db["events"]) > 50000:
        events_db["events"] = events_db["events"][-50000:]
    save_json(EVENTS_FILE, events_db)
    logger.info(f"EVENT [{event_type}]: {details}")

def _country_groups_for_platform(platform: str) -> List[Dict]:
    normalized = _normalize_platform(platform)
    index = _get_numbers_runtime_index()
    groups = index.get("country_groups", {}).get(normalized, []) or []
    return [dict(item) for item in groups]


def _numbers_for_platform_country(platform: str, country_key: str) -> List[Dict]:
    normalized = _normalize_platform(platform)
    target_key = str(country_key or "").strip() or "unknown"
    index = _get_numbers_runtime_index()
    rows = index.get("platform_country_rows", {}).get(normalized, {}).get(target_key, []) or []
    return [dict(item) for item in rows]


def _reset_state_country_rows(state: Optional[Dict]) -> Dict:
    payload = state if isinstance(state, dict) else {}
    payload.pop('_country_rows_platform', None)
    payload.pop('_country_rows_key', None)
    payload.pop('_country_rows', None)
    return payload


def _state_country_rows(state: Optional[Dict], platform: str, country_key: str, refresh: bool = False) -> List[Dict]:
    payload = state if isinstance(state, dict) else {}
    normalized = _normalize_platform(platform)
    target_key = str(country_key or '').strip() or 'unknown'
    cached_platform = _normalize_platform(payload.get('_country_rows_platform', ''))
    cached_key = str(payload.get('_country_rows_key') or '').strip()
    cached_rows = payload.get('_country_rows', [])
    if (
        not refresh
        and cached_platform == normalized
        and cached_key == target_key
        and isinstance(cached_rows, list)
        and cached_rows
    ):
        return [dict(item) for item in cached_rows if isinstance(item, dict)]

    rows = _numbers_for_platform_country(normalized, target_key)
    random.shuffle(rows)
    payload['_country_rows_platform'] = normalized
    payload['_country_rows_key'] = target_key
    payload['_country_rows'] = [dict(item) for item in rows]
    return [dict(item) for item in rows if isinstance(item, dict)]


SPECIAL_PLATFORMS = set()
SPECIAL_PLATFORMS = set()

PLATFORM_BUTTON_ICONS = {
    "WhatsApp": "💬",
    "Telegram": "✈️",
    "TikTok": "🎵",
    "Instagram": "📸",
    "Facebook": "📘",
    "Twitter": "🐦",
    "Snapchat": "👻",
    "Line": "💚",
    "WeChat": "🟢",
    "Viber": "📞",
    "Discord": "🎮",
    "Gmail": "📧",
    "Hotmail": "📨",
    "Yahoo": "📬",
    "Microsoft": "🪟",
    "Apple": "🍎",
    "Amazon": "🛒",
    "Netflix": "🎬",
    "Uber": "🚕",
    "PayPal": "💳",
}

def _extract_csrf_token(page_html: str) -> str:
    if not page_html:
        return ""
    patterns = [
        r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
        r"_token['\"]?\s*[,=:]\s*['\"]([^'\"]+)['\"]",
        r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def _strip_html_text(value: str) -> str:
    text_value = re.sub(r"<br\s*/?>", "\n", str(value or ""), flags=re.IGNORECASE)
    text_value = re.sub(r"<[^>]+>", " ", text_value)
    text_value = html.unescape(text_value)
    return re.sub(r"\s+", " ", text_value).strip()

def _extract_ranges_from_summary(summary_html: str) -> List[str]:
    found = []
    for match in re.finditer(r"toggleRange\('([^']+)'", summary_html or ""):
        range_name = match.group(1).strip()
        if range_name and range_name not in found:
            found.append(range_name)
    return found

def _extract_number_rows(range_html: str) -> List[str]:
    found = []
    for match in re.finditer(r"toggleNum\w*\('([^']+)'", range_html or ""):
        number = _normalize_number(match.group(1))
        if number and number not in found:
            found.append(number)
    return found

def _extract_sms_entries(sms_html: str) -> List[Dict]:
    """
    يستخرج إدخالات SMS من HTML الموقع.
    - دعم متعدد لأنماط HTML المختلفة (رئيسي + احتياطي)
    - استخراج الأكواد بثبات: الكلمات المفتاحية أولاً، ثم الأرقام (4-8)
    - تجاهل السنوات والأرقام العشوائية
    """
    entries  = []
    raw_html = sms_html or ""

    # النمط الرئيسي (البنية الأصلية للموقع)
    pattern_main = re.compile(
        r"<tr[^>]*>\s*<td[^>]*><span[^>]*class=[\"']cli-tag[\"'][^>]*>(.*?)</span></td>"
        r"\s*<td[^>]*><div[^>]*class=[\"']msg-text[\"'][^>]*>(.*?)</div></td>"
        r"\s*<td[^>]*class=[\"']time-cell[\"'][^>]*>(.*?)</td>",
        re.IGNORECASE | re.DOTALL,
    )
    # النمط الاحتياطي (أي ثلاثة أعمدة)
    pattern_fallback = re.compile(
        r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>",
        re.IGNORECASE | re.DOTALL,
    )

    matched = pattern_main.findall(raw_html) or pattern_fallback.findall(raw_html)

    # أنماط استخراج الكود مرتبة من الأكثر دقة للأقل
    _CODE_REGEXPS = [
        re.compile(
            r"(?i)(?:code|رمز|كود|verification|verify|otp|pin|password|code is|your code)"
            r"\s*[:\-]?\s*([0-9]{4,8})"
        ),
        re.compile(r"\b([0-9]{5,8})\b"),
        re.compile(r"(?<!\d)([0-9]{4,8})(?!\d)"),
    ]

    def _smart_code(txt: str) -> str:
        clean = re.sub(r"[^\w\s\u0600-\u06FF:،-]", " ", txt)
        for rx in _CODE_REGEXPS:
            m = rx.search(clean)
            if m:
                c = m.group(1)
                # تخطّي السنوات مثل 2023 / 1998
                if re.match(r"^(19|20)\d{2}$", c):
                    continue
                return c
        return ""

    for sender_raw, message_raw, time_raw in matched:
        msg_text = _strip_html_text(message_raw)
        if not msg_text:
            continue
        entries.append({
            "sender":  _strip_html_text(sender_raw),
            "message": msg_text,
            "time":    _strip_html_text(time_raw),
            "code":    _smart_code(msg_text),
        })

    return entries

def _extract_code_from_text(raw_text: str) -> str:
    text_value = _strip_html_text(raw_text or '')
    if not text_value:
        return ''
    patterns = [
        re.compile(
            r"(?i)(?:code|رمز|كود|verification|verify|otp|pin|password|code is|your code)"
            r"\s*[:\-]?\s*([0-9]{4,8})"
        ),
        re.compile(r"([0-9]{5,8})"),
        re.compile(r"(?<!\d)([0-9]{4,8})(?!\d)"),
    ]
    clean = re.sub(r"[^\w\s\u0600-\u06FF:،-]", " ", text_value)
    for rx in patterns:
        match = rx.search(clean)
        if not match:
            continue
        code_value = str(match.group(1) or '').strip()
        if re.match(r"^(19|20)\d{2}$", code_value):
            continue
        return code_value
    return ''


def _platform_hint_matches(candidate_platform: str, platform_hint: str = '') -> bool:
    hint_value = _normalize_platform(platform_hint)
    if not hint_value:
        return True
    candidate_value = _normalize_platform(candidate_platform)
    if candidate_value == hint_value:
        return True
    hint_key = _platform_alias_key(hint_value)
    candidate_key = _platform_alias_key(candidate_value)
    if not candidate_key:
        return False
    return hint_key in candidate_key or candidate_key in hint_key


def _lookup_cached_code_for_number(number: str, platform_hint: str = '') -> Optional[Dict]:
    target = _normalize_number(number)
    if not target:
        return None
    candidates = []
    for item in list(numbers_db.get('numbers', [])) if isinstance(numbers_db, dict) else []:
        if _normalize_number(item.get('number', '')) != target:
            continue
        if platform_hint and not _platform_hint_matches(str(item.get('platform', '')), platform_hint):
            continue
        message_text = str(item.get('last_sms') or item.get('message') or item.get('sms') or '').strip()
        code_value = str(item.get('last_code') or item.get('code') or '').strip() or _extract_code_from_text(message_text)
        if not code_value:
            continue
        candidates.append({
            'number': target,
            'platform': _normalize_platform(item.get('platform', '') or platform_hint or GENERAL_PLATFORM_NAME),
            'code': code_value,
            'message': message_text,
            'time': str(item.get('last_code_time') or item.get('last_checked_at') or item.get('added_at') or '').strip(),
            'source': 'bot_cache',
        })
    if not candidates:
        return None
    candidates.sort(key=lambda row: len(str(row.get('time') or '')), reverse=True)
    return candidates[0]


def _cache_code_for_number(number: str, platform_hint: str, payload: Dict) -> None:
    target = _normalize_number(number)
    if not target or not isinstance(numbers_db, dict):
        return
    code_value = str((payload or {}).get('code') or '').strip()
    message_text = str((payload or {}).get('text') or (payload or {}).get('message') or '').strip()
    time_value = str((payload or {}).get('date') or (payload or {}).get('created_at') or (payload or {}).get('time') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).strip()
    if not code_value:
        return

    changed = False
    for bucket_key in ('numbers', 'general_numbers'):
        bucket = numbers_db.get(bucket_key, []) if isinstance(numbers_db.get(bucket_key, []), list) else []
        for item in bucket:
            if _normalize_number(item.get('number', '')) != target:
                continue
            if platform_hint and not _platform_hint_matches(str(item.get('platform', '')), platform_hint):
                continue
            item['last_code'] = code_value
            item['code'] = code_value
            if message_text:
                item['last_sms'] = message_text
                item['sms'] = message_text
            item['last_code_time'] = time_value
            item['last_checked_at'] = time_value
            item['code_source'] = str((payload or {}).get('source') or 'runtime_check')
            changed = True
    if changed:
        try:
            _save_numbers()
        except Exception as cache_err:
            logger.warning(f'تعذر حفظ آخر كود للرقم {target}: {cache_err}')


def _extract_live_code_rows_from_payload(payload: Any, source: str = 'live_payload') -> List[Dict]:
    rows: List[Dict] = []
    seen = set()
    number_keys = ('number', 'Number', 'phone', 'mobile', 'msisdn', 'full_number', 'tel', 'did', 'cli', 'line')
    message_keys = ('Msg', 'msg', 'message', 'sms', 'text', 'body', 'content', 'last_sms')
    time_keys = ('time', 'Time', 'date', 'created_at', 'createdAt', 'updated_at', 'receive_time', 'received_at', 'sent_at')

    def _row_numbers(raw_row: Dict[str, Any]) -> List[str]:
        found: List[str] = []
        local_seen = set()

        def _push(candidate: Any) -> None:
            normalized = _normalize_number(str(candidate or ''))
            digits = re.sub(r'\D', '', normalized)
            if not normalized or len(digits) < 8 or len(digits) > 15:
                return
            if normalized in local_seen:
                return
            local_seen.add(normalized)
            found.append(normalized)

        for key in number_keys:
            if key in raw_row:
                _push(raw_row.get(key))
        for value in raw_row.values():
            if isinstance(value, str):
                for candidate in _extract_phone_candidates_from_text(value):
                    _push(candidate)
        return found

    def _row_message(raw_row: Dict[str, Any]) -> str:
        for key in message_keys:
            value = str(raw_row.get(key) or '').strip()
            if value:
                return value
        for value in raw_row.values():
            if not isinstance(value, str):
                continue
            code_value = _extract_code_from_text(value)
            if code_value:
                return value.strip()
        return ''

    def _row_time(raw_row: Dict[str, Any]) -> str:
        for key in time_keys:
            value = str(raw_row.get(key) or '').strip()
            if value:
                return value
        return ''

    def _append(raw_row: Dict[str, Any]) -> None:
        numbers = _row_numbers(raw_row)
        if not numbers:
            return
        message_text = _row_message(raw_row)
        code_value = _extract_code_from_text(message_text)
        if not code_value:
            return
        platform_name = _route_platform_for_site_row(raw_row, fallback=raw_row.get('Sender', '') or raw_row.get('sender', '') or raw_row.get('service', '') or raw_row.get('platform', '') or GENERAL_PLATFORM_NAME)
        time_value = _row_time(raw_row)
        for normalized in numbers:
            key = (normalized, code_value, platform_name, message_text)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'number': normalized,
                'platform': platform_name,
                'service': platform_name,
                'code': code_value,
                'message': message_text,
                'time': time_value,
                'source': source,
            })

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            _append(node)
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)

    _walk(payload)
    return rows


def _extract_live_code_rows_from_html(page_html: str, source: str = 'live_html') -> List[Dict]:
    rows: List[Dict] = []
    seen = set()
    blocks = re.findall(r'<tr\b[^>]*>.*?</tr>', page_html or '', flags=re.IGNORECASE | re.DOTALL)
    if not blocks:
        blocks = re.findall(r'<li\b[^>]*>.*?</li>', page_html or '', flags=re.IGNORECASE | re.DOTALL)
    if not blocks:
        blocks = re.findall(r'<div\b[^>]*>.*?</div>', page_html or '', flags=re.IGNORECASE | re.DOTALL)
    for block in blocks[:1500]:
        numbers = _extract_phone_candidates_from_text(block)
        if not numbers:
            continue
        text_value = _strip_html_text(block)
        code_value = _extract_code_from_text(text_value)
        if not code_value:
            continue
        platform_name = _guess_platform_from_payload(text_value) or GENERAL_PLATFORM_NAME
        key = (numbers[0], code_value, platform_name, text_value)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            'number': numbers[0],
            'platform': platform_name,
            'service': platform_name,
            'code': code_value,
            'message': text_value,
            'time': '',
            'source': source,
        })
    return rows


def _fetch_latest_live_code_for_number(number: str, platform_hint: str = '') -> Optional[Dict]:
    target = _normalize_number(number)
    if not target:
        return None

    hint = _normalize_platform(platform_hint)
    collected: List[Dict] = []

    try:
        session = _build_site_session()
    except Exception as session_err:
        logger.warning(f'تعذر تجهيز جلسة فحص الكود للرقم {target}: {session_err}')
        return None

    page_tokens: Dict[str, str] = {}
    page_jobs = [
        ('my_sms', f'{SITE_URL}/portal/live/my_sms'),
        ('test_system', f'{SITE_URL}/portal/live/test-system'),
    ]
    for label, page_url in page_jobs:
        try:
            page_resp = session.get(page_url, timeout=20, allow_redirects=True)
            if not _is_authenticated_response(page_resp):
                continue
            page_html = getattr(page_resp, 'text', '') or ''
            page_tokens[label] = _extract_csrf_token(page_html) or ''
            collected.extend(_extract_live_code_rows_from_html(page_html, source=f'{label}_page'))
        except Exception as page_err:
            logger.debug(f'live code page probe failed for {label}: {page_err}')

    ajax_jobs = [
        ('test_system_ajax', f'{SITE_URL}/portal/live/test-system/get', 'post', page_tokens.get('test_system', ''), f'{SITE_URL}/portal/live/test-system'),
        ('my_sms_get', f'{SITE_URL}/portal/live/my_sms/get', 'post', page_tokens.get('my_sms', ''), f'{SITE_URL}/portal/live/my_sms'),
        ('my_sms_data', f'{SITE_URL}/portal/live/my_sms/data', 'post', page_tokens.get('my_sms', ''), f'{SITE_URL}/portal/live/my_sms'),
        ('my_sms_list', f'{SITE_URL}/portal/live/my_sms/list', 'post', page_tokens.get('my_sms', ''), f'{SITE_URL}/portal/live/my_sms'),
        ('my_sms_table', f'{SITE_URL}/portal/live/my_sms/table', 'post', page_tokens.get('my_sms', ''), f'{SITE_URL}/portal/live/my_sms'),
    ]
    for label, endpoint, method, token, referer in ajax_jobs:
        try:
            headers = {
                'Referer': referer,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/plain, */*',
            }
            data = {'_token': token} if token else {}
            if method == 'post':
                resp = session.post(endpoint, data=data, headers=headers, timeout=20, allow_redirects=True)
            else:
                resp = session.get(endpoint, headers=headers, timeout=20, allow_redirects=True)
            if resp.status_code != 200:
                continue
            content_type = (resp.headers.get('content-type', '') or '').lower()
            if 'json' in content_type:
                try:
                    payload = resp.json()
                except Exception:
                    payload = None
                if payload is not None:
                    collected.extend(_extract_live_code_rows_from_payload(payload, source=label))
            else:
                collected.extend(_extract_live_code_rows_from_html(getattr(resp, 'text', '') or '', source=label))
        except Exception as ajax_err:
            logger.debug(f'live code ajax probe failed for {label}: {ajax_err}')

    if not collected:
        return None

    exact_platform: List[Dict] = []
    same_number: List[Dict] = []
    target_digits = target.lstrip('+')
    for item in collected:
        item_number = _normalize_number(item.get('number', ''))
        if item_number.lstrip('+') != target_digits:
            continue
        normalized_item = dict(item)
        normalized_item['number'] = item_number
        if hint and _platform_hint_matches(str(item.get('platform', '') or item.get('service', '')), hint):
            exact_platform.append(normalized_item)
        else:
            same_number.append(normalized_item)

    picked = exact_platform[0] if exact_platform else (same_number[0] if same_number else None)
    if not picked:
        return None
    picked['platform'] = _normalize_platform(picked.get('platform', '') or picked.get('service', '') or hint or GENERAL_PLATFORM_NAME)
    return picked

def _fetch_latest_sms_for_number(number: str, platform_hint: str = "") -> Optional[Dict]:
    target = _normalize_number(number)
    if not target:
        return None

    live_candidate = _fetch_latest_live_code_for_number(target, platform_hint)
    if live_candidate:
        _cache_code_for_number(target, platform_hint, live_candidate)
        return live_candidate

    try:
        session = _build_site_session()
        session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{SITE_URL}/portal/sms/received",
        })
        page_resp = session.get(f"{SITE_URL}/portal/sms/received", timeout=20)
        csrf = _extract_csrf_token(getattr(page_resp, "text", ""))
        if not csrf:
            logger.warning("تعذر استخراج CSRF token من صفحة الرسائل")
        else:
            today = datetime.date.today()
            windows = [7, 30, 90]
            hint = _normalize_platform(platform_hint).lower() if platform_hint else ""

            for days in windows:
                start = today - datetime.timedelta(days=days)
                end = today
                summary_resp = session.post(
                    f"{SITE_URL}/portal/sms/received/getsms",
                    data={"from": start.isoformat(), "to": end.isoformat(), "_token": csrf},
                    timeout=30,
                )
                if summary_resp.status_code != 200:
                    continue

                ranges = _extract_ranges_from_summary(summary_resp.text)
                preferred = [r for r in ranges if hint and hint in r.lower()]
                ordered_ranges = preferred + [r for r in ranges if r not in preferred]

                for range_name in ordered_ranges:
                    range_resp = session.post(
                        f"{SITE_URL}/portal/sms/received/getsms/number",
                        data={
                            "_token": csrf,
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "range": range_name,
                        },
                        timeout=30,
                    )
                    if range_resp.status_code != 200:
                        continue

                    available_numbers = _extract_number_rows(range_resp.text)
                    matched_number = None
                    for candidate in available_numbers:
                        candidate_digits = candidate.lstrip("+")
                        if candidate_digits == target.lstrip("+"):
                            matched_number = candidate_digits
                            break
                    if not matched_number:
                        continue

                    sms_resp = session.post(
                        f"{SITE_URL}/portal/sms/received/getsms/number/sms",
                        data={
                            "_token": csrf,
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "Number": matched_number,
                            "Range": range_name,
                        },
                        timeout=30,
                    )
                    if sms_resp.status_code != 200:
                        continue

                    entries = _extract_sms_entries(sms_resp.text)
                    if entries:
                        latest = entries[0]
                        latest.update({
                            "number": matched_number,
                            "range": range_name,
                            "date_from": start.isoformat(),
                            "date_to": end.isoformat(),
                            "platform": _platform_label_loose(range_name) or _normalize_platform(platform_hint or range_name) or GENERAL_PLATFORM_NAME,
                            "source": "portal_sms_received",
                        })
                        _cache_code_for_number(target, platform_hint, latest)
                        return latest
    except Exception as sms_err:
        logger.warning(f"فشل فحص الكود للرقم {number}: {sms_err}")

    cached_candidate = _lookup_cached_code_for_number(target, platform_hint)
    if cached_candidate:
        return cached_candidate

    return None

DEFAULT_PLATFORMS = [
    "WhatsApp", "Telegram", "TikTok", "Instagram",
    "Facebook", "Twitter", "Snapchat", "Line",
    "WeChat", "Viber", "Discord", "Gmail",
    "Hotmail", "Yahoo", "Microsoft", "Apple",
    "Amazon", "Netflix", "Uber", "PayPal",
]

PLATFORM_CANONICAL_ALIASES = {
    "whatsapp": "WhatsApp",
    "whats app": "WhatsApp",
    "واتساب": "WhatsApp",
    "واتس اب": "WhatsApp",
    "telegram": "Telegram",
    "تيليجرام": "Telegram",
    "تلجرام": "Telegram",
    "facebook": "Facebook",
    "فيسبوك": "Facebook",
    "فيس بوك": "Facebook",
    "instagram": "Instagram",
    "insta": "Instagram",
    "انستا": "Instagram",
    "انستغرام": "Instagram",
    "انستجرام": "Instagram",
    "انستقرام": "Instagram",
    "tiktok": "TikTok",
    "tik tok": "TikTok",
    "تيك توك": "TikTok",
    "تيكتوك": "TikTok",
}

dynamic_platforms: List[str] = list(DEFAULT_PLATFORMS)

PLATFORM_BLACKLIST = {
    "profile", "logout", "reload", "dashboard", "client system",
    "client active sms", "my numbers", "my sms statistics", "test system",
    "test active sms", "test numbers", "sms test history", "invoices",
    "my invoices", "invoices archive", "customer care", "online now",
    "account code", "details", "action", "rates", "limit by range",
    "sid/range limit", "sid→did limit",
}

def _platform_alias_key(value: str) -> str:
    key = str(value or "").strip().lower()
    key = key.replace("_", " ").replace("-", " ").replace("/", " ")
    key = re.sub(r"\s+", " ", key)
    return key

def _guess_platform_from_payload(*values) -> str:
    scanned_text = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, dict):
            iterable = list(value.values())
        elif isinstance(value, (list, tuple, set)):
            iterable = list(value)
        else:
            iterable = [value]

        for part in iterable:
            text_value = _strip_html_text(str(part or "")).strip()
            if not text_value:
                continue
            scanned_text.append(text_value)
            direct = _clean_platform_name(text_value)
            if direct:
                return direct
            alias_key = _platform_alias_key(text_value)
            for alias, canonical in PLATFORM_CANONICAL_ALIASES.items():
                if alias in alias_key:
                    return canonical

    combined = " ".join(scanned_text)
    direct = _clean_platform_name(combined)
    if direct:
        return direct
    alias_key = _platform_alias_key(combined)
    for alias, canonical in PLATFORM_CANONICAL_ALIASES.items():
        if alias in alias_key:
            return canonical
    return ""

def _smart_scrape_homepage() -> dict:
    """
    يسحب صفحة الحساب/الرئيسية ويستخرج:
    - قائمة المنصات المدعومة (من نصوص الصفحة)
    - أرقام هاتف إن وُجدت
    يرجع: {"platforms": [...], "numbers": [...]}
    """
    result = {"platforms": [], "numbers": []}
    try:
        from bs4 import BeautifulSoup

        session = _build_site_session()

        # الصفحات المرشحة للسحب
        candidate_pages = [
            f"{SITE_URL}/portal/numbers",
            f"{SITE_URL}/portal/live/my_sms",
            f"{SITE_URL}/portal/sms/received",
            f"{SITE_URL}/portal/profile",
            f"{SITE_URL}/portal",
            f"{SITE_URL}/",
        ]

        soup_obj = None
        for page_url in candidate_pages:
            try:
                resp = session.get(page_url, timeout=12)
                if resp.status_code == 200 and len(resp.text) > 200:
                    soup_obj = BeautifulSoup(resp.text, "html.parser")
                    logger.info(f"🌐 تم سحب الصفحة: {page_url}")
                    break
            except Exception as page_err:
                logger.warning(f"scrape page {page_url}: {page_err}")

        if not soup_obj:
            return result

        page_text = soup_obj.get_text(separator=" ", strip=True)

        # --- استخراج المنصات ---
        found_platforms = []
        # ① تحقق مما إذا كانت المنصة الافتراضية مذكورة في الصفحة
        for plat in DEFAULT_PLATFORMS:
            if plat.lower() in page_text.lower():
                found_platforms.append(plat)

        # ② ابحث في بطاقات/أزرار/عناصر data-* عن أسماء منصات
        for tag in soup_obj.find_all(True):
            for attr in ("data-service", "data-platform", "data-name"):
                val = tag.get(attr, "")
                if val and len(val) < 30:
                    found_platforms.append(val.strip().title())

        # ③ ابحث في نصوص الروابط والأزرار
        for tag in soup_obj.find_all(["a", "button", "span", "label"]):
            txt = tag.get_text(strip=True)
            if 3 <= len(txt) <= 20 and txt.replace(" ", "").isalpha():
                found_platforms.append(txt.title())

        result["platforms"] = list(dict.fromkeys(found_platforms))[:50]

        # --- استخراج أرقام الهاتف ---
        phone_pattern = re.compile(
            r"(\+?\d[\d\s\-]{8,16}\d)"
        )
        found_numbers = []
        for m in phone_pattern.finditer(page_text):
            num = re.sub(r"[\s\-]", "", m.group(0))
            if 8 <= len(num) <= 16:
                found_numbers.append(num)

        # أيضاً من خصائص data-phone / data-number
        for tag in soup_obj.find_all(True):
            for attr in ("data-phone", "data-number", "data-mobile"):
                val = tag.get(attr, "")
                if val and re.match(r"\+?\d{7,15}$", val.strip()):
                    found_numbers.append(val.strip())

        result["numbers"] = list(dict.fromkeys(found_numbers))  # بلا حد
        logger.info(
            f"📊 الصفحة: {len(result['platforms'])} منصة، "
            f"{len(result['numbers'])} رقم"
        )

    except ImportError:
        logger.error("❌ beautifulsoup4 غير مثبت! شغّل: pip install beautifulsoup4")
    except Exception as e:
        logger.error(f"_smart_scrape_homepage: {e}")

    return result

def _fetch_numbers_from_homepage_scrape() -> List[Dict]:
    """Fallback مرن لاستخراج الأرقام من الصفحة الرئيسية/البوابة عند تغيّر واجهات AJAX."""
    payload = _smart_scrape_homepage() or {}
    numbers = list(payload.get("numbers") or [])
    platforms = [p for p in (payload.get("platforms") or []) if str(p or "").strip()]
    guessed_platform = _normalize_platform(platforms[0]) if platforms else GENERAL_PLATFORM_NAME
    rows: List[Dict] = []
    for raw_number in numbers:
        item = _enrich_number_item({
            'number': raw_number,
            'platform': guessed_platform or GENERAL_PLATFORM_NAME,
            'site_section': SITE_ADD_SOURCE_LABEL,
            'source': 'homepage_scrape',
            'added_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'raw_platform': guessed_platform or GENERAL_PLATFORM_NAME,
        })
        if item:
            rows.append(item)
    return _dedupe_numbers(rows)

def _portal_numbers_datatable_params(length: int = 200, start: int = 0, draw: int = 1) -> dict:
    return {
        "draw": str(max(1, int(draw or 1))),
        "start": str(max(0, int(start or 0))),
        "length": str(max(1, int(length or 200))),
        "columns[0][data]": "number_id",
        "columns[0][name]": "id",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "false",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",
        "columns[1][data]": "Number",
        "columns[1][name]": "Number",
        "columns[1][searchable]": "true",
        "columns[1][orderable]": "true",
        "columns[1][search][value]": "",
        "columns[1][search][regex]": "false",
        "columns[2][data]": "range",
        "columns[2][name]": "range",
        "columns[2][searchable]": "true",
        "columns[2][orderable]": "true",
        "columns[2][search][value]": "",
        "columns[2][search][regex]": "false",
        "columns[3][data]": "A2P",
        "columns[3][name]": "A2P",
        "columns[3][searchable]": "true",
        "columns[3][orderable]": "true",
        "columns[3][search][value]": "",
        "columns[3][search][regex]": "false",
        "columns[4][data]": "LimitA2P",
        "columns[4][name]": "LimitA2P",
        "columns[4][searchable]": "true",
        "columns[4][orderable]": "true",
        "columns[4][search][value]": "",
        "columns[4][search][regex]": "false",
        "columns[5][data]": "limit_cli_a2p",
        "columns[5][name]": "limit_cli_a2p",
        "columns[5][searchable]": "true",
        "columns[5][orderable]": "true",
        "columns[5][search][value]": "",
        "columns[5][search][regex]": "false",
        "columns[6][data]": "limit_cli_did_a2p",
        "columns[6][name]": "limit_cli_did_a2p",
        "columns[6][searchable]": "true",
        "columns[6][orderable]": "true",
        "columns[6][search][value]": "",
        "columns[6][search][regex]": "false",
        "columns[7][data]": "action",
        "columns[7][name]": "action",
        "columns[7][searchable]": "false",
        "columns[7][orderable]": "false",
        "columns[7][search][value]": "",
        "columns[7][search][regex]": "false",
        "order[0][column]": "1",
        "order[0][dir]": "desc",
        "search[value]": "",
        "search[regex]": "false",
    }


def _fetch_numbers_from_portal(session: requests.Session) -> List[Dict]:
    collected: List[Dict] = []
    seen_numbers = set()
    endpoint = f"{SITE_URL}/portal/numbers"
    page_size = max(100, min(1000, int(_get("SITE_ADD_PORTAL_PAGE_SIZE", "300") or "300")))
    max_pages = max(1, min(25, int(_get("SITE_ADD_PORTAL_MAX_PAGES", "8") or "8")))
    soft_timeout = max(6.0, float(_get("SITE_ADD_PORTAL_SOFT_TIMEOUT_SECONDS", "12") or "12"))
    started_at = time.time()
    try:
        for page_idx in range(max_pages):
            if (time.time() - started_at) >= soft_timeout:
                logger.warning(f"Portal datatable fetch stopped after {soft_timeout}s to keep bot responsive")
                break
            start = page_idx * page_size
            resp = session.get(
                endpoint,
                params=_portal_numbers_datatable_params(page_size, start=start, draw=page_idx + 1),
                headers={
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=min(10, max(6, int(soft_timeout))),
            )
            logger.info(f"Portal datatable {endpoint} page={page_idx + 1} start={start} → {resp.status_code}")
            if resp.status_code != 200 or "json" not in (resp.headers.get("content-type", "").lower()):
                break

            payload = resp.json()
            rows = payload.get("data", []) or []
            if not rows:
                break

            for item in rows:
                if not isinstance(item, dict):
                    continue
                number = _normalize_number(str(item.get("Number") or item.get("number") or item.get("phone") or "").strip())
                if not number or number in seen_numbers:
                    continue
                seen_numbers.add(number)
                platform = _guess_platform_from_payload(
                    item.get("range"),
                    item.get("platform"),
                    item.get("service"),
                    item.get("A2P"),
                    item,
                ) or GENERAL_PLATFORM_NAME
                collected.append({
                    "number": number,
                    "platform": platform,
                    "site_section": str(item.get("range") or item.get("platform") or item.get("service") or "").strip(),
                    "source": "portal_json",
                    "added_at": time.ctime(),
                    "country_name": str(item.get("country_name") or item.get("country") or item.get("country_label") or "").strip(),
                    "country_name_ar": str(item.get("country_name_ar") or item.get("country_name") or item.get("country") or item.get("country_label") or "").strip(),
                    "country": str(item.get("country") or item.get("country_name") or "").strip(),
                    "country_flag": str(item.get("country_flag") or "").strip(),
                    "country_code": str(item.get("country_code") or item.get("countryCode") or "").strip(),
                })

            total_rows = int(payload.get("recordsFiltered") or payload.get("recordsTotal") or 0)
            if total_rows and (start + len(rows)) >= total_rows:
                break
            if len(rows) < page_size:
                break
    except Exception as portal_err:
        logger.warning(f"Portal datatable fetch failed: {portal_err}")
    return _dedupe_numbers(collected)

def _find_newly_added_numbers(old_items: List[Dict], new_items: List[Dict]) -> List[Dict]:
    old_keys = {_number_item_key(item) for item in old_items if _number_item_key(item)[0]}
    fresh = []
    seen = set()
    for item in _dedupe_numbers(new_items):
        key = _number_item_key(item)
        if not key[0] or key in old_keys or key in seen:
            continue
        fresh.append(item)
        seen.add(key)
    return fresh

def _source_label_for_new_numbers(source: str) -> str:
    normalized = str(source or '').strip().lower()
    mapping = {
        'manual': 'إضافة يدوية',
        'sync': 'مزامنة تلقائية',
        'site': 'إضافة من الموقع',
        'site_picker': 'إضافة من الموقع',
        'site_add': 'إضافة من الموقع',
    }
    return mapping.get(normalized, normalized or 'غير معروف')


def _notify_users_about_new_numbers(new_items: List[Dict], source: str = "sync"):
    if not new_items:
        return
    platform_summary: Dict[str, int] = {}
    country_summary: Dict[str, int] = {}
    for item in new_items:
        platform = _normalize_platform(item.get("platform", "General")) or "General"
        platform_summary[platform] = platform_summary.get(platform, 0) + 1

        country_info = item.get('country') if isinstance(item.get('country'), dict) else {}
        if not country_info:
            country_info = _get_country_info(item.get('number', ''))
        country_label = f"{country_info.get('flag', '🌐')} {country_info.get('name', 'غير محددة')}"
        country_summary[country_label] = country_summary.get(country_label, 0) + 1

    lines = [
        "📢 تم إضافة أرقام جديدة داخل البوت!",
        "",
        f"🆕 عدد الأرقام الجديدة: {len(new_items)}",
        f"🧭 المصدر: {_source_label_for_new_numbers(source)}",
        "",
        "📂 تفاصيل المنصات:",
    ]
    for platform, count in sorted(platform_summary.items()):
        lines.append(f"• {_display_platform_name(platform)}: {count} رقم")

    if country_summary:
        lines.extend(["", "🌍 تفاصيل الدول:"])
        ordered_countries = sorted(country_summary.items(), key=lambda pair: (-pair[1], pair[0]))
        preview_limit = 12
        for country_label, count in ordered_countries[:preview_limit]:
            lines.append(f"• {country_label}: {count} رقم")
        remaining = len(ordered_countries) - preview_limit
        if remaining > 0:
            lines.append(f"• +{remaining} دولة إضافية")

    lines.append("\nافتح /start أو اضغط على زر الأقسام المتاحة لاستعراضها.")
    text_value = "\n".join(lines)

    sent = failed = 0
    for uid in list(dict.fromkeys(users_db.get("users", []))):
        try:
            bot.send_message(uid, text_value)
            sent += 1
        except Exception:
            failed += 1
    log_event("NEW_NUMBERS_NOTIFY", {"count": len(new_items), "sent": sent, "failed": failed, "source": source})

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set it in your hosting environment variables.")

if not ADMIN_ID:
    logger.warning("ADMIN_ID is not set. Admin-only commands will not work correctly until you set ADMIN_ID.")

bot        = TeleBot(BOT_TOKEN, threaded=True, num_threads=BOT_WORKER_THREADS)

bot_active = True   # مفتاح تشغيل/إيقاف الاستجابة

_bot_username_cache = ""

def _get_bot_public_url(start_param: str = "channel_post") -> str:
    """يرجع رابط البوت العام لاستخدامه في أزرار القناة."""
    global _bot_username_cache
    try:
        if not _bot_username_cache:
            me = bot.get_me()
            _bot_username_cache = (getattr(me, "username", "") or "").strip()
        if not _bot_username_cache:
            return ""
        suffix = f"?start={urllib.parse.quote(str(start_param))}" if start_param else ""
        return f"https://t.me/{_bot_username_cache}{suffix}"
    except Exception as bot_link_err:
        logger.warning(f"تعذر جلب رابط البوت العام: {bot_link_err}")
        return ""

def _build_channel_post_markup() -> Optional[types.InlineKeyboardMarkup]:
    """يبني زرًا أسفل منشور القناة للدخول إلى البوت مباشرة."""
    bot_url = _get_bot_public_url()
    if not bot_url:
        return None
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🤖 دخول البوت", url=bot_url))
    return mk


def _build_test_channel_post_markup() -> Optional[types.InlineKeyboardMarkup]:
    """أزرار ستايل الصورة لقناة الاختبار الخاصة."""
    main_url = str(TEST_MAIN_CHANNEL_URL or "").strip()
    get_url = str(TEST_GET_NUMBER_URL or "").strip() or _get_bot_public_url()
    if not main_url and not get_url:
        return _build_channel_post_markup()
    mk = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    if main_url:
        buttons.append(types.InlineKeyboardButton(TEST_MAIN_BUTTON_TEXT, url=main_url))
    if get_url:
        buttons.append(types.InlineKeyboardButton(TEST_GET_BUTTON_TEXT, url=get_url))
    if not buttons:
        return None
    if len(buttons) == 1:
        mk.add(buttons[0])
    else:
        mk.row(*buttons[:2])
    return mk

def is_admin(m) -> bool:
    return m.from_user.id == ADMIN_ID

def _check_subscription(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("creator", "administrator", "member")
    except Exception:
        return False

def _require_subscription(message) -> bool:
    if _check_subscription(message.from_user.id):
        return True
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        f"📢 اشترك في {DEVELOPER_CHANNEL}",
        url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME}",
    ))
    mk.add(types.InlineKeyboardButton("✅ تحققت من اشتراكي", callback_data="check_sub"))
    bot.reply_to(
        message,
        f"⚠️ يجب الاشتراك في قناة المطور أولاً للاستفادة من خدمات البوت.\n\nالقناة: {DEVELOPER_CHANNEL}",
        reply_markup=mk,
    )
    return False

COUNTRY_PHONE_MAP = [
    # ─── الخليج والشرق الأوسط ───
    ("+966",  "السعودية",        "🇸🇦"),
    ("+971",  "الإمارات",         "🇦🇪"),
    ("+965",  "الكويت",           "🇰🇼"),
    ("+974",  "قطر",              "🇶🇦"),
    ("+973",  "البحرين",          "🇧🇭"),
    ("+968",  "عُمان",            "🇴🇲"),
    ("+967",  "اليمن",            "🇾🇪"),
    ("+962",  "الأردن",           "🇯🇴"),
    ("+964",  "العراق",           "🇮🇶"),
    ("+963",  "سوريا",            "🇸🇾"),
    ("+961",  "لبنان",            "🇱🇧"),
    ("+970",  "فلسطين",           "🇵🇸"),
    ("+972",  "إسرائيل",          "🇮🇱"),
    # ─── أفريقيا ───
    ("+20",   "مصر",              "🇪🇬"),
    ("+212",  "المغرب",           "🇲🇦"),
    ("+213",  "الجزائر",          "🇩🇿"),
    ("+216",  "تونس",             "🇹🇳"),
    ("+218",  "ليبيا",            "🇱🇾"),
    ("+249",  "السودان",          "🇸🇩"),
    ("+252",  "الصومال",          "🇸🇴"),
    ("+234",  "نيجيريا",          "🇳🇬"),
    ("+233",  "غانا",             "🇬🇭"),
    ("+254",  "كينيا",            "🇰🇪"),
    ("+255",  "تنزانيا",          "🇹🇿"),
    ("+256",  "أوغندا",           "🇺🇬"),
    ("+251",  "إثيوبيا",          "🇪🇹"),
    ("+260",  "زامبيا",           "🇿🇲"),
    ("+263",  "زيمبابوي",         "🇿🇼"),
    ("+27",   "جنوب أفريقيا",    "🇿🇦"),
    ("+237",  "الكاميرون",        "🇨🇲"),
    ("+243",  "الكونغو",          "🇨🇩"),
    ("+221",  "السنغال",          "🇸🇳"),
    # ─── أوروبا ───
    ("+44",   "المملكة المتحدة", "🇬🇧"),
    ("+49",   "ألمانيا",          "🇩🇪"),
    ("+33",   "فرنسا",            "🇫🇷"),
    ("+34",   "إسبانيا",          "🇪🇸"),
    ("+39",   "إيطاليا",          "🇮🇹"),
    ("+31",   "هولندا",           "🇳🇱"),
    ("+32",   "بلجيكا",           "🇧🇪"),
    ("+41",   "سويسرا",           "🇨🇭"),
    ("+43",   "النمسا",           "🇦🇹"),
    ("+46",   "السويد",           "🇸🇪"),
    ("+47",   "النرويج",          "🇳🇴"),
    ("+45",   "الدنمارك",         "🇩🇰"),
    ("+358",  "فنلندا",           "🇫🇮"),
    ("+48",   "بولندا",           "🇵🇱"),
    ("+351",  "البرتغال",         "🇵🇹"),
    ("+30",   "اليونان",          "🇬🇷"),
    ("+420",  "التشيك",           "🇨🇿"),
    ("+36",   "المجر",            "🇭🇺"),
    ("+40",   "رومانيا",          "🇷🇴"),
    ("+380",  "أوكرانيا",         "🇺🇦"),
    ("+7",    "روسيا/كازاخستان", "🇷🇺"),
    # ─── آسيا ───
    ("+90",   "تركيا",            "🇹🇷"),
    ("+98",   "إيران",            "🇮🇷"),
    ("+92",   "باكستان",          "🇵🇰"),
    ("+91",   "الهند",            "🇮🇳"),
    ("+94",   "سريلانكا",         "🇱🇰"),
    ("+880",  "بنغلاديش",         "🇧🇩"),
    ("+977",  "نيبال",            "🇳🇵"),
    ("+86",   "الصين",            "🇨🇳"),
    ("+81",   "اليابان",          "🇯🇵"),
    ("+82",   "كوريا الجنوبية",  "🇰🇷"),
    ("+62",   "إندونيسيا",        "🇮🇩"),
    ("+60",   "ماليزيا",          "🇲🇾"),
    ("+63",   "الفلبين",          "🇵🇭"),
    ("+66",   "تايلاند",          "🇹🇭"),
    ("+84",   "فيتنام",           "🇻🇳"),
    ("+65",   "سنغافورة",         "🇸🇬"),
    ("+93",   "أفغانستان",        "🇦🇫"),
    ("+995",  "جورجيا",           "🇬🇪"),
    ("+994",  "أذربيجان",         "🇦🇿"),
    ("+374",  "أرمينيا",          "🇦🇲"),
    ("+996",  "قيرغيزستان",       "🇰🇬"),
    ("+998",  "أوزبكستان",        "🇺🇿"),
    # ─── أمريكا ───
    ("+1",    "أمريكا/كندا",     "🇺🇸"),
    ("+52",   "المكسيك",          "🇲🇽"),
    ("+55",   "البرازيل",         "🇧🇷"),
    ("+54",   "الأرجنتين",        "🇦🇷"),
    ("+57",   "كولومبيا",         "🇨🇴"),
    ("+56",   "تشيلي",            "🇨🇱"),
    ("+51",   "بيرو",             "🇵🇪"),
    ("+58",   "فنزويلا",          "🇻🇪"),
    ("+593",  "الإكوادور",        "🇪🇨"),
    # ─── أوقيانوسيا ───
    ("+61",   "أستراليا",         "🇦🇺"),
    ("+64",   "نيوزيلندا",        "🇳🇿"),
]

def _guess_country_from_number(number: str) -> str:
    """يرجع اسم الدولة فقط (للتوافق مع الكود القديم)."""
    return _get_country_info(number)["name"]

def _guess_country_flag(number: str) -> str:
    """يرجع علم الدولة فقط."""
    return _get_country_info(number)["flag"]

def _guess_country_with_flag(number: str) -> str:
    """يرجع علم + اسم الدولة معاً."""
    info = _get_country_info(number)
    return f"{info['flag']} {info['name']}"

def _chunked_send(chat_id: int, text_value: str, parse_mode: str = None):
    chunk = ""
    for line in text_value.splitlines(True):
        if len(chunk) + len(line) > 3500:
            bot.send_message(chat_id, chunk, parse_mode=parse_mode)
            chunk = ""
        chunk += line
    if chunk:
        bot.send_message(chat_id, chunk, parse_mode=parse_mode)

def _build_sections_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=2)
    platforms = _platform_picker_platforms()
    for idx, plat in enumerate(platforms):
        mk.add(types.InlineKeyboardButton(_platform_button_label(plat), callback_data=f"sec_{idx}"))
    return mk

DEMO_SERVICE_META = {
    "WhatsApp": {"icon": "💬", "label": "WhatsApp"},
    "Telegram": {"icon": "✈️", "label": "Telegram"},
    "Facebook": {"icon": "📘", "label": "Facebook"},
    "Instagram": {"icon": "📸", "label": "Instagram"},
}

def _build_all_country_samples() -> list:
    """يبني قائمة DEMO_COUNTRY_SAMPLES من COUNTRY_PHONE_MAP الشاملة."""
    samples = []
    for code, name, flag in COUNTRY_PHONE_MAP:
        key = code.lstrip("+").replace(" ", "_")
        samples.append({
            "key":  key,
            "name": name,
            "flag": flag,
            "code": code,
        })
    return samples

DEMO_COUNTRY_SAMPLES = _build_all_country_samples()

def _build_country_names_map() -> dict:
    """يبني قاموساً مرناً للبحث عن الدولة بالاسم أو الكود أو الاسم المنظّف."""
    names = {}

    def _put(token: str, payload: dict) -> None:
        token = re.sub(r'\s+', ' ', str(token or '').strip()).lower()
        if not token:
            return
        names[token] = dict(payload)

    for code, name, flag in COUNTRY_PHONE_MAP:
        digits_code = re.sub(r'\D', '', str(code or ''))
        key = digits_code or code.lstrip('+').replace(' ', '_')
        payload = {
            'name': name,
            'flag': flag,
            'code': code,
            'digits_code': digits_code,
            'key': key or 'unknown',
        }
        _put(code, payload)
        _put(code.lstrip('+'), payload)
        _put(key, payload)
        _put(name, payload)
        _put(str(name).replace('-', ' '), payload)
    return names
DEMO_COUNTRY_NAMES = _build_country_names_map()

def _country_counts_for_service(service: str) -> Dict[str, int]:
    results = {item["key"]: 0 for item in DEMO_COUNTRY_SAMPLES}
    for item in numbers_db.get("numbers", []):
        platform = _normalize_platform(item.get("platform", ""))
        if platform != service:
            continue
        info = _get_country_info(item.get("number", ""))
        key = info.get("code", "").lstrip("+").replace(" ", "_")
        if key in results:
            results[key] += 1
    return results

def _build_demo_services_markup() -> types.InlineKeyboardMarkup:
    counts = _service_counts()
    mk = types.InlineKeyboardMarkup(row_width=1)
    for service, meta in DEMO_SERVICE_META.items():
        label = f"{meta['icon']} {meta['label']} ({counts.get(service, 0)})"
        mk.add(types.InlineKeyboardButton(label, callback_data=f"svc_{service}"))
    return mk

def _build_demo_countries_markup(service: str) -> types.InlineKeyboardMarkup:
    counts = _country_counts_for_service(service)
    mk = types.InlineKeyboardMarkup(row_width=1)
    for item in DEMO_COUNTRY_SAMPLES:
        label = f"{item['flag']} {item['name']} ({item['code']}) ({counts.get(item['key'], 0)})"
        mk.add(types.InlineKeyboardButton(label, callback_data=f"ctry_{service}_{item['key']}"))
    mk.add(types.InlineKeyboardButton("رجوع", callback_data="demo_home"))
    return mk

def _send_or_edit(chat_id: int, text_value: str, reply_markup=None, message_id: Optional[int] = None, parse_mode: Optional[str] = None):
    if message_id:
        try:
            bot.edit_message_text(
                text_value,
                chat_id,
                message_id,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
            return
        except Exception:
            pass
    bot.send_message(
        chat_id,
        text_value,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )

def _send_demo_countries(chat_id: int, service: str, message_id: Optional[int] = None):
    meta = DEMO_SERVICE_META.get(service, {"icon": "📱", "label": service})
    text = (
        f"{meta['icon']} *{meta['label']}*\n\n"
        "اختر الدولة من القائمة تحت:\n"
        "— واجهة مشابهة للصورة مع زر رجوع —"
    )
    _send_or_edit(
        chat_id,
        text,
        reply_markup=_build_demo_countries_markup(service),
        message_id=message_id,
        parse_mode="Markdown",
    )

def _send_demo_country_card(chat_id: int, service: str, country_key: str, message_id: Optional[int] = None):
    meta = DEMO_SERVICE_META.get(service, {"icon": "📱", "label": service})
    country = next((item for item in DEMO_COUNTRY_SAMPLES if item["key"] == country_key), None)
    if not country:
        _send_demo_home(chat_id, message_id=message_id)
        return
    count = _country_counts_for_service(service).get(country_key, 0)
    text = (
        "═══《 MV 》═══\n\n"
        f"▪️ service: {meta['label']} {meta['icon']}\n"
        f"▪️ Country: {country['name']} {country['flag']}\n"
        f"▪️ Numbers available: {count}\n\n"
        f"🔗 {DEVELOPER_CHANNEL}\n\n"
        f"✅ تم فتح قسم {country['name']} بنجاح"
    )
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("رجوع للدول", callback_data=f"svc_{service}"))
    mk.add(types.InlineKeyboardButton("القائمة الرئيسية", callback_data="demo_home"))
    _send_or_edit(chat_id, text, reply_markup=mk, message_id=message_id)

def demo_home_callback(call):
    bot.answer_callback_query(call.id)
    _send_demo_home(call.message.chat.id, message_id=call.message.message_id)

def demo_service_callback(call):
    service = call.data[4:]
    if service not in DEMO_SERVICE_META:
        bot.answer_callback_query(call.id, "الخدمة غير متاحة", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _send_demo_countries(call.message.chat.id, service, message_id=call.message.message_id)

def demo_country_callback(call):
    payload = call.data[5:]
    try:
        service, country_key = payload.split("_", 1)
    except ValueError:
        bot.answer_callback_query(call.id, "البيانات غير صالحة", show_alert=True)
        return
    if service not in DEMO_SERVICE_META:
        bot.answer_callback_query(call.id, "الخدمة غير متاحة", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _send_demo_country_card(call.message.chat.id, service, country_key, message_id=call.message.message_id)

def _send_user_start_bundle(chat_id: int):
    bot.send_message(
        chat_id,
        _get_welcome_message(),
        reply_markup=_build_user_main_keyboard(),
    )

    def _async_send_sections():
        try:
            _send_demo_home(chat_id)
        except Exception as start_bundle_err:
            logger.exception(f"User start bundle failed: {start_bundle_err}")

    threading.Thread(target=_async_send_sections, daemon=True).start()

def cmd_start(message):
    uid = message.from_user.id
    if uid not in users_db["users"]:
        users_db["users"].append(uid)
        save_json(USERS_FILE, users_db)
        log_event("NEW_USER", {"user_id": uid})

    if not is_admin(message) and not _check_subscription(uid):
        mk_sub = types.InlineKeyboardMarkup()
        mk_sub.add(types.InlineKeyboardButton(
            f"📢 اشترك في {DEVELOPER_CHANNEL}",
            url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME}",
        ))
        mk_sub.add(types.InlineKeyboardButton("✅ تحققت من اشتراكي", callback_data="check_sub"))
        bot.send_message(
            message.chat.id,
            f"👋 أهلاً بك\n\nلاستخدام البوت لازم تشترك أولاً في قناة المطور: {DEVELOPER_CHANNEL}",
            reply_markup=mk_sub,
        )
        return
    if not is_admin(message):
        _send_user_start_bundle(message.chat.id)
        return

    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("➕ إضافة يدوية")
    mk.add("🗑️ حذف الأرقام", "📊 حالة البوت")
    mk.add("📢 إرسال للكل", "👥 المستخدمون")
    mk.add("📱 الأرقام المتوفرة", "📋 آخر الأحداث")
    mk.add("⛔ إيقاف البوت", "▶️ تشغيل البوت")
    mk.add("📲 إرسال لواتساب", "🧹 تنظيف اللوجات")
    mk.add("📂 تحميل لوجات", "🔎 فحص الاتصال")
    mk.add("🛠️ لوحة المطور")

    bot.send_message(
        message.chat.id,
        (
            f"👋 أهلاً بك في النسخة الآمنة من البوت\n\n"
            f"👑 المطور: @{DEVELOPER_USERNAME}\n"
            f"📢 القناة: {DEVELOPER_CHANNEL}\n\n"
            f"📝 رسالة الترحيب الحالية:\n{_get_welcome_message()}\n\n"
            "استخدم الأزرار أدناه."
        ),
        reply_markup=mk,
    )

def sync_handler(message):
    bot.reply_to(message, "⛔ تم تعطيل الجلب من الموقع. إضافة الأرقام أصبحت يدوية فقط من داخل البوت.")

def add_manual_prompt(message):
    platforms = _platform_picker_platforms()
    mk = types.InlineKeyboardMarkup(row_width=2)
    for plat in platforms:
        mk.add(types.InlineKeyboardButton(plat, callback_data=f"admplt_{plat}"))

    prompt = bot.reply_to(
        message,
        "📝 اختار المنصة الأول من الأزرار تحت، وبعدها ابعت الأرقام كل رقم في سطر.\n\n"
        "أو تقدر تستخدم الصيغة القديمة: `الرقم:المنصة` لكل سطر.",
        parse_mode="Markdown",
        reply_markup=mk,
    )
    bot.register_next_step_handler(prompt, _process_manual_add)

def admin_platform_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    plat = _normalize_platform(call.data[7:])
    admin_pending_platform[call.from_user.id] = plat
    bot.answer_callback_query(call.id, f"تم اختيار منصة {plat}")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    bot.send_message(call.message.chat.id, f"✅ المنصة المختارة: *{plat}*\nابعت الأرقام الآن، كل رقم في سطر.", parse_mode="Markdown")

def clear_numbers(message):
    count = len(numbers_db["numbers"])
    numbers_db["numbers"] = []
    numbers_db["general_numbers"] = []
    save_json(NUMBERS_FILE, numbers_db)
    _invalidate_numbers_runtime_index()
    _refresh_dynamic_platforms()
    log_event("NUMBERS_CLEARED", {"deleted": count})
    bot.reply_to(message, f"🗑️ تم حذف {count} رقم.")


def status_handler(message):
    state   = "▶️ يعمل" if bot_active else "⛔ موقوف"
    wa_ok   = bool(WA_NUMBER_1 and WA_APIKEY_1)
    pending = _wa_retry_queue.qsize()
    uptime  = _get_uptime()
    text = (
        f"📊 *حالة البوت:*\n"
        f"🤖 الحالة: {state}\n"
        f"📱 الأرقام: {len(numbers_db['numbers'])}\n"
        f"🌐 المنصات: {len(dynamic_platforms)}\n"
        f"👥 المستخدمون: {len(users_db['users'])}\n"
        f"🧠 سرعة المعالجة: x{int(FAST_RESPONSE_MULTIPLIER)}\n"
        f"🧵 ثريدات البوت: {BOT_WORKER_THREADS}\n"
        f"💽 السعة البرمجية المستهدفة: {STORAGE_TARGET_GB} GB\n"
        f"📟 واتساب: {'✅ مفعّل' if wa_ok else '❌ غير مهيأ'}\n"
        f"📬 رسائل واتساب معلّقة: {pending}\n"
        f"⏱ وقت التشغيل: {uptime}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

def stop_handler(message):
    global bot_active
    bot_active = False
    log_event("BOT_PAUSED", {"by": message.from_user.id})
    bot.reply_to(message, "⛔ *تم إيقاف البوت مؤقتاً.*", parse_mode="Markdown")

def start_handler(message):
    global bot_active
    bot_active = True
    log_event("BOT_RESUMED", {"by": message.from_user.id})
    bot.reply_to(message, "▶️ *تم تشغيل البوت بنجاح!*", parse_mode="Markdown")

def broadcast_prompt(message):
    prompt = bot.reply_to(message, "📢 أرسل الرسالة للإذاعة:")
    bot.register_next_step_handler(prompt, _broadcast_exec)

def _broadcast_exec(message):
    ok = fail = 0
    for uid in users_db["users"]:
        try:
            bot.send_message(uid, message.text)
            ok += 1
        except Exception:
            fail += 1
    log_event("BROADCAST", {"sent": ok, "failed": fail})
    bot.send_message(
        ADMIN_ID,
        f"📢 الإذاعة انتهت:\n✅ نجاح: {ok}\n❌ فشل: {fail}",
    )

def users_handler(message):
    bot.reply_to(message, f"👥 المستخدمون المسجلون: *{len(users_db['users'])}*", parse_mode="Markdown")

def my_numbers(message):
    if not is_admin(message) and not _require_subscription(message):
        return
    if not is_admin(message):
        _send_demo_home(message.chat.id)
        return
    if not numbers_db["numbers"]:
        bot.reply_to(message, "📭 لا توجد بيانات متاحة حالياً.")
        return
    stats: dict = {}
    for n in numbers_db["numbers"]:
        plat = n.get("platform", "General")
        stats[plat] = stats.get(plat, 0) + 1
    text = "📱 الأقسام/العناصر المتوفرة حالياً:\n\n"
    for plat, cnt in stats.items():
        text += f"• {plat}: {cnt} عنصر\n"
    bot.send_message(message.chat.id, text)

def events_handler(message):
    last = events_db["events"][-10:]
    if not last:
        bot.reply_to(message, "📭 لا أحداث مسجّلة.")
        return
    text = "📋 *آخر 10 أحداث:*\n\n"
    for ev in reversed(last):
        ts = ev.get("timestamp", "")[:16]
        tp = ev.get("type", "")
        text += f"`{ts}` — {tp}\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def send_summary_wa(message):
    if not numbers_db["numbers"]:
        bot.reply_to(message, "📭 لا توجد أرقام.")
        return
    stats: dict = {}
    for n in numbers_db["numbers"]:
        p = n.get("platform", "General")
        stats[p] = stats.get(p, 0) + 1
    lines = [f"📊 ملخص الأرقام – {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    for plat, cnt in stats.items():
        lines.append(f"• {plat}: {cnt} رقم")
    lines.append(f"\nإجمالي: {len(numbers_db['numbers'])} رقم")
    text = "\n".join(lines)
    bot.reply_to(message, "⏳ جاري الإرسال…")
    ok = send_whatsapp(text, label="SUMMARY")
    bot.reply_to(message, "✅ تم الإرسال." if ok else "❌ فشل الإرسال، تحقق من إعدادات واتساب.")

def clean_logs(message):
    try:
        deleted = 0
        cutoff = time.time() - 7 * 24 * 3600  # أقدم من 7 أيام
        for f in LOGS_DIR.glob("*.log*"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
        log_event("LOGS_CLEANED", {"deleted_files": deleted})
        bot.reply_to(message, f"🧹 تم حذف {deleted} ملف لوج قديم.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

def download_logs(message):
    log_file = LOGS_DIR / "bot.log"
    if log_file.exists() and log_file.stat().st_size > 0:
        with open(log_file, "rb") as f:
            bot.send_document(
                message.chat.id, f,
                caption=f"📂 bot.log – {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
    else:
        bot.reply_to(message, "📭 ملف اللوج فارغ أو غير موجود.")

def check_connection(message):
    site_ok = "❌ غير متاح"
    portal_ok = "⚠️ غير مفحوص"
    cookies_ok = "⚠️ غير متوفرة"
    tg_ok = "❌ غير متاح"

    try:
        r = requests.get(SITE_URL, timeout=8, allow_redirects=True)
        site_ok = f"✅ {r.status_code}"
    except Exception as e:
        site_ok = f"❌ {type(e).__name__}: {e}"

    try:
        session = _build_site_session()
        cookies_ok = "✅ متوفرة" if getattr(session, "cookies", None) else "⚠️ غير متوفرة"
        portal_resp = session.get(f"{SITE_URL}/portal", timeout=12, allow_redirects=True)
        portal_ok = f"✅ {portal_resp.status_code}"
    except Exception as e:
        portal_ok = f"❌ {type(e).__name__}: {e}"

    try:
        me = bot.get_me()
        tg_ok = f"✅ @{getattr(me, 'username', '') or 'bot'}"
    except Exception as e:
        tg_ok = f"❌ {type(e).__name__}: {e}"

    text = (
        "🔎 <b>فحص الاتصال</b>\n\n"
        f"🌐 الموقع: {html.escape(str(site_ok))}\n"
        f"🧩 البوابة: {html.escape(str(portal_ok))}\n"
        f"🍪 الكوكيز: {html.escape(str(cookies_ok))}\n"
        f"🤖 تيليجرام: {html.escape(str(tg_ok))}\n"
        f"📟 واتساب أساسي: {html.escape('✅ مهيأ' if WA_NUMBER_1 else '⚠️ غير مهيأ')}\n"
        f"📟 واتساب احتياطي: {html.escape('✅ مهيأ' if WA_NUMBER_2 else '⚠️ غير مهيأ')}"
    )
    try:
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, text, parse_mode="HTML")

def _build_platform_picker_markup() -> types.InlineKeyboardMarkup:
    platforms = _user_visible_platforms()
    counts = _platform_counts_snapshot()
    mk = types.InlineKeyboardMarkup(row_width=2)
    if not platforms:
        mk.add(types.InlineKeyboardButton("✉️ مراسلة المطور", callback_data="contact_dev"))
        return mk
    for idx, platform in enumerate(platforms):
        label = _platform_button_label(platform, counts_map=counts)
        mk.add(types.InlineKeyboardButton(label, callback_data=f"plt_{idx}"))
    return mk

def _build_platform_country_markup(platform: str, page: int = 0) -> types.InlineKeyboardMarkup:
    normalized = _normalize_platform(platform)
    page = max(0, int(page or 0))
    cache_key = (normalized, page)
    with _country_markup_cache_lock:
        cached = _country_markup_cache.get(cache_key)
    if cached is not None:
        return cached

    countries = _country_groups_for_platform(normalized)
    total = len(countries)
    total_pages = max(1, (total + COUNTRY_PAGE_SIZE - 1) // COUNTRY_PAGE_SIZE)
    page = min(page, total_pages - 1)
    start = page * COUNTRY_PAGE_SIZE
    end = start + COUNTRY_PAGE_SIZE

    mk = types.InlineKeyboardMarkup(row_width=1)
    for country in countries[start:end]:
        mk.add(types.InlineKeyboardButton(_country_button_label(country), callback_data=f"num_country_{country['key']}"))

    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton("⬅️ السابق", callback_data=f"num_country_page_{page - 1}"))
    if page < (total_pages - 1):
        nav_row.append(types.InlineKeyboardButton("التالي ➡️", callback_data=f"num_country_page_{page + 1}"))
    if nav_row:
        mk.row(*nav_row)

    mk.add(types.InlineKeyboardButton("↩️ رجوع للمنصات", callback_data="num_back"))
    with _country_markup_cache_lock:
        _country_markup_cache[cache_key] = mk
    return mk

def _build_number_actions_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data="num_change"))
    mk.add(types.InlineKeyboardButton("🔍 فحص الكود", callback_data="num_check"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع للدول", callback_data="num_back_countries"))
    mk.add(types.InlineKeyboardButton("🌐 رجوع للمنصات", callback_data="num_back"))
    return mk


def _selected_user_platform(state: Optional[Dict]) -> str:
    return _clean_platform_name((state or {}).get("platform", ""))


def _open_special_platform_section(chat_id: int, platform: str, user_id: Optional[int] = None, message_id: Optional[int] = None) -> bool:
    return False


def _render_user_number_card(chat_id: int, user_id: int, message_id: Optional[int] = None):
    state = user_number_state.get(user_id) or {}
    platform = _selected_user_platform(state)
    if not platform:
        _clear_auto_code_watch(user_id)
        return _send_or_edit(
            chat_id,
            "🌐 اختر القسم من الأقسام الموجودة في الموقع:",
            reply_markup=_build_platform_picker_markup(),
            message_id=message_id,
        )

    platform_numbers = _numbers_for_platform(platform)
    platform_display = html.escape(_display_platform_name(platform))
    if not platform_numbers:
        state["platform"] = platform
        state["index"] = 0
        state.pop("country_key", None)
        state.pop("number", None)
        _reset_state_country_rows(state)
        _clear_auto_code_watch(user_id)
        user_number_state[user_id] = state
        text = (
            f"📂 <b>القسم:</b> {platform_display}\n\n"
            "📭 <b>هذا القسم لا يوجد عليه أرقام حالياً.</b>\n\n"
            "تقدر ترجع للمنصات أو تراسل المطور من الأزرار تحت."
        )
        mk = types.InlineKeyboardMarkup(row_width=1)
        mk.add(types.InlineKeyboardButton("↩️ رجوع للمنصات", callback_data="num_back"))
        mk.add(types.InlineKeyboardButton("✉️ إرسال رسالة للمطور", callback_data="contact_dev"))
        return _send_or_edit(chat_id, text, reply_markup=mk, message_id=message_id, parse_mode="HTML")

    country_key = str(state.get("country_key", "")).strip()
    if not country_key:
        countries = _country_groups_for_platform(platform)
        page = max(0, int(state.get("country_page", 0) or 0))
        total_pages = max(1, (len(countries) + COUNTRY_PAGE_SIZE - 1) // COUNTRY_PAGE_SIZE)
        page = min(page, total_pages - 1)
        start = page * COUNTRY_PAGE_SIZE
        end = min(len(countries), start + COUNTRY_PAGE_SIZE)
        state["platform"] = platform
        state["country_page"] = page
        state["index"] = 0
        state.pop("number", None)
        _reset_state_country_rows(state)
        _clear_auto_code_watch(user_id)
        user_number_state[user_id] = state
        text = (
            f"📂 <b>القسم:</b> {platform_display}\n"
            f"🌍 <b>عدد الدول:</b> {len(countries)}\n"
            f"📱 <b>إجمالي الأرقام:</b> {len(platform_numbers)}\n"
            f"📄 <b>الصفحة:</b> {page + 1} / {total_pages}\n"
            f"⚡ <b>المعروض الآن:</b> {start + 1 if countries else 0} - {end} من الدول المسجلة بالموقع\n\n"
            "اضغط على <b>اسم الدولة</b> أولاً، وبعدها البوت هيعرض لك الأرقام بشكل عشوائي."
        )
        return _send_or_edit(
            chat_id,
            text,
            reply_markup=_build_platform_country_markup(platform, page=page),
            message_id=message_id,
            parse_mode="HTML",
        )

    avail = _state_country_rows(state, platform, country_key)
    if not avail:
        state.pop("country_key", None)
        state["index"] = 0
        state.pop("number", None)
        _reset_state_country_rows(state)
        user_number_state[user_id] = state
        _render_user_number_card(chat_id, user_id, message_id=message_id)
        return

    index = int(state.get("index", 0)) % len(avail)
    state["index"] = index
    state["platform"] = platform
    state["number"] = avail[index]["number"]
    user_number_state[user_id] = state

    country_info = avail[index].get("country") or _get_country_info(avail[index]["number"])
    _set_auto_code_watch(chat_id, user_id, avail[index]["number"], platform, country_info=country_info)
    country_name = html.escape(str(country_info.get("name", "غير محددة") or "غير محددة"))
    code_digits = html.escape(str(country_info.get("code", "") or ""))
    code_text = f" ({code_digits})" if code_digits else ""
    number_html = html.escape(str(avail[index].get("number", "") or ""))
    text = (
        f"📱 <b>القسم:</b> {platform_display}\n"
        f"🌍 <b>الدولة:</b> {country_info.get('flag', '🌐')} {country_name}{code_text}\n"
        f"🔢 <b>الرقم الحالي:</b>\n<code>{number_html}</code>\n\n"
        f"📦 <b>ترتيب الرقم داخل الدولة:</b> {index + 1} من {len(avail)}\n"
        "استخدم الأزرار اللي تحت لتغيير الرقم أو فحص آخر كود."
    )
    return _send_or_edit(
        chat_id,
        text,
        reply_markup=_build_number_actions_markup(),
        message_id=message_id,
        parse_mode="HTML",
    )


def request_number(message):
    bot.reply_to(message, "⚠️ هذه الميزة غير مفعلة في النسخة الآمنة. يمكنك استعراض الأقسام المتاحة أو التواصل مع المطور.")

def platform_callback(call):
    platforms = _user_visible_platforms()
    if not platforms:
        bot.answer_callback_query(call.id, "لا توجد منصات عليها أرقام حالياً", show_alert=True)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return
    try:
        idx = int(call.data.split("_", 1)[1])
        platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, "القسم غير صالح", show_alert=True)
        return
    if _open_special_platform_section(call.message.chat.id, platform, user_id=call.from_user.id, message_id=call.message.message_id):
        bot.answer_callback_query(call.id, f"تم فتح قسم {platform}")
        return
    user_number_state[call.from_user.id] = {
        "platform": platform,
        "country_key": "",
        "country_page": 0,
        "index": 0,
        "_country_rows": [],
    }
    bot.answer_callback_query(call.id, f"تم فتح قسم {platform}")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)

def country_page_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    platform = _selected_user_platform(state)
    if not platform:
        bot.answer_callback_query(call.id, "اختر القسم أولاً", show_alert=True)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return

    try:
        page = max(0, int(call.data.replace("num_country_page_", "", 1).strip() or "0"))
    except Exception:
        page = 0

    state["platform"] = platform
    state["country_page"] = page
    state.pop("country_key", None)
    state["index"] = 0
    state.pop("number", None)
    _reset_state_country_rows(state)
    user_number_state[call.from_user.id] = state
    bot.answer_callback_query(call.id)
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def platform_country_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    platform = _selected_user_platform(state)
    if not platform:
        bot.answer_callback_query(call.id, "اختر القسم أولاً", show_alert=True)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return
    country_key = call.data.replace("num_country_", "", 1).strip() or "unknown"
    avail = _numbers_for_platform_country(platform, country_key)
    if not avail:
        state.pop("country_key", None)
        state["index"] = 0
        state.pop("number", None)
        _reset_state_country_rows(state)
        user_number_state[call.from_user.id] = state
        bot.answer_callback_query(call.id, "لا توجد أرقام داخل هذه الدولة حالياً", show_alert=True)
        _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)
        return
    random.shuffle(avail)
    state["platform"] = platform
    state["country_key"] = country_key
    state["index"] = 0
    state.pop("number", None)
    state['_country_rows_platform'] = _normalize_platform(platform)
    state['_country_rows_key'] = country_key
    state['_country_rows'] = [dict(item) for item in avail]
    user_number_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, "✅ تم فتح الدولة")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def number_change_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    platform = _selected_user_platform(state)
    country_key = str(state.get("country_key", "")).strip()
    if not platform:
        bot.answer_callback_query(call.id, "اختر القسم أولاً", show_alert=True)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return
    if not country_key:
        bot.answer_callback_query(call.id, "اختر الدولة أولاً", show_alert=True)
        _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)
        return
    avail = _state_country_rows(state, platform, country_key)
    if not avail:
        bot.answer_callback_query(call.id, "لا توجد أرقام داخل هذه الدولة حالياً", show_alert=True)
        state.pop("country_key", None)
        state["index"] = 0
        _reset_state_country_rows(state)
        user_number_state[call.from_user.id] = state
        _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)
        return
    state["index"] = (int(state.get("index", 0)) + 1) % len(avail)
    user_number_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, "✅ تم تغيير الرقم")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def number_back_countries_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    platform = _selected_user_platform(state)
    if not platform:
        user_number_state.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return
    state.pop("country_key", None)
    state["country_page"] = max(0, int(state.get("country_page", 0) or 0))
    state["index"] = 0
    state.pop("number", None)
    _reset_state_country_rows(state)
    user_number_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, "تم الرجوع لقائمة الدول")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def number_back_callback(call):
    user_number_state.pop(call.from_user.id, None)
    _clear_auto_code_watch(call.from_user.id)
    bot.answer_callback_query(call.id)
    _send_demo_home(call.message.chat.id, message_id=call.message.message_id)

def number_check_callback(call):
    """
    يفحص آخر كود للرقم المختار.
    - يعمل في خيط منفصل لعدم تجميد البوت
    - ينتظر فترة قصيرة لمتابعة وصول الكود مباشرة بعد تفعيل الرقم
    - يعرض الكود بصيغة HTML آمنة لتجنب انهيار الرسائل بسبب Markdown
    - يُسجّل الكود في القناة تلقائياً
    """
    state = user_number_state.get(call.from_user.id) or {}
    number = _normalize_number(state.get("number", ""))
    platform = _selected_user_platform(state) or GENERAL_PLATFORM_NAME
    country_info = _get_country_info(number) if number else {"name": "غير محددة", "flag": "🌐"}

    if not number:
        bot.answer_callback_query(call.id, "اختر الدولة ثم الرقم أولاً", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ جاري متابعة وصول الكود...")
    chat_id = call.message.chat.id

    def _do_fetch():
        wait_message = None
        try:
            max_attempts = max(20, int(str(_get("CHECK_CODE_ATTEMPTS", "60") or "60").strip() or "60"))
            delay_seconds = max(0.35, float(str(_get("CHECK_CODE_DELAY_SECONDS", "0.35") or "0.35").strip() or "0.35"))
            total_wait = int(max_attempts * delay_seconds)
            number_html = html.escape(number)
            try:
                wait_message = bot.send_message(
                    chat_id,
                    f"⏳ جاري متابعة الرقم <code>{number_html}</code> لمدة تقريبية {total_wait} ثانية أو حتى وصول الكود.",
                    parse_mode="HTML",
                )
            except Exception:
                wait_message = None

            data = None
            for attempt in range(max_attempts):
                data = _fetch_latest_sms_for_number(number, platform)
                code_value = str((data or {}).get("code") or "").strip()
                if data and code_value and code_value != "غير متوفر":
                    break
                data = None
                if attempt < max_attempts - 1:
                    time.sleep(delay_seconds)

            if wait_message is not None:
                try:
                    bot.delete_message(chat_id, wait_message.message_id)
                except Exception:
                    pass

            country_name = html.escape(str(country_info.get('name', 'غير محددة') or 'غير محددة'))
            platform_name = html.escape(_display_platform_name(platform))
            if not data:
                bot.send_message(
                    chat_id,
                    (
                        "🔍 <b>فحص الكود</b>\n\n"
                        f"📂 القسم: {platform_name}\n"
                        f"🌍 الدولة: {country_info.get('flag','🌐')} {country_name}\n"
                        f"📱 الرقم: <code>{number_html}</code>\n\n"
                        "❌ لم يصل كود خلال فترة المتابعة الحالية. جرّب مرة ثانية بعد لحظات."
                    ),
                    parse_mode="HTML",
                )
                return

            sms_text = (data.get("text") or data.get("message") or "").strip()
            code = str(data.get("code") or "").strip() or "غير متوفر"
            received_at = str(data.get("date") or data.get("created_at") or data.get("time") or "غير محدد")
            source_name = str(data.get("source") or "").strip()
            detected_platform = _normalize_platform(data.get("platform") or data.get("service") or platform or GENERAL_PLATFORM_NAME)
            _cache_code_for_number(number, detected_platform or platform, data)
            _mark_auto_code_watch_seen(call.from_user.id, number, code)

            reply = (
                "🔍 <b>نتيجة فحص الكود</b>\n\n"
                f"📂 القسم: {html.escape(_display_platform_name(detected_platform or platform))}\n"
                f"🌍 الدولة: {country_info.get('flag','🌐')} {country_name}\n"
                f"📱 الرقم: <code>{number_html}</code>\n"
                f"🔐 <b>الكود:</b> <code>{html.escape(code)}</code>\n"
                f"🕐 الوقت: {html.escape(received_at)}"
            )
            if source_name:
                reply += f"\n📡 المصدر: {html.escape(source_name)}"
            if sms_text:
                reply += f"\n\n📩 <b>نص الرسالة:</b>\n{html.escape(sms_text[:1000])}"

            bot.send_message(chat_id, reply + "\n\n🗑️ <b>سيتم حذف الرقم تلقائياً من البوت بعد إرسال الكود للحماية.</b>", parse_mode="HTML")
            _notify_code_to_channel(
                number,
                detected_platform or platform,
                code,
                country_info=country_info,
                received_at=received_at,
                sms_text=sms_text,
            )
            removed_count = _remove_number_from_storage(number)
            state_after = user_number_state.get(call.from_user.id) or {}
            cached_rows = [
                dict(item) for item in list(state_after.get('_country_rows') or [])
                if _normalize_number(item.get('number', '')) != number
            ]
            if cached_rows:
                state_after['_country_rows'] = cached_rows
            else:
                state_after.pop('country_key', None)
                _reset_state_country_rows(state_after)
            state_after.pop('number', None)
            state_after['index'] = 0
            user_number_state[call.from_user.id] = state_after
            _clear_auto_code_watch(call.from_user.id)
            if removed_count > 0:
                logger.info(f"🗑️ تم حذف الرقم {number} تلقائياً بعد إرسال الكود للمستخدم {call.from_user.id}")
        except Exception as check_err:
            logger.warning(f"number_check_callback error ({number}): {check_err}")
            try:
                if wait_message is not None:
                    try:
                        bot.delete_message(chat_id, wait_message.message_id)
                    except Exception:
                        pass
                bot.send_message(chat_id, f"⚠️ حدث خطأ أثناء جلب الكود: {check_err}")
            except Exception:
                pass

    threading.Thread(target=_do_fetch, daemon=True).start()


def support_handler(message):
    bot.reply_to(message, f"🆘 للدعم الفني تواصل مع: {SUPPORT_USERNAME}")

def user_sections_handler(message):
    if not _require_subscription(message):
        return
    _send_demo_home(message.chat.id)

def check_sub_callback(call):
    if _check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق من الاشتراك.", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        cmd_start(call.message)
    else:
        bot.answer_callback_query(call.id, f"❌ تأكد من الاشتراك في {DEVELOPER_CHANNEL} ثم أعد المحاولة.", show_alert=True)

def developer_channel_handler(message):
    if not _require_subscription(message):
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        f"📢 الانضمام إلى {DEVELOPER_CHANNEL}",
        url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME}",
    ))
    bot.send_message(message.chat.id, f"📢 قناة المطور الرسمية\n\nالقناة: {DEVELOPER_CHANNEL}\nالمطور: @{DEVELOPER_USERNAME}", reply_markup=mk)

def contact_dev_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✉️ أرسل رسالتك الآن ليتم تحويلها إلى المطور.")
    bot.register_next_step_handler(msg, _send_to_developer)

def contact_dev_prompt(message):
    if not _require_subscription(message):
        return
    msg = bot.reply_to(message, "✉️ أرسل رسالتك الآن ليتم تحويلها إلى المطور.")
    bot.register_next_step_handler(msg, _send_to_developer)

def _send_to_developer(message):
    body = message.text or ""
    sender_name = message.from_user.full_name or "مستخدم"
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون معرف"
    payload = (
        "✉️ رسالة جديدة من أحد المستخدمين\n\n"
        f"الاسم: {sender_name}\n"
        f"المعرف: {username}\n"
        f"الآيدي: {message.from_user.id}\n\n"
        f"الرسالة:\n{body}"
    )
    try:
        bot.send_message(ADMIN_ID, payload)
        bot.reply_to(message, "✅ تم إرسال رسالتك للمطور.")
    except Exception as e:
        bot.reply_to(message, f"❌ تعذر الإرسال حالياً: {e}")

def _feature_removed_notice(target, feature_name: str):
    text = f"ℹ️ تم حذف قسم {feature_name} من هذه النسخة لتحسين الاستقرار على الاستضافة المجانية."
    try:
        if hasattr(target, "id") and hasattr(target, "message"):
            bot.answer_callback_query(target.id, text, show_alert=True)
            bot.send_message(target.message.chat.id, text)
        elif hasattr(target, "chat"):
            bot.reply_to(target, text)
    except Exception as feature_notice_err:
        logger.warning(f"Feature removed notice warning: {feature_notice_err}")


def download_video_menu(message):
    _feature_removed_notice(message, "تحميل الفيديو")


def download_platform_callback(call):
    _feature_removed_notice(call, "تحميل الفيديو")


def _process_video_download(message, platform: str):
    _feature_removed_notice(message, f"تحميل {platform}")


def name_decoration_prompt(message):
    _feature_removed_notice(message, "الزخرفة")


def _show_decorated_names(message):
    _feature_removed_notice(message, "الزخرفة")


def paid_numbers_handler(message):
    if not _require_subscription(message):
        return
    nums = paid_numbers_db.get("numbers", [])
    if not nums:
        bot.reply_to(message, f"💎 لا توجد عناصر مدفوعة حالياً. للاستفسار تواصل مع @{DEVELOPER_USERNAME}")
        return
    stats = {}
    for item in nums:
        plat = item.get("platform", "General")
        stats[plat] = stats.get(plat, 0) + 1
    text = "💎 ملخص العناصر المدفوعة:\n\n"
    for plat, cnt in stats.items():
        text += f"• {plat}: {cnt}\n"
    text += f"\nللطلب تواصل مع @{DEVELOPER_USERNAME}"
    bot.send_message(message.chat.id, text)

def developer_panel_handler(message):
    bot.send_message(message.chat.id, "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:", reply_markup=_build_developer_panel_markup())

def dev_sections_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📚 أقسام الموقع الحالية:", reply_markup=_build_sections_markup())

def dev_section_numbers_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    platforms = _platform_picker_platforms()
    try:
        idx = int(call.data.split("_", 1)[1])
        plat = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, "القسم غير صالح", show_alert=True)
        return
    rows = _numbers_for_platform(plat)
    if not rows:
        bot.answer_callback_query(call.id, "لا توجد عناصر في هذا القسم", show_alert=True)
        return
    lines = [f"📚 القسم: {plat}", f"📦 العدد: {len(rows)}", ""]
    for row in rows[:50]:
        country = _guess_country_with_flag(row.get("number", ""))
        source = row.get("source", "manual")
        site_section = str(row.get("site_section", "")).strip()
        extra = f" — المصدر: {source}"
        if site_section and _normalize_platform(site_section) != _normalize_platform(plat):
            extra += f" — قسم الموقع الأصلي: {site_section}"
        lines.append(f"• {row.get('number', '')} — الدولة: {country}{extra}")
    if len(rows) > 50:
        lines.append(f"\n... ويوجد {len(rows) - 50} عناصر إضافية")
    _chunked_send(call.message.chat.id, "\n".join(lines))
    bot.answer_callback_query(call.id, f"تم فتح قسم {plat}")

def dev_sub_status_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"🔐 الاشتراك الإجباري: مفعّل\n📢 القناة: {DEVELOPER_CHANNEL}\n🆔 Channel ID: {CHANNEL_ID}")

def dev_paid_summary_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    nums = paid_numbers_db.get("numbers", [])
    if not nums:
        bot.send_message(call.message.chat.id, "💎 لا توجد بيانات مدفوعة محفوظة حالياً.")
        return
    stats = {}
    for item in nums:
        plat = item.get("platform", "General")
        stats[plat] = stats.get(plat, 0) + 1
    text = "💎 ملخص البيانات المدفوعة:\n\n"
    for plat, cnt in stats.items():
        text += f"• {plat}: {cnt}\n"
    bot.send_message(call.message.chat.id, text)

def dev_channel_info_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"👑 المطور: @{DEVELOPER_USERNAME}\n📢 القناة: {DEVELOPER_CHANNEL}\n🆔 Channel ID: {CHANNEL_ID}")

_start_time = time.time()

def _get_uptime() -> str:
    secs = int(time.time() - _start_time)
    h, m = divmod(secs // 60, 60)
    s    = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def _release_bot_lock():
    try:
        if BOT_LOCK_FILE.exists() and BOT_LOCK_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
            BOT_LOCK_FILE.unlink()
    except Exception as lock_cleanup_err:
        logger.warning(f"Lock cleanup warning: {lock_cleanup_err}")

def _ensure_single_local_instance():
    try:
        current_pid = os.getpid()
        if BOT_LOCK_FILE.exists():
            existing_pid = BOT_LOCK_FILE.read_text(encoding="utf-8").strip()
            if existing_pid.isdigit():
                existing_pid_int = int(existing_pid)
                if existing_pid_int == current_pid:
                    return
                try:
                    os.kill(existing_pid_int, 0)
                    raise RuntimeError(f"يوجد تشغيل محلي آخر للبوت بنفس الجهاز (PID: {existing_pid}).")
                except OSError:
                    BOT_LOCK_FILE.unlink(missing_ok=True)
            else:
                BOT_LOCK_FILE.unlink(missing_ok=True)
        BOT_LOCK_FILE.write_text(str(current_pid), encoding="utf-8")
        atexit.register(_release_bot_lock)
    except RuntimeError:
        raise
    except Exception as lock_err:
        logger.warning(f"تعذر إنشاء ملف القفل المحلي: {lock_err}")

def handle_txt_file(message):
    if not is_admin(message):
        return

    file_name = message.document.file_name.lower()
    if not file_name.endswith(".txt"):
        bot.reply_to(message, "❌ فقط ملفات TXT مسموحة.")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    content = downloaded_file.decode("utf-8", errors="ignore")

    user_number_state[message.from_user.id] = {
        "txt_numbers": content.splitlines()
    }

    platforms = _platform_picker_platforms()
    mk = types.InlineKeyboardMarkup(row_width=2)

    for plat in platforms[:30]:
        mk.add(types.InlineKeyboardButton(plat, callback_data=f"txtplt_{plat}"))

    bot.reply_to(message, "📂 اختر المنصة لإضافة الأرقام إليها:", reply_markup=mk)

def txt_platform_selected(call):
    if call.from_user.id != ADMIN_ID:
        return

    platform = _normalize_platform(call.data.replace("txtplt_", ""))
    data = user_number_state.get(call.from_user.id, {})

    lines = data.get("txt_numbers", [])
    prepared = []

    for line in lines:
        num = _normalize_number(line)
        if num:
            prepared.append({
                "number": num,
                "platform": platform,
                "source": "txt",
                "added_at": time.ctime(),
            })

    if not prepared:
        bot.send_message(call.message.chat.id, "❌ الملف لا يحتوي أرقام صالحة.")
        return

    before = list(numbers_db.get("numbers", []))
    merged = _append_numbers(prepared)

    added_items = _find_newly_added_numbers(before, merged)

    bot.send_message(
        call.message.chat.id,
        f"✅ تم إضافة {len(added_items)} رقم إلى {platform}"
    )

    log_event("TXT_IMPORT", {"count": len(added_items), "platform": platform})

    if added_items:
        import io
        icon = PLATFORM_BUTTON_ICONS.get(platform, "📂")
        txt_lines = [
            "📋 أرقام مستوردة من ملف TXT",
            f"⏱ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{icon} المنصة: {platform}",
            f"📱 عدد الأرقام: {len(added_items)}",
            "",
            f"{'='*40}",
        ]
        for item in added_items:
            country = _get_country_info(item.get("number", ""))
            txt_lines.append(f"{country['flag']} {item['number']}  |  {country['name']}")

        content = "\n".join(txt_lines).encode("utf-8")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            bot.send_document(
                call.message.chat.id,
                ("txt_import_" + timestamp + ".txt", io.BytesIO(content), "text/plain"),
                caption=f"📨 ملف الأرقام المستوردة\n✅ {len(added_items)} رقم → {icon} {platform}",
            )
        except Exception as e:
            logger.warning(f"إرسال ملف TXT بعد الاستيراد فشل: {e}")

def _platform_exists(platform):
    existing = set()
    for n in numbers_db.get("numbers", []):
        existing.add(_normalize_platform(n.get("platform", "")))
    return platform in existing

pending_activation = {}

AUTO_CODE_WATCH_ENABLED = _env_flag("AUTO_CODE_WATCH_ENABLED", False)
AUTO_CODE_WATCH_INTERVAL_SECONDS = max(10.0, float(str(_get("AUTO_CODE_WATCH_INTERVAL_SECONDS", "15.0") or "15.0").strip() or "15.0"))
AUTO_CODE_WATCH_TTL_SECONDS = max(600, int(str(_get("AUTO_CODE_WATCH_TTL_SECONDS", "1800") or "1800").strip() or "1800"))
_auto_code_watch_started = False
_auto_code_watch_lock = threading.Lock()
_auto_code_watchers: Dict[int, Dict[str, Any]] = {}


def _clear_auto_code_watch(user_id: int) -> None:
    with _auto_code_watch_lock:
        _auto_code_watchers.pop(int(user_id), None)



def _mark_auto_code_watch_seen(user_id: int, number: str, code: str) -> None:
    normalized_number = _normalize_number(number)
    normalized_code = str(code or "").strip()
    if not normalized_number or not normalized_code:
        return
    with _auto_code_watch_lock:
        watch = _auto_code_watchers.get(int(user_id))
        if not watch:
            return
        if _normalize_number(watch.get("number", "")) != normalized_number:
            return
        watch["last_seen_code"] = normalized_code
        watch["updated_at"] = time.time()



def _set_auto_code_watch(chat_id: int, user_id: int, number: str, platform: str, country_info: Optional[Dict] = None) -> None:
    if not AUTO_CODE_WATCH_ENABLED:
        return
    normalized_number = _normalize_number(number)
    normalized_platform = _normalize_platform(platform or GENERAL_PLATFORM_NAME)
    if not normalized_number:
        _clear_auto_code_watch(user_id)
        return
    baseline = _lookup_cached_code_for_number(normalized_number, normalized_platform) or {}
    baseline_code = str((baseline or {}).get("code") or "").strip()
    info = dict(country_info or _get_country_info(normalized_number) or {})
    with _auto_code_watch_lock:
        _auto_code_watchers[int(user_id)] = {
            "chat_id": int(chat_id),
            "user_id": int(user_id),
            "number": normalized_number,
            "platform": normalized_platform,
            "country_info": info,
            "last_seen_code": baseline_code,
            "skip_initial_fetch": not bool(baseline_code),
            "updated_at": time.time(),
        }



def _auto_code_watch_loop():
    idle_sleep_seconds = max(5.0, AUTO_CODE_WATCH_INTERVAL_SECONDS)
    while True:
        sleep_seconds = max(3.0, AUTO_CODE_WATCH_INTERVAL_SECONDS)
        try:
            now = time.time()
            expired_user_ids = []
            with _auto_code_watch_lock:
                watchers_snapshot = [dict(item) for item in _auto_code_watchers.values()]
                for uid, item in list(_auto_code_watchers.items()):
                    if now - float(item.get("updated_at") or 0) > AUTO_CODE_WATCH_TTL_SECONDS:
                        expired_user_ids.append(uid)
            for uid in expired_user_ids:
                _clear_auto_code_watch(uid)

            if not watchers_snapshot:
                time.sleep(idle_sleep_seconds)
                continue

            grouped_watchers: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
            for watch in watchers_snapshot:
                number = _normalize_number(watch.get("number", ""))
                platform = _normalize_platform(watch.get("platform", ""))
                if not number:
                    continue
                grouped_watchers.setdefault((number, platform), []).append(watch)

            if not grouped_watchers:
                time.sleep(idle_sleep_seconds)
                continue

            fetched_results: Dict[Tuple[str, str], Optional[Dict[str, Any]]] = {}
            for cache_key in grouped_watchers.keys():
                number, platform = cache_key
                try:
                    fetched_results[cache_key] = _fetch_latest_sms_for_number(number, platform)
                except Exception as fetch_err:
                    fetched_results[cache_key] = None
                    logger.debug(f"AUTO_CODE_WATCH fetch skipped for {number}: {fetch_err}")

            for cache_key, watch_group in grouped_watchers.items():
                number, platform = cache_key
                data = fetched_results.get(cache_key) or {}
                code_value = str((data or {}).get("code") or "").strip()
                if not data or not code_value or code_value == "غير متوفر":
                    continue

                sms_text = str((data or {}).get("text") or (data or {}).get("message") or "").strip()
                received_at = str((data or {}).get("date") or (data or {}).get("created_at") or (data or {}).get("time") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
                detected_platform = _normalize_platform((data or {}).get("platform") or (data or {}).get("service") or platform or GENERAL_PLATFORM_NAME)
                _cache_code_for_number(number, detected_platform, data)

                for watch in watch_group:
                    if bool(watch.get("skip_initial_fetch")):
                        try:
                            with _auto_code_watch_lock:
                                current = _auto_code_watchers.get(int(watch.get("user_id") or 0))
                                if current and _normalize_number(current.get("number", "")) == number and _normalize_platform(current.get("platform", "")) == platform:
                                    current["skip_initial_fetch"] = False
                                    current["updated_at"] = time.time()
                        except Exception:
                            pass
                    if code_value == str(watch.get("last_seen_code") or "").strip():
                        continue
                    info = dict(watch.get("country_info") or _get_country_info(number) or {})
                    safe_platform = html.escape(str(detected_platform or GENERAL_PLATFORM_NAME))
                    safe_flag = html.escape(str(info.get('flag', '🌐') or '🌐'))
                    safe_country = html.escape(str(info.get('name', 'غير محددة') or 'غير محددة'))
                    safe_number = html.escape(str(number or ''))
                    safe_code = html.escape(str(code_value or ''))
                    safe_time = html.escape(str(received_at or ''))
                    reply = (
                        "⚡ <b>وصل كود جديد تلقائياً</b>\n\n"
                        f"📂 القسم: <b>{safe_platform}</b>\n"
                        f"🌍 الدولة: {safe_flag} {safe_country}\n"
                        f"📱 الرقم: <code>{safe_number}</code>\n"
                        f"🔐 الكود: <code>{safe_code}</code>\n"
                        f"🕐 الوقت: {safe_time}"
                    )
                    if sms_text:
                        reply += f"\n\n📩 <b>نص الرسالة:</b>\n<blockquote>{html.escape(str(sms_text)[:1000])}</blockquote>"

                    try:
                        bot.send_message(int(watch.get("chat_id")), reply, parse_mode="HTML")
                        _notify_code_to_channel(
                            number,
                            detected_platform,
                            code_value,
                            country_info=info,
                            received_at=received_at,
                            sms_text=sms_text,
                        )
                        _mark_auto_code_watch_seen(int(watch.get("user_id")), number, code_value)
                        logger.info(f"⚡ [AUTO-WATCH] تم إرسال الكود تلقائياً للرقم {number}")
                    except Exception as auto_watch_err:
                        logger.warning(f"AUTO_CODE_WATCH send error for {number}: {auto_watch_err}")
        except Exception as auto_watch_loop_err:
            logger.warning(f"AUTO_CODE_WATCH loop error: {auto_watch_loop_err}")

        time.sleep(sleep_seconds)

def _start_auto_code_watch_loop_once() -> None:
    global _auto_code_watch_started
    if _auto_code_watch_started:
        return
    if not AUTO_CODE_WATCH_ENABLED:
        logger.info("⏸️ المراقبة التلقائية للأكواد متوقفة.")
        return
    _auto_code_watch_started = True
    threading.Thread(target=_auto_code_watch_loop, daemon=True).start()
    logger.info(
        f"✅ تم تشغيل المراقبة التلقائية للأكواد كل {AUTO_CODE_WATCH_INTERVAL_SECONDS} ثانية"
    )


def _filter_existing_platforms(prepared):
    prepared_filtered = []
    for item in prepared:
        plat = _normalize_platform(item.get("platform"))
        if not _platform_exists(plat):
            continue
        prepared_filtered.append(item)
    return prepared_filtered

def confirm_number(message):
    if not is_admin(message):
        return

    try:
        number = message.text.split(" ", 1)[1].strip()
    except:
        bot.reply_to(message, "❌ استخدم: /confirm الرقم")
        return

    data = pending_activation.get(number)

    if not data:
        bot.reply_to(message, "❌ الرقم غير موجود أو منتهي.")
        return

    new_numbers = []
    for n in numbers_db.get("numbers", []):
        if n.get("number") != number:
            new_numbers.append(n)

    numbers_db["numbers"] = new_numbers
    _save_numbers()

    pending_activation.pop(number, None)

    bot.reply_to(message, f"✅ تم تأكيد الرقم {number} وحذفه تلقائيًا")

def cleanup_pending():
    now = time.time()
    to_delete = []

    for num, data in pending_activation.items():
        if now - data["time"] > 600:
            to_delete.append(num)

    for num in to_delete:
        pending_activation.pop(num, None)

CHANNEL_USERNAME = "@fz_z_Z"

sent_codes_cache: set = set()  # cache الأكواد المُرسلة للقناة

def _limit_sent_codes_cache(max_size: int = 100000) -> None:
    """يُحدّد حجم sent_codes_cache ويحذف القديم إذا تجاوز الحد."""
    global sent_codes_cache
    if len(sent_codes_cache) > max_size:
        items = list(sent_codes_cache)
        sent_codes_cache = set(items[-(max_size // 2):])

def extract_codes_from_numbers():
    codes = []
    for n in numbers_db.get("numbers", []):
        code = n.get("code") or n.get("sms") or n.get("last_code")
        if code:
            codes.append((n.get("platform"), n.get("number"), code))
    return codes

def auto_send_codes():
    codes = extract_codes_from_numbers()

    for platform, number, code in codes:
        key = f"{number}_{code}"
        if key in sent_codes_cache:
            continue

        text = f"📩 كود جديد\n\n📱 الرقم: {number}\n💻 المنصة: {platform}\n🔐 الكود: {code}"
        try:
            bot.send_message(CHANNEL_USERNAME, text)
            sent_codes_cache.add(key)
        except Exception as e:
            print("Channel send error:", e)

def start_auto_sender():
    import threading, time
    def loop():
        while True:
            try:
                auto_send_codes()
                time.sleep(10)
            except:
                time.sleep(5)
    threading.Thread(target=loop, daemon=True).start()

import re

import time

import threading

CHANNEL_USERNAME = "@fz_z_Z"

def send_codes_to_channel(codes):
    for item in codes:
        country_info = _get_country_info(item.get('number', ''))
        if item.get('country'):
            country_info = dict(country_info)
            country_info['name'] = item.get('country') or country_info.get('name', 'غير محددة')
        _notify_code_to_channel(
            item.get('number', ''),
            item.get('service', ''),
            item.get('code', ''),
            country_info=country_info,
            sms_text=item.get('message', ''),
        )

def live_codes_loop():
    sent = set()
    while True:
        try:
            codes = fetch_live_test_codes()

            for item in codes:
                key = item["code"] + item["number"]

                if key not in sent:
                    send_codes_to_channel([item])
                    sent.add(key)

        except Exception as e:
            print("Loop error:", e)

        time.sleep(10)

_EXTRA_PLATFORM_ICONS = {
    "Binance":          "🪙",
    "Bybit":            "📊",
    "OKX":              "🔷",
    "Crypto.com":       "💎",
    "Coinbase":         "🏦",
    "Kraken":           "🐙",
    "Bitget":           "⚡",
    "KuCoin":           "🟢",
    "Gate.io":          "🔑",
    "Huobi":            "🔥",
    "Blum":             "🌸",
    "Hamster Kombat":   "🐹",
    "Notcoin":          "💰",
    "TON":              "💎",
    "Tether":           "💵",
    "Steam":            "🎮",
    "Epic Games":       "🎯",
    "Xbox":             "🎲",
    "PlayStation":      "🕹️",
    "Roblox":           "🧱",
    "PUBG":             "🔫",
    "Free Fire":        "🔥",
    "Call of Duty":     "💣",
    "Shopee":           "🛍️",
    "AliExpress":       "🛒",
    "Noon":             "🌙",
    "Careem":           "🚗",
    "Lyft":             "🚕",
    "InDrive":          "🚖",
    "Bolt":             "⚡",
    "Airbnb":           "🏠",
    "Booking":          "📅",
    "Agoda":            "🏨",
    "OLX":              "📢",
    "Dubizzle":         "🏷️",
    "eBay":             "🏪",
    "Etsy":             "🎨",
    "Fiverr":           "💼",
    "Upwork":           "💻",
    "LinkedIn":         "🔗",
    "Pinterest":        "📌",
    "Reddit":           "🤖",
    "Quora":            "❓",
    "Tumblr":           "📝",
    "Signal":           "🔐",
    "Skype":            "📹",
    "Zoom":             "📽️",
    "Google":           "🔍",
    "Outlook":          "📧",
    "iCloud":           "☁️",
    "Dropbox":          "📦",
    "OneDrive":         "🌐",
    "Spotify":          "🎵",
    "SoundCloud":       "🎶",
    "Deezer":           "🎧",
    "YouTube":          "▶️",
    "Shahid":           "🎬",
    "OSN":              "📺",
    "beIN Sports":      "⚽",
    "Starzplay":        "⭐",
    "Anghami":          "🎼",
    "Jawwy":            "📡",
    "Mobily":           "📶",
    "Zain":             "📲",
    "STC":              "📱",
    "Etisalat":         "📞",
    "Du":               "🔵",
    "Ooredoo":          "🔴",
    "General":          "📂",
}

for _plat, _icon in _EXTRA_PLATFORM_ICONS.items():
    if _plat not in PLATFORM_BUTTON_ICONS:
        PLATFORM_BUTTON_ICONS[_plat] = _icon

_EXTRA_PLATFORM_ALIASES = {
    "binance":        "Binance",
    "bybit":          "Bybit",
    "okx":            "OKX",
    "ok x":           "OKX",
    "crypto.com":     "Crypto.com",
    "coinbase":       "Coinbase",
    "kraken":         "Kraken",
    "bitget":         "Bitget",
    "kucoin":         "KuCoin",
    "gate.io":        "Gate.io",
    "huobi":          "Huobi",
    "blum":           "Blum",
    "hamster":        "Hamster Kombat",
    "hamster kombat": "Hamster Kombat",
    "notcoin":        "Notcoin",
    "steam":          "Steam",
    "epic games":     "Epic Games",
    "epicgames":      "Epic Games",
    "xbox":           "Xbox",
    "playstation":    "PlayStation",
    "ps":             "PlayStation",
    "roblox":         "Roblox",
    "pubg":           "PUBG",
    "free fire":      "Free Fire",
    "freefire":       "Free Fire",
    "call of duty":   "Call of Duty",
    "cod":            "Call of Duty",
    "shopee":         "Shopee",
    "aliexpress":     "AliExpress",
    "noon":           "Noon",
    "careem":         "Careem",
    "lyft":           "Lyft",
    "indrive":        "InDrive",
    "bolt":           "Bolt",
    "airbnb":         "Airbnb",
    "booking":        "Booking",
    "agoda":          "Agoda",
    "olx":            "OLX",
    "dubizzle":       "Dubizzle",
    "ebay":           "eBay",
    "etsy":           "Etsy",
    "fiverr":         "Fiverr",
    "upwork":         "Upwork",
    "linkedin":       "LinkedIn",
    "لينكدإن":        "LinkedIn",
    "pinterest":      "Pinterest",
    "reddit":         "Reddit",
    "quora":          "Quora",
    "signal":         "Signal",
    "سيجنال":         "Signal",
    "skype":          "Skype",
    "سكايب":          "Skype",
    "zoom":           "Zoom",
    "زوم":            "Zoom",
    "google":         "Google",
    "جوجل":           "Google",
    "outlook":        "Outlook",
    "icloud":         "iCloud",
    "آي كلاود":       "iCloud",
    "dropbox":        "Dropbox",
    "spotify":        "Spotify",
    "سبوتيفاي":       "Spotify",
    "youtube":        "YouTube",
    "يوتيوب":         "YouTube",
    "shahid":         "Shahid",
    "شاهد":           "Shahid",
    "osn":            "OSN",
    "bein sports":    "beIN Sports",
    "bein":           "beIN Sports",
    "بي إن":          "beIN Sports",
    "starzplay":      "Starzplay",
    "anghami":        "Anghami",
    "أنغامي":         "Anghami",
    "jawwy":          "Jawwy",
    "جوّي":           "Jawwy",
    "mobily":         "Mobily",
    "موبايلي":        "Mobily",
    "zain":           "Zain",
    "زين":            "Zain",
    "stc":            "STC",
    "اس تي سي":       "STC",
    "etisalat":       "Etisalat",
    "اتصالات":        "Etisalat",
    "du":             "Du",
    "دو":             "Du",
    "ooredoo":        "Ooredoo",
    "اوريدو":         "Ooredoo",
}

for _alias, _canonical in _EXTRA_PLATFORM_ALIASES.items():
    if _alias not in PLATFORM_CANONICAL_ALIASES:
        PLATFORM_CANONICAL_ALIASES[_alias] = _canonical

def dev_fetch_site_callback(call):
    """يفتح تدفق إضافة أرقام الموقع: دولة ← منصة ← إضافة جماعية."""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id, "⏳ جاري تحديث دول الموقع الآن...")
    _launch_site_add_open_async(
        call.message.chat.id,
        call.from_user.id,
        refresh=True,
        message_id=call.message.message_id,
    )


def dev_edit_welcome_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    current = _get_welcome_message()
    msg = bot.send_message(
        call.message.chat.id,
        "🖊️ تعديل رسالة الترحيب\n\n"
        f"الرسالة الحالية:\n{current}\n\n"
        "أرسل الرسالة الجديدة الآن.\n"
        "ولو حابب ترجع للوضع الافتراضي ابعت: /reset",
    )
    bot.register_next_step_handler(msg, _save_new_welcome_step)

def dev_show_commands_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, _developer_commands_text())

def dev_export_all_txt_callback(call):
    """يُصدّر ملف TXT واحد يحتوي كل الأرقام مصنّفة حسب المنصة."""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _export_all_numbers_txt(call.message.chat.id)

def _export_all_numbers_txt(chat_id: int):
    """يُنشئ ملف TXT يحتوي كل الأرقام مصنّفة حسب المنصة ويرسله."""
    platforms = _platform_picker_platforms()
    lines = []
    has_numbers = False

    for plat in platforms:
        nums = _numbers_for_platform(plat)
        if not nums:
            continue
        has_numbers = True
        icon = PLATFORM_BUTTON_ICONS.get(plat, "📂")
        lines.append(f"{'='*40}")
        lines.append(f"{icon} {plat} ({len(nums)} رقم)")
        lines.append(f"{'='*40}")
        for item in nums:
            country = _get_country_info(item.get("number", ""))
            lines.append(
                f"{country['flag']} {item['number']}  |  {country['name']}  |  {item.get('added_at','')}"
            )
        lines.append("")

    if not has_numbers:
        bot.send_message(chat_id, "📭 لا توجد أرقام في قاعدة البيانات حالياً.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    total = len(numbers_db.get("numbers", []))
    header = [
        f"📋 ملف تصدير الأرقام",
        f"⏱ التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"📱 إجمالي الأرقام: {total}",
        f"🌐 عدد المنصات: {len([p for p in platforms if _numbers_for_platform(p)])}",
        "",
    ]

    full_content = "\n".join(header + lines)
    file_bytes = full_content.encode("utf-8")

    import io
    bot.send_document(
        chat_id,
        ("numbers_export_" + timestamp + ".txt", io.BytesIO(file_bytes), "text/plain"),
        caption=(
            f"📤 ملف تصدير الأرقام\n"
            f"📱 {total} رقم على {len([p for p in platforms if _numbers_for_platform(p)])} منصة"
        ),
    )
    log_event("EXPORT_TXT", {"total": total, "platforms": len(platforms)})

def add_manual_prompt_v2(message):
    """نسخة محدّثة من زر الإضافة اليدوية تستخدم _process_manual_add المحسّنة."""
    platforms = _platform_picker_platforms()
    mk = types.InlineKeyboardMarkup(row_width=2)
    for plat in platforms:
        mk.add(types.InlineKeyboardButton(plat, callback_data=f"admplt_{plat}"))
    prompt = bot.reply_to(
        message,
        "📝 اختار المنصة الأول من الأزرار تحت، وبعدها ابعت الأرقام كل رقم في سطر.\n\n"
        "أو تقدر تستخدم الصيغة القديمة: `الرقم:المنصة` لكل سطر.",
        parse_mode="Markdown",
        reply_markup=mk,
    )
    bot.register_next_step_handler(prompt, _process_manual_add)

def txt_platform_selected_v2(call):
    """نسخة موسّعة من txt_platform_selected ترسل ملف TXT بعد الإضافة."""
    if call.from_user.id != ADMIN_ID:
        return

    platform = _normalize_platform(call.data.replace("txtplt2_", ""))
    data = user_number_state.get(call.from_user.id, {})
    lines = data.get("txt_numbers", [])

    prepared = []
    for line in lines:
        num = _normalize_number(line)
        if num:
            prepared.append({
                "number": num,
                "platform": platform,
                "source": "txt",
                "added_at": time.ctime(),
            })

    if not prepared:
        bot.send_message(call.message.chat.id, "❌ الملف لا يحتوي أرقام صالحة.")
        return

    before = list(numbers_db.get("numbers", []))
    merged = _append_numbers(prepared)
    added_items = _find_newly_added_numbers(before, merged)

    bot.send_message(
        call.message.chat.id,
        f"✅ تم إضافة {len(added_items)} رقم إلى {platform}"
    )
    log_event("TXT_IMPORT_V2", {"count": len(added_items), "platform": platform})

    if added_items:
        import io
        icon = PLATFORM_BUTTON_ICONS.get(platform, "📂")
        txt_lines = [
            f"📋 أرقام مستوردة من ملف TXT",
            f"⏱ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{icon} المنصة: {platform}",
            f"📱 عدد الأرقام: {len(added_items)}",
            "",
            f"{'='*40}",
        ]
        for item in added_items:
            country = _get_country_info(item.get("number", ""))
            txt_lines.append(f"{country['flag']} {item['number']}  |  {country['name']}")

        content = "\n".join(txt_lines).encode("utf-8")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            bot.send_document(
                call.message.chat.id,
                ("txt_import_" + timestamp + ".txt", io.BytesIO(content), "text/plain"),
                caption=f"📨 ملف الأرقام المستوردة\n✅ {len(added_items)} رقم → {icon} {platform}",
            )
        except Exception as e:
            logger.warning(f"إرسال ملف TXT بعد الاستيراد فشل: {e}")

def developer_panel_handler_v2(message):
    """نسخة محدّثة من لوحة المطور تتضمن أزرار الجلب والتصدير."""
    bot.send_message(
        message.chat.id,
        "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:",
        reply_markup=_build_developer_panel_markup()
    )

COUNTRY_PHONE_MAP = [
    ('+1', 'الولايات المتحدة / أنتيغوا وبربودا / أنغويلا / ساموا الأمريكية / بربادوس / برمودا / جزر البهاما / كندا / دومينيكا / جمهورية الدومينيكان / غرينادا / غوام / جامايكا / سانت كيتس ونيفيس / جزر كايمان / سانت لوسيا / جزر ماريانا الشمالية / مونتسرات / بورتوريكو / سانت مارتن / جزر توركس وكايكوس / ترينيداد وتوباغو / سانت فنسنت وجزر غرينادين / جزر فيرجن البريطانية / جزر فيرجن الأمريكية', '🇺🇸'),
    ('+7', 'روسيا / كازاخستان', '🇷🇺'),
    ('+20', 'مصر', '🇪🇬'),
    ('+27', 'جنوب أفريقيا', '🇿🇦'),
    ('+30', 'اليونان', '🇬🇷'),
    ('+31', 'هولندا', '🇳🇱'),
    ('+32', 'بلجيكا', '🇧🇪'),
    ('+33', 'فرنسا', '🇫🇷'),
    ('+34', 'إسبانيا', '🇪🇸'),
    ('+36', 'هنغاريا', '🇭🇺'),
    ('+39', 'إيطاليا / الفاتيكان', '🇮🇹'),
    ('+40', 'رومانيا', '🇷🇴'),
    ('+41', 'سويسرا', '🇨🇭'),
    ('+43', 'النمسا', '🇦🇹'),
    ('+44', 'المملكة المتحدة / غيرنزي / جزيرة مان / جيرسي', '🇬🇧'),
    ('+45', 'الدانمرك', '🇩🇰'),
    ('+46', 'السويد', '🇸🇪'),
    ('+47', 'النرويج / سفالبارد وجان ماين', '🇳🇴'),
    ('+48', 'بولندا', '🇵🇱'),
    ('+49', 'ألمانيا', '🇩🇪'),
    ('+51', 'بيرو', '🇵🇪'),
    ('+52', 'المكسيك', '🇲🇽'),
    ('+53', 'كوبا', '🇨🇺'),
    ('+54', 'الأرجنتين', '🇦🇷'),
    ('+55', 'البرازيل', '🇧🇷'),
    ('+56', 'تشيلي', '🇨🇱'),
    ('+57', 'كولومبيا', '🇨🇴'),
    ('+58', 'فنزويلا', '🇻🇪'),
    ('+60', 'ماليزيا', '🇲🇾'),
    ('+61', 'أستراليا / جزر كوكوس (كيلينغ) / جزيرة كريسماس', '🇦🇺'),
    ('+62', 'إندونيسيا', '🇮🇩'),
    ('+63', 'الفلبين', '🇵🇭'),
    ('+64', 'نيوزيلندا', '🇳🇿'),
    ('+65', 'سنغافورة', '🇸🇬'),
    ('+66', 'تايلاند', '🇹🇭'),
    ('+81', 'اليابان', '🇯🇵'),
    ('+82', 'كوريا الجنوبية', '🇰🇷'),
    ('+84', 'فيتنام', '🇻🇳'),
    ('+86', 'الصين', '🇨🇳'),
    ('+90', 'تركيا', '🇹🇷'),
    ('+91', 'الهند', '🇮🇳'),
    ('+92', 'باكستان', '🇵🇰'),
    ('+93', 'أفغانستان', '🇦🇫'),
    ('+94', 'سريلانكا', '🇱🇰'),
    ('+95', 'ميانمار (بورما)', '🇲🇲'),
    ('+98', 'إيران', '🇮🇷'),
    ('+211', 'جنوب السودان', '🇸🇸'),
    ('+212', 'المغرب / الصحراء الغربية', '🇲🇦'),
    ('+213', 'الجزائر', '🇩🇿'),
    ('+216', 'تونس', '🇹🇳'),
    ('+218', 'ليبيا', '🇱🇾'),
    ('+220', 'غامبيا', '🇬🇲'),
    ('+221', 'السنغال', '🇸🇳'),
    ('+222', 'موريتانيا', '🇲🇷'),
    ('+223', 'مالي', '🇲🇱'),
    ('+224', 'غينيا', '🇬🇳'),
    ('+225', 'ساحل العاج', '🇨🇮'),
    ('+226', 'بوركينا فاسو', '🇧🇫'),
    ('+227', 'النيجر', '🇳🇪'),
    ('+228', 'توغو', '🇹🇬'),
    ('+229', 'بنين', '🇧🇯'),
    ('+230', 'موريشيوس', '🇲🇺'),
    ('+231', 'ليبيريا', '🇱🇷'),
    ('+232', 'سيراليون', '🇸🇱'),
    ('+233', 'غانا', '🇬🇭'),
    ('+234', 'نيجيريا', '🇳🇬'),
    ('+235', 'تشاد', '🇹🇩'),
    ('+236', 'جمهورية أفريقيا الوسطى', '🇨🇫'),
    ('+237', 'الكاميرون', '🇨🇲'),
    ('+238', 'الرأس الأخضر', '🇨🇻'),
    ('+239', 'ساو تومي وبرينسيبي', '🇸🇹'),
    ('+240', 'غينيا الاستوائية', '🇬🇶'),
    ('+241', 'الغابون', '🇬🇦'),
    ('+242', 'الكونغو - برازافيل', '🇨🇬'),
    ('+243', 'الكونغو - كينشاسا', '🇨🇩'),
    ('+244', 'أنغولا', '🇦🇴'),
    ('+245', 'غينيا بيساو', '🇬🇼'),
    ('+246', 'الإقليم البريطاني في المحيط الهندي', '🇮🇴'),
    ('+247', 'جزيرة أسينشيون', '🇦🇨'),
    ('+248', 'سيشل', '🇸🇨'),
    ('+249', 'السودان', '🇸🇩'),
    ('+250', 'رواندا', '🇷🇼'),
    ('+251', 'إثيوبيا', '🇪🇹'),
    ('+252', 'الصومال', '🇸🇴'),
    ('+253', 'جيبوتي', '🇩🇯'),
    ('+254', 'كينيا', '🇰🇪'),
    ('+255', 'تنزانيا', '🇹🇿'),
    ('+256', 'أوغندا', '🇺🇬'),
    ('+257', 'بوروندي', '🇧🇮'),
    ('+258', 'موزمبيق', '🇲🇿'),
    ('+260', 'زامبيا', '🇿🇲'),
    ('+261', 'مدغشقر', '🇲🇬'),
    ('+262', 'روينيون / مايوت', '🇷🇪'),
    ('+263', 'زيمبابوي', '🇿🇼'),
    ('+264', 'ناميبيا', '🇳🇦'),
    ('+265', 'ملاوي', '🇲🇼'),
    ('+266', 'ليسوتو', '🇱🇸'),
    ('+267', 'بوتسوانا', '🇧🇼'),
    ('+268', 'إسواتيني', '🇸🇿'),
    ('+269', 'جزر القمر', '🇰🇲'),
    ('+290', 'سانت هيلينا / تريستان دا كونا', '🇸🇭'),
    ('+291', 'إريتريا', '🇪🇷'),
    ('+297', 'أروبا', '🇦🇼'),
    ('+298', 'جزر فارو', '🇫🇴'),
    ('+299', 'غرينلاند', '🇬🇱'),
    ('+350', 'جبل طارق', '🇬🇮'),
    ('+351', 'البرتغال', '🇵🇹'),
    ('+352', 'لوكسمبورغ', '🇱🇺'),
    ('+353', 'أيرلندا', '🇮🇪'),
    ('+354', 'آيسلندا', '🇮🇸'),
    ('+355', 'ألبانيا', '🇦🇱'),
    ('+356', 'مالطا', '🇲🇹'),
    ('+357', 'قبرص', '🇨🇾'),
    ('+358', 'فنلندا / جزر آلاند', '🇫🇮'),
    ('+359', 'بلغاريا', '🇧🇬'),
    ('+370', 'ليتوانيا', '🇱🇹'),
    ('+371', 'لاتفيا', '🇱🇻'),
    ('+372', 'إستونيا', '🇪🇪'),
    ('+373', 'مولدوفا', '🇲🇩'),
    ('+374', 'أرمينيا', '🇦🇲'),
    ('+375', 'بيلاروس', '🇧🇾'),
    ('+376', 'أندورا', '🇦🇩'),
    ('+377', 'موناكو', '🇲🇨'),
    ('+378', 'سان مارينو', '🇸🇲'),
    ('+380', 'أوكرانيا', '🇺🇦'),
    ('+381', 'صربيا', '🇷🇸'),
    ('+382', 'الجبل الأسود', '🇲🇪'),
    ('+383', 'كوسوفو', '🇽🇰'),
    ('+385', 'كرواتيا', '🇭🇷'),
    ('+386', 'سلوفينيا', '🇸🇮'),
    ('+387', 'البوسنة والهرسك', '🇧🇦'),
    ('+389', 'مقدونيا الشمالية', '🇲🇰'),
    ('+420', 'التشيك', '🇨🇿'),
    ('+421', 'سلوفاكيا', '🇸🇰'),
    ('+423', 'ليختنشتاين', '🇱🇮'),
    ('+500', 'جزر فوكلاند', '🇫🇰'),
    ('+501', 'بليز', '🇧🇿'),
    ('+502', 'غواتيمالا', '🇬🇹'),
    ('+503', 'السلفادور', '🇸🇻'),
    ('+504', 'هندوراس', '🇭🇳'),
    ('+505', 'نيكاراغوا', '🇳🇮'),
    ('+506', 'كوستاريكا', '🇨🇷'),
    ('+507', 'بنما', '🇵🇦'),
    ('+508', 'سان بيير ومكويلون', '🇵🇲'),
    ('+509', 'هايتي', '🇭🇹'),
    ('+590', 'غوادلوب / سان بارتليمي / سان مارتن', '🇬🇵'),
    ('+591', 'بوليفيا', '🇧🇴'),
    ('+592', 'غيانا', '🇬🇾'),
    ('+593', 'الإكوادور', '🇪🇨'),
    ('+594', 'غويانا الفرنسية', '🇬🇫'),
    ('+595', 'باراغواي', '🇵🇾'),
    ('+596', 'جزر المارتينيك', '🇲🇶'),
    ('+597', 'سورينام', '🇸🇷'),
    ('+598', 'أورغواي', '🇺🇾'),
    ('+599', 'كوراساو / هولندا الكاريبية', '🇨🇼'),
    ('+670', 'تيمور - ليشتي', '🇹🇱'),
    ('+672', 'جزيرة نورفولك', '🇳🇫'),
    ('+673', 'بروناي', '🇧🇳'),
    ('+674', 'ناورو', '🇳🇷'),
    ('+675', 'بابوا غينيا الجديدة', '🇵🇬'),
    ('+676', 'تونغا', '🇹🇴'),
    ('+677', 'جزر سليمان', '🇸🇧'),
    ('+678', 'فانواتو', '🇻🇺'),
    ('+679', 'فيجي', '🇫🇯'),
    ('+680', 'بالاو', '🇵🇼'),
    ('+681', 'جزر والس وفوتونا', '🇼🇫'),
    ('+682', 'جزر كوك', '🇨🇰'),
    ('+683', 'نيوي', '🇳🇺'),
    ('+685', 'ساموا', '🇼🇸'),
    ('+686', 'كيريباتي', '🇰🇮'),
    ('+687', 'كاليدونيا الجديدة', '🇳🇨'),
    ('+688', 'توفالو', '🇹🇻'),
    ('+689', 'بولينيزيا الفرنسية', '🇵🇫'),
    ('+690', 'توكيلاو', '🇹🇰'),
    ('+691', 'ميكرونيزيا', '🇫🇲'),
    ('+692', 'جزر مارشال', '🇲🇭'),
    ('+850', 'كوريا الشمالية', '🇰🇵'),
    ('+852', 'هونغ كونغ الصينية (منطقة إدارية خاصة)', '🇭🇰'),
    ('+853', 'منطقة ماكاو الإدارية الخاصة', '🇲🇴'),
    ('+855', 'كمبوديا', '🇰🇭'),
    ('+856', 'لاوس', '🇱🇦'),
    ('+880', 'بنغلاديش', '🇧🇩'),
    ('+886', 'تايوان', '🇹🇼'),
    ('+960', 'جزر المالديف', '🇲🇻'),
    ('+961', 'لبنان', '🇱🇧'),
    ('+962', 'الأردن', '🇯🇴'),
    ('+963', 'سوريا', '🇸🇾'),
    ('+964', 'العراق', '🇮🇶'),
    ('+965', 'الكويت', '🇰🇼'),
    ('+966', 'المملكة العربية السعودية', '🇸🇦'),
    ('+967', 'اليمن', '🇾🇪'),
    ('+968', 'عُمان', '🇴🇲'),
    ('+970', 'الأراضي الفلسطينية', '🇵🇸'),
    ('+971', 'الإمارات العربية المتحدة', '🇦🇪'),
    ('+972', 'إسرائيل', '🇮🇱'),
    ('+973', 'البحرين', '🇧🇭'),
    ('+974', 'قطر', '🇶🇦'),
    ('+975', 'بوتان', '🇧🇹'),
    ('+976', 'منغوليا', '🇲🇳'),
    ('+977', 'نيبال', '🇳🇵'),
    ('+992', 'طاجيكستان', '🇹🇯'),
    ('+993', 'تركمانستان', '🇹🇲'),
    ('+994', 'أذربيجان', '🇦🇿'),
    ('+995', 'جورجيا', '🇬🇪'),
    ('+996', 'قيرغيزستان', '🇰🇬'),
    ('+998', 'أوزبكستان', '🇺🇿'),
]

COUNTRY_CODE_LOOKUP = {
    re.sub(r"\D", "", code): {
        "code": code,
        "name": name,
        "flag": flag,
    }
    for code, name, flag in COUNTRY_PHONE_MAP
}

COUNTRY_CODE_PREFIXES = sorted(COUNTRY_CODE_LOOKUP.keys(), key=len, reverse=True)

def _region_to_flag(region_code: str) -> str:
    region = str(region_code or "").strip().upper()
    if len(region) == 2 and region.isalpha():
        return "".join(chr(127397 + ord(ch)) for ch in region)
    return "🌐"

def _static_country_info_from_digits(digits: str) -> dict:
    clean_digits = re.sub(r"\D", "", str(digits or ""))
    if clean_digits.startswith("00"):
        clean_digits = clean_digits[2:]

    for prefix in COUNTRY_CODE_PREFIXES:
        if clean_digits.startswith(prefix):
            info = COUNTRY_CODE_LOOKUP[prefix]
            return {
                "name": info["name"],
                "flag": info["flag"],
                "code": info["code"],
                "digits_code": prefix,
                "key": prefix or "unknown",
            }

    return {
        "name": "غير محددة",
        "flag": "🌐",
        "code": "",
        "digits_code": "",
        "key": "unknown",
    }

DEMO_COUNTRY_SAMPLES = _build_all_country_samples()

DEMO_COUNTRY_NAMES = _build_country_names_map()

def _platforms_with_numbers() -> List[str]:
    platforms = []
    for plat in _platform_picker_platforms():
        if _numbers_for_platform(plat):
            platforms.append(plat)
    return platforms

def _delete_numbers_by_platform(platform: str) -> int:
    target = _normalize_platform(platform).lower()
    before_items = list(numbers_db.get("numbers", []))
    kept_items = [
        item for item in before_items
        if _normalize_platform(item.get("platform", "General")).lower() != target
    ]
    deleted = len(before_items) - len(kept_items)
    if deleted <= 0:
        return 0
    numbers_db["numbers"] = kept_items
    save_json(NUMBERS_FILE, numbers_db)
    _refresh_dynamic_platforms()
    log_event("PLATFORM_NUMBERS_DELETED", {"platform": _normalize_platform(platform), "deleted": deleted})
    return deleted

def _build_delete_platforms_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=1)
    platforms = _platforms_with_numbers()
    for idx, plat in enumerate(platforms):
        count = len(_numbers_for_platform(plat))
        icon = PLATFORM_BUTTON_ICONS.get(plat, "📂")
        mk.add(types.InlineKeyboardButton(f"{icon} {plat} ({count})", callback_data=f"dev_delpl_{idx}"))
    mk.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="dev_delete_platform_back"))
    return mk

def _build_delete_platform_confirm_markup(platform_idx: int) -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"dev_delcfm_{platform_idx}"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="dev_delete_platforms"),
    )
    return mk

def dev_delete_platforms_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    platforms = _platforms_with_numbers()
    if not platforms:
        bot.send_message(call.message.chat.id, "📭 لا توجد منصات عليها أرقام حالياً.")
        return
    bot.send_message(
        call.message.chat.id,
        "🗂️ اختر المنصة اللي عايز تحذف كل أرقامها:",
        reply_markup=_build_delete_platforms_markup(),
    )

def dev_delete_platform_back_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:", reply_markup=_build_developer_panel_markup())

def dev_delete_platform_pick_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    platforms = _platforms_with_numbers()
    try:
        idx = int(call.data.split("_", 2)[2])
        platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, "المنصة غير صالحة", show_alert=True)
        return
    count = len(_numbers_for_platform(platform))
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        (
            f"⚠️ تأكيد حذف أرقام منصة\n\n"
            f"المنصة: {platform}\n"
            f"عدد الأرقام: {count}\n\n"
            f"لو متأكد اضغط تأكيد الحذف."
        ),
        reply_markup=_build_delete_platform_confirm_markup(idx),
    )

def dev_delete_platform_confirm_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    platforms = _platforms_with_numbers()
    try:
        idx = int(call.data.split("_", 2)[2])
        platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, "المنصة غير صالحة أو تغيّرت القائمة", show_alert=True)
        return
    deleted = _delete_numbers_by_platform(platform)
    bot.answer_callback_query(call.id, "تم تنفيذ الحذف")
    if deleted:
        bot.send_message(call.message.chat.id, f"✅ تم حذف {deleted} رقم من منصة {platform}.")
    else:
        bot.send_message(call.message.chat.id, f"📭 منصة {platform} لا تحتوي على أرقام حالياً.")

def delete_platform_command(message):
    if not is_admin(message):
        return
    try:
        platform = _normalize_platform(message.text.split(" ", 1)[1].strip())
    except Exception:
        bot.reply_to(message, "❌ استخدم: /deleteplatform اسم_المنصة")
        return
    if not platform:
        bot.reply_to(message, "❌ لازم تكتب اسم المنصة بعد الأمر.")
        return
    deleted = _delete_numbers_by_platform(platform)
    if deleted:
        bot.reply_to(message, f"✅ تم حذف {deleted} رقم من منصة {platform}.")
    else:
        bot.reply_to(message, f"📭 ما لقيتش أرقام محفوظة لمنصة {platform}.")

EMBEDDED_SITE_COOKIES = [
    {
        "name": "ivas_sms_session",
        "value": "eyJpdiI6InpselpOOHhuaWRVVG5xNm1iMWc2Y2c9PSIsInZhbHVlIjoib29sWm83VUcxbjRrL29ucXd5YVlINklNT1NiLzU4WlhCSjNyZkZIcnFuaWZSektkQlJqSGhlTFBGOGJocVFGa1lscHJML1hwRlNuWStQYnczV2RLU3FIZmFSY1dUZDh6N2I5cWRuKzM0TXYyTWE2Q2xmeWMvMFhOamlpejBySFMiLCJtYWMiOiJhNjhmMmY1Y2ZkNWNiOTEzM2ZjZmMwOGI0YjcwYmNlNDQ0YmViODc1ZTgxZDA4YmYzNjkwMmE4N2RiMDBhOGY3IiwidGFnIjoiIn0%3D",
        "domain": "www.ivasms.com",
        "path": "/",
        "expires": 1776694653.951559,
        "httpOnly": True,
        "secure": False,
        "sameSite": "lax",
        "origin": "https://www.ivasms.com"
    },
    {
        "name": "XSRF-TOKEN",
        "value": "eyJpdiI6IlpEWnlpd2VUaHlaMUhIRzlxRUNFZ3c9PSIsInZhbHVlIjoiWnpHS21DTTFMYjNQRHVySnAzakRmZUN5eWpCL2FPcEE2LytEeWtadFQrZ3MwK0hBeFczcGlCQ0dueUdLZnRRVmRvb0FpZ0ltNGlYUzBDQzVFOHFKdkpDMnd4eWlUcCtSOThBYXFkUGtSTmJuU0ZxYUxqNHJidi9jd0tuN0p4cjEiLCJtYWMiOiJiNjUwZDU5ZmJkOTEyNGE4YmQ4YTBjNzgxNTBlNzY1NWFkYmVkZGJiNjg5NmQwY2I1NmRmMDg1OWI2ZjE2ZjFhIiwidGFnIjoiIn0%3D",
        "domain": ".www.ivasms.com",
        "path": "/",
        "httpOnly": False,
        "secure": False,
        "sameSite": "unspecified",
        "origin": "https://www.ivasms.com"
    },
    {
        "name": "XSRF-TOKEN",
        "value": "eyJpdiI6IlBYOWFnK0o3VUs2ZFFpZ1FQQ0VxOUE9PSIsInZhbHVlIjoidjJIa1VvV2Vkbi91cXB1ZjFCU0xvbzkyejB0YWJkaGhVOXRPZkVjanJ2alhtYUJqZTRyRXFoLzZFeThOTkljOTU3U1drK3BSWUpBVVByWVFYTStvVDNJYjF0SDBrWmtrSXQ3NmtmMnpHcWpEUlgzczdIaHpJVlpaU1pmdzlQRWkiLCJtYWMiOiJmMDE0MDJmMmUxNzQzNDY3N2M3NTQyMWIwYzRjZWFlZTAzMjQ0MTZkNGRiYzM0MzA2MTI2MTEzODM1MmIzY2Y2IiwidGFnIjoiIn0%3D",
        "domain": "www.ivasms.com",
        "path": "/",
        "expires": 1776694653.951353,
        "httpOnly": False,
        "secure": False,
        "sameSite": "lax",
        "origin": "https://www.ivasms.com"
    }
]

# مهم: لا تمسح قيم الكوكيز هنا. البوت يعتمد على SITE_COOKIE / SITE_COOKIE_FILE
# أو runtime_cookies.json للوصول الصحيح لصفحات الموقع.

ALLOWED_PLATFORMS = ["WhatsApp", "Facebook", "TikTok", "Telegram"]

ALLOWED_PLATFORM_SET = set(ALLOWED_PLATFORMS)

# AUTO_SYNC_NUMBERS controlled at top of file

AUTO_SYNC_INTERVAL_MINUTES = max(1, int(_get("AUTO_SYNC_INTERVAL_MINUTES", "3") or "3"))

# INITIAL_SYNC_ON_START controlled via environment

DEFAULT_PLATFORMS = list(ALLOWED_PLATFORMS)

dynamic_platforms = list(ALLOWED_PLATFORMS)

SPECIAL_PLATFORMS = set()

PLATFORM_BUTTON_ICONS = {
    "WhatsApp": "💬",
    "Facebook": "📘",
    "TikTok": "🎵",
    "Telegram": "✈️",
}

DEMO_SERVICE_META = {
    "WhatsApp": {"icon": "💬", "label": "WhatsApp"},
    "Facebook": {"icon": "📘", "label": "Facebook"},
    "TikTok": {"icon": "🎵", "label": "TikTok"},
    "Telegram": {"icon": "✈️", "label": "Telegram"},
}

PLATFORM_CANONICAL_ALIASES = {
    "whatsapp": "WhatsApp",
    "whats app": "WhatsApp",
    "واتساب": "WhatsApp",
    "واتس اب": "WhatsApp",
    "facebook": "Facebook",
    "face book": "Facebook",
    "فيسبوك": "Facebook",
    "فيس بوك": "Facebook",
    "tiktok": "TikTok",
    "tik tok": "TikTok",
    "تيك توك": "TikTok",
    "تيكتوك": "TikTok",
    "telegram": "Telegram",
    "تيليجرام": "Telegram",
    "تلجرام": "Telegram",
}

def _normalize_cookie_payload(payload) -> List[Dict]:
    if isinstance(payload, dict):
        if isinstance(payload.get("cookies"), list):
            items = payload.get("cookies")
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("تنسيق الكوكيز لازم يكون JSON list أو object")

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        value = str(item.get("value") or "").strip()
        if not name or not value:
            continue
        row = {
            "name": name,
            "value": value,
            "domain": str(item.get("domain") or _cookie_host()).strip(),
            "path": str(item.get("path") or "/").strip() or "/",
            "httpOnly": bool(item.get("httpOnly", False)),
            "secure": bool(item.get("secure", False)),
            "sameSite": str(item.get("sameSite") or "lax").strip() or "lax",
        }
        if "expires" in item:
            row["expires"] = item.get("expires")
        if "expirationDate" in item:
            row["expirationDate"] = item.get("expirationDate")
        normalized.append(row)

    if not normalized:
        raise ValueError("مافيش كوكيز صالحة للحفظ")
    return normalized

def _cookie_identity(item: Dict) -> Tuple[str, str, str]:
    return (
        str(item.get("name") or "").strip().lower(),
        str(item.get("domain") or _cookie_host()).strip().lower(),
        str(item.get("path") or "/").strip() or "/",
    )


def _merge_cookie_items(existing_items, new_items) -> List[Dict]:
    merged: List[Dict] = []
    index_map: Dict[Tuple[str, str, str], int] = {}

    for item in _normalize_cookie_payload(existing_items or []):
        key = _cookie_identity(item)
        if key in index_map:
            merged[index_map[key]] = item
        else:
            index_map[key] = len(merged)
            merged.append(item)

    for item in _normalize_cookie_payload(new_items):
        key = _cookie_identity(item)
        if key in index_map:
            merged[index_map[key]] = item
        else:
            index_map[key] = len(merged)
            merged.append(item)

    if not merged:
        raise ValueError("مافيش كوكيز صالحة للحفظ")
    return merged


def _extract_cookie_json_text(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    if not text:
        return ""
    command = text.split(None, 1)[0].split("@", 1)[0].lower()
    if command in {"/setcookies", "/setcookie", "/addcookies", "/appendcookies"}:
        parts = text.split(None, 1)
        text = parts[1].strip() if len(parts) > 1 else ""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _extract_cookie_delete_text(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    if not text:
        return ""
    command = text.split(None, 1)[0].split("@", 1)[0].lower()
    if command in {"/delcookies", "/deletecookies", "/removecookies"}:
        parts = text.split(None, 1)
        return parts[1].strip() if len(parts) > 1 else ""
    return text


def _load_runtime_cookies(session: requests.Session) -> bool:
    runtime_items = load_json(RUNTIME_COOKIES_FILE, [])
    if not isinstance(runtime_items, list) or not runtime_items:
        return False
    return _load_cookie_items(session, runtime_items, "ملف runtime_cookies.json")


def _save_runtime_cookies(payload, append: bool = False) -> int:
    normalized = _normalize_cookie_payload(payload)
    if append:
        normalized = _merge_cookie_items(_runtime_cookie_items(), normalized)
    save_json(RUNTIME_COOKIES_FILE, normalized)
    return len(normalized)


def _delete_runtime_cookies(selected_text: str) -> Tuple[int, int, List[str]]:
    items = _runtime_cookie_items()
    if not items:
        raise ValueError("لا توجد Runtime cookies محفوظة حالياً.")

    tokens = [token.strip() for token in re.split(r"[,\n]+", str(selected_text or "").strip()) if token.strip()]
    if not tokens:
        raise ValueError("حدد أرقام الكوكيز أو أسماءها للحذف.")

    numeric_indexes = set()
    text_selectors = set()
    for token in tokens:
        if token.isdigit():
            numeric_indexes.add(int(token))
        else:
            text_selectors.add(token.lower())

    kept_items: List[Dict] = []
    removed_labels: List[str] = []
    for idx, item in enumerate(items, 1):
        name = str(item.get("name") or "").strip()
        domain = str(item.get("domain") or _cookie_host()).strip()
        path = str(item.get("path") or "/").strip() or "/"
        composite = f"{name}@{domain}{path}".lower()
        if idx in numeric_indexes or name.lower() in text_selectors or composite in text_selectors:
            removed_labels.append(f"{idx}. {name} | {domain}{path}")
        else:
            kept_items.append(item)

    if not removed_labels:
        raise ValueError("مافيش كوكيز مطابقة للعناصر المحددة.")

    if kept_items:
        save_json(RUNTIME_COOKIES_FILE, kept_items)
    else:
        try:
            if RUNTIME_COOKIES_FILE.exists():
                RUNTIME_COOKIES_FILE.unlink()
        except Exception:
            save_json(RUNTIME_COOKIES_FILE, [])

    return len(removed_labels), len(kept_items), removed_labels


def _build_cookie_delete_result(removed_count: int, remaining_count: int, removed_labels: List[str]) -> str:
    preview = "\n".join(removed_labels[:12])
    extra = ""
    if len(removed_labels) > 12:
        extra = f"\n... +{len(removed_labels) - 12} عناصر إضافية"
    return (
        f"🗑️ تم حذف {removed_count} كوكيز محددة بنجاح.\n"
        f"📦 المتبقي الآن: {remaining_count} كوكيز\n\n"
        f"{preview}{extra}"
    )


def setcookies_command(message):
    if not is_admin(message):
        return

    payload_text = _extract_cookie_json_text(getattr(message, "text", ""))
    if payload_text:
        try:
            saved_count = _save_runtime_cookies(json.loads(payload_text), append=False)
            bot.reply_to(message, f"✅ تم استبدال Runtime cookies بالكامل. العدد المحفوظ الآن: {saved_count}")
        except Exception as cookie_save_err:
            bot.reply_to(message, f"❌ فشل حفظ الكوكيز: {cookie_save_err}")
        return

    prompt = bot.reply_to(
        message,
        "🍪 ابعت JSON الكوكيز هنا مباشرةً لاستبدال Runtime cookies الحالية بالكامل.\n\n"
        "لو عايز تضيف 4 كوكيز زيادة أو أي عدد إضافي بدون مسح الموجود استخدم /addcookies\n"
        "وللإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_setcookies_step)


def addcookies_command(message):
    if not is_admin(message):
        return

    payload_text = _extract_cookie_json_text(getattr(message, "text", ""))
    if payload_text:
        try:
            saved_count = _save_runtime_cookies(json.loads(payload_text), append=True)
            bot.reply_to(message, f"✅ تم دمج الكوكيز الجديدة مع الحالية بنجاح. الإجمالي الآن: {saved_count} كوكيز")
        except Exception as cookie_save_err:
            bot.reply_to(message, f"❌ فشل إضافة الكوكيز: {cookie_save_err}")
        return

    prompt = bot.reply_to(
        message,
        "➕ ابعت JSON الكوكيز التي تريد إضافتها فوق الموجودة حالياً.\n\n"
        "تقدر تضيف 4 كوكيز زيادة أو أكثر، وسيتم دمجها بدون حذف القديم إلا إذا تكرر نفس name/domain/path.\n"
        "وللإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_addcookies_step)


def _process_setcookies_step(message):
    if not is_admin(message):
        return
    text = str(getattr(message, "text", "") or "").strip()
    if not text:
        bot.reply_to(message, "❌ ما وصلنيش أي JSON. حاول تاني.")
        return
    if text.lower() == "/cancel":
        bot.reply_to(message, "✅ تم إلغاء تحديث الكوكيز.")
        return
    try:
        saved_count = _save_runtime_cookies(json.loads(_extract_cookie_json_text(text)), append=False)
        bot.reply_to(message, f"✅ تم استبدال Runtime cookies بنجاح. العدد المحفوظ الآن: {saved_count}")
    except Exception as cookie_step_err:
        bot.reply_to(message, f"❌ JSON غير صالح أو فيه مشكلة: {cookie_step_err}")


def _process_addcookies_step(message):
    if not is_admin(message):
        return
    text = str(getattr(message, "text", "") or "").strip()
    if not text:
        bot.reply_to(message, "❌ ما وصلنيش أي JSON. حاول تاني.")
        return
    if text.lower() == "/cancel":
        bot.reply_to(message, "✅ تم إلغاء إضافة الكوكيز.")
        return
    try:
        saved_count = _save_runtime_cookies(json.loads(_extract_cookie_json_text(text)), append=True)
        bot.reply_to(message, f"✅ تم دمج الكوكيز الجديدة بنجاح. الإجمالي الآن: {saved_count}")
    except Exception as cookie_step_err:
        bot.reply_to(message, f"❌ JSON غير صالح أو فيه مشكلة: {cookie_step_err}")


def delcookies_command(message):
    if not is_admin(message):
        return

    selected_text = _extract_cookie_delete_text(getattr(message, "text", ""))
    if selected_text:
        try:
            removed_count, remaining_count, removed_labels = _delete_runtime_cookies(selected_text)
            _chunked_send(message.chat.id, _build_cookie_delete_result(removed_count, remaining_count, removed_labels))
        except Exception as delete_cookie_err:
            bot.reply_to(message, f"❌ فشل حذف الكوكيز المحددة: {delete_cookie_err}")
        return

    prompt = bot.reply_to(
        message,
        "🗑️ ابعت أرقام الكوكيز أو أسماءها لحذفها من Runtime cookies.\n\n"
        "أمثلة:\n"
        "1,3,5\n"
        "XSRF-TOKEN,ivas_sms_session\n"
        "XSRF-TOKEN@www.ivasms.com/\n\n"
        "وللإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_delcookies_step)


def _process_delcookies_step(message):
    if not is_admin(message):
        return
    text = str(getattr(message, "text", "") or "").strip()
    if not text:
        bot.reply_to(message, "❌ ما وصلنيش أي عناصر للحذف. حاول تاني.")
        return
    if text.lower() == "/cancel":
        bot.reply_to(message, "✅ تم إلغاء حذف الكوكيز.")
        return
    try:
        removed_count, remaining_count, removed_labels = _delete_runtime_cookies(_extract_cookie_delete_text(text))
        _chunked_send(message.chat.id, _build_cookie_delete_result(removed_count, remaining_count, removed_labels))
    except Exception as delete_cookie_err:
        bot.reply_to(message, f"❌ فشل حذف الكوكيز المحددة: {delete_cookie_err}")


def clearcookies_command(message):
    if not is_admin(message):
        return
    try:
        if RUNTIME_COOKIES_FILE.exists():
            RUNTIME_COOKIES_FILE.unlink()
            bot.reply_to(message, "🗑️ تم حذف runtime_cookies.json والرجوع للكوكيز المدمجة داخل الملف.")
        else:
            bot.reply_to(message, "ℹ️ لا يوجد ملف runtime_cookies.json حالياً.")
    except Exception as clear_cookie_err:
        bot.reply_to(message, f"❌ تعذر حذف ملف الكوكيز: {clear_cookie_err}")

def _summarize_cookie_items(items) -> str:
    rows = []
    if not isinstance(items, list) or not items:
        return "لا توجد كوكيز محفوظة حالياً."
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "?")
        domain = str(item.get("domain") or _cookie_host())
        path = str(item.get("path") or "/")
        value = str(item.get("value") or "")
        preview = (value[:10] + "..." + value[-6:]) if len(value) > 22 else value
        rows.append(f"{idx}. {name} | {domain}{path} | {preview}")
    return "\n".join(rows) if rows else "لا توجد كوكيز محفوظة حالياً."

def _runtime_cookie_items() -> List[Dict]:
    data = load_json(RUNTIME_COOKIES_FILE, [])
    return data if isinstance(data, list) else []

def _cookie_help_text() -> str:
    runtime_count = len(_runtime_cookie_items())
    embedded_count = len(EMBEDDED_SITE_COOKIES) if isinstance(EMBEDDED_SITE_COOKIES, list) else 0
    return (
        "🍪 إدارة الكوكيز\n\n"
        f"• Runtime cookies الحالية: {runtime_count}\n"
        f"• Embedded cookies الاحتياطية: {embedded_count}\n\n"
        "الأوامر المتاحة:\n"
        "• /cookies ← لوحة إدارة الكوكيز\n"
        "• /setcookies ← استبدال كل Runtime cookies بصيغة JSON\n"
        "• /addcookies ← إضافة / دمج كوكيز جديدة فوق الحالية (تقدر تضيف 4 أو أكثر)\n"
        "• /delcookies ← حذف كوكيز محددة بالرقم أو الاسم\n"
        "• /showcookies ← عرض الكوكيز الحالية بشكل مختصر\n"
        "• /clearcookies ← حذف كل Runtime cookies والرجوع للمضمّنة\n\n"
        "ملاحظات:\n"
        "• /setcookies يستبدل الكل\n"
        "• /addcookies يضيف بدون مسح الموجود\n"
        "• /delcookies يقبل مثل: 1,3 أو XSRF-TOKEN\n\n"
        "مثال JSON:\n"
        "[\n"
        "  {\"name\": \"XSRF-TOKEN\", \"value\": \"...\", \"domain\": \"www.ivasms.com\", \"path\": \"/\"},\n"
        "  {\"name\": \"ivas_sms_session\", \"value\": \"...\", \"domain\": \"www.ivasms.com\", \"path\": \"/\"}\n"
        "]"
    )

def dev_cookie_center_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("👁️ عرض الكوكيز", callback_data="dev_cookie_show"))
    mk.add(types.InlineKeyboardButton("♻️ استبدال كل الكوكيز", callback_data="dev_cookie_set"))
    mk.add(types.InlineKeyboardButton("➕ إضافة / دمج كوكيز", callback_data="dev_cookie_add"))
    mk.add(types.InlineKeyboardButton("🗑️ حذف كوكيز محددة", callback_data="dev_cookie_delete"))
    mk.add(types.InlineKeyboardButton("🚨 حذف كل Runtime Cookies", callback_data="dev_cookie_clear"))
    mk.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="dev_cookie_back"))
    bot.send_message(call.message.chat.id, _cookie_help_text(), reply_markup=mk)

def dev_cookie_show_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    runtime_items = _runtime_cookie_items()
    text = (
        "🍪 الكوكيز الحالية\n\n"
        f"Runtime cookies ({len(runtime_items)}):\n{_summarize_cookie_items(runtime_items)}\n\n"
        f"Embedded cookies ({len(EMBEDDED_SITE_COOKIES)}):\n{_summarize_cookie_items(EMBEDDED_SITE_COOKIES)}"
    )
    _chunked_send(call.message.chat.id, text)

def dev_cookie_set_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        "♻️ ابعت JSON الكوكيز هنا لاستبدال Runtime cookies الحالية بالكامل.\n\n"
        "الصيغة المقبولة: List أو Object يحتوي name / value / domain / path\n"
        "للإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_setcookies_step)


def dev_cookie_add_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        "➕ ابعت JSON الكوكيز التي تريد إضافتها فوق الموجودة حالياً.\n\n"
        "تقدر تضيف 4 كوكيز زيادة أو أكثر، وسيتم دمجها تلقائياً.\n"
        "للإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_addcookies_step)


def dev_cookie_delete_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        "🗑️ ابعت أرقام الكوكيز أو أسماءها لحذفها.\n\n"
        "أمثلة:\n"
        "1,2,4\n"
        "XSRF-TOKEN,ivas_sms_session\n"
        "XSRF-TOKEN@www.ivasms.com/\n\n"
        "للإلغاء اكتب: /cancel"
    )
    bot.register_next_step_handler(prompt, _process_delcookies_step)


def dev_cookie_clear_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    try:
        if RUNTIME_COOKIES_FILE.exists():
            RUNTIME_COOKIES_FILE.unlink()
            bot.send_message(call.message.chat.id, "🗑️ تم حذف Runtime cookies. تم الرجوع للكوكيز المدمجة داخل الملف.")
            log_event("COOKIES_CLEARED", {"by": call.from_user.id})
        else:
            bot.send_message(call.message.chat.id, "ℹ️ لا يوجد runtime_cookies.json حالياً.")
    except Exception as clear_cookie_err:
        bot.send_message(call.message.chat.id, f"❌ تعذر حذف ملف الكوكيز: {clear_cookie_err}")

def dev_cookie_back_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:", reply_markup=_build_developer_panel_markup())

def showcookies_command(message):
    if not is_admin(message):
        return
    runtime_items = _runtime_cookie_items()
    text = (
        "🍪 الكوكيز الحالية\n\n"
        f"Runtime cookies ({len(runtime_items)}):\n{_summarize_cookie_items(runtime_items)}\n\n"
        f"Embedded cookies ({len(EMBEDDED_SITE_COOKIES)}):\n{_summarize_cookie_items(EMBEDDED_SITE_COOKIES)}"
    )
    _chunked_send(message.chat.id, text)

def cookies_center_command(message):
    if not is_admin(message):
        return
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("👁️ عرض الكوكيز", callback_data="dev_cookie_show"))
    mk.add(types.InlineKeyboardButton("♻️ استبدال كل الكوكيز", callback_data="dev_cookie_set"))
    mk.add(types.InlineKeyboardButton("➕ إضافة / دمج كوكيز", callback_data="dev_cookie_add"))
    mk.add(types.InlineKeyboardButton("🗑️ حذف كوكيز محددة", callback_data="dev_cookie_delete"))
    mk.add(types.InlineKeyboardButton("🚨 حذف كل Runtime Cookies", callback_data="dev_cookie_clear"))
    bot.reply_to(message, _cookie_help_text(), reply_markup=mk)

# AUTO_SYNC_NUMBERS controlled at top of file
INITIAL_SYNC_ON_START = _env_flag("INITIAL_SYNC_ON_START", False)

def _report_site_platforms(chat_id: int):
    try:
        data = _scan_site_platforms_live()
        platforms = data.get("platforms", [])
        if not platforms:
            bot.send_message(chat_id, "⚠️ ماقدرتش أستخرج منصات من الموقع حالياً. راجع الكوكيز أو الحساب.")
            return
        lines = [
            "🧭 فحص المنصات المتاحة في الموقع",
            "",
            f"📚 عدد المنصات المكتشفة: {len(platforms)}",
            f"📦 المنصات المحفوظة حالياً داخل البوت: {len(dynamic_platforms)}",
            "",
        ]
        for idx, platform in enumerate(platforms, 1):
            count = data.get("counts", {}).get(platform, 0)
            source_text = ", ".join(data.get("sources", {}).get(platform, []))
            suffix = f" | داخل البوت: {count}" if count else ""
            lines.append(f"{idx}. {platform}{suffix} | المصدر: {source_text}")
        _chunked_send(chat_id, "\n".join(lines))
    except Exception as report_err:
        logger.exception(f"Site platform report error: {report_err}")
        bot.send_message(chat_id, f"❌ حصل خطأ أثناء فحص المنصات: {report_err}")

def _collect_codes_from_window(session: requests.Session, csrf: str, start_date: datetime.date, end_date: datetime.date, label: str, max_ranges: int = 8, max_numbers_per_range: int = 5, max_entries: int = 20) -> List[Dict]:
    rows: List[Dict] = []
    seen = set()
    summary_resp = session.post(
        f"{SITE_URL}/portal/sms/received/getsms",
        data={"from": start_date.isoformat(), "to": end_date.isoformat(), "_token": csrf},
        timeout=30,
    )
    if summary_resp.status_code != 200:
        return rows

    ranges = _extract_ranges_from_summary(summary_resp.text)[:max_ranges]
    for range_name in ranges:
        range_resp = session.post(
            f"{SITE_URL}/portal/sms/received/getsms/number",
            data={
                "_token": csrf,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": range_name,
            },
            timeout=30,
        )
        if range_resp.status_code != 200:
            continue
        numbers = _extract_number_rows(range_resp.text)[:max_numbers_per_range]
        for number in numbers:
            sms_resp = session.post(
                f"{SITE_URL}/portal/sms/received/getsms/number/sms",
                data={
                    "_token": csrf,
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "Number": number.lstrip("+"),
                    "Range": range_name,
                },
                timeout=30,
            )
            if sms_resp.status_code != 200:
                continue
            for entry in _extract_sms_entries(sms_resp.text):
                code = str(entry.get("code") or "").strip()
                if not code:
                    continue
                message_text = re.sub(r"\s+", " ", str(entry.get("message") or "")).strip()
                key = (number, code, entry.get("time", ""), range_name, label)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "bucket": label,
                    "platform": _platform_label_loose(range_name) or _normalize_platform(range_name),
                    "range": str(range_name).strip(),
                    "number": _normalize_number(number),
                    "code": code,
                    "time": str(entry.get("time") or "").strip(),
                    "sender": str(entry.get("sender") or "").strip(),
                    "message": message_text,
                })
                if len(rows) >= max_entries:
                    return rows
    return rows

def _fetch_site_codes_snapshot() -> Dict:
    session = _build_site_session()
    page_resp = session.get(f"{SITE_URL}/portal/sms/received", timeout=20)
    csrf = _extract_csrf_token(getattr(page_resp, "text", ""))
    if not csrf:
        raise RuntimeError("تعذر استخراج CSRF token من صفحة الرسائل")

    today = datetime.date.today()
    recent_start = today - datetime.timedelta(days=30)
    old_start = today - datetime.timedelta(days=365)
    old_end = today - datetime.timedelta(days=31)

    recent_rows = _collect_codes_from_window(session, csrf, recent_start, today, "new", max_ranges=100, max_numbers_per_range=50, max_entries=1000)
    old_rows = []
    if old_start <= old_end:
        old_rows = _collect_codes_from_window(session, csrf, old_start, old_end, "old", max_ranges=50, max_numbers_per_range=20, max_entries=500)

    return {
        "recent": recent_rows,
        "old": old_rows,
        "recent_window": f"{recent_start.isoformat()} → {today.isoformat()}",
        "old_window": f"{old_start.isoformat()} → {old_end.isoformat()}",
    }

def _format_site_code_rows(title: str, rows: List[Dict], window_text: str) -> str:
    lines = [title, f"🗓️ الفترة: {window_text}", ""]
    if not rows:
        lines.append("لا توجد أكواد مطابقة في هذه الفترة.")
        return "\n".join(lines)
    for idx, row in enumerate(rows, 1):
        snippet = str(row.get("message", "")).strip()
        if len(snippet) > 90:
            snippet = snippet[:90] + "…"
        lines.append(
            f"{idx}. {row.get('platform', 'General')} | {row.get('number', '')} | الكود: {row.get('code', '')} | الوقت: {row.get('time', '')}"
        )
        if row.get("sender"):
            lines.append(f"   المرسل: {row.get('sender')}")
        if snippet:
            lines.append(f"   الرسالة: {snippet}")
    return "\n".join(lines)

def _report_site_codes(chat_id: int):
    try:
        data = _fetch_site_codes_snapshot()
        text = "\n\n".join([
            "🧾 جلب الأكواد الجديدة والقديمة من الموقع",
            _format_site_code_rows("🆕 الأكواد الجديدة", data.get("recent", []), data.get("recent_window", "")),
            _format_site_code_rows("🗂️ الأكواد القديمة", data.get("old", []), data.get("old_window", "")),
        ])
        _chunked_send(chat_id, text)
    except Exception as codes_err:
        logger.exception(f"Site codes report error: {codes_err}")
        bot.send_message(chat_id, f"❌ حصل خطأ أثناء جلب أكواد الموقع: {codes_err}")

def dev_site_platforms_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id, "الميزة متوقفة", show_alert=True)
    bot.send_message(call.message.chat.id, "⛔ فحص منصات الموقع متوقف لأن البوت صار يعتمد على الإضافة اليدوية فقط.")

def dev_site_codes_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id, "الميزة متوقفة", show_alert=True)
    bot.send_message(call.message.chat.id, "⛔ جلب أكواد الموقع متوقف لأن الجلب من الموقع تم تعطيله.")

def siteplatforms_command(message):
    if not is_admin(message):
        return
    bot.reply_to(message, "⛔ أمر فحص منصات الموقع متوقف. البوت الآن يدعم الإضافة اليدوية فقط.")

def sitecodes_command(message):
    if not is_admin(message):
        return
    bot.reply_to(message, "⛔ أمر جلب أكواد الموقع متوقف لأن ربط الموقع تم تعطيله.")

GENERAL_PLATFORM_NAME = "General"

if GENERAL_PLATFORM_NAME not in ALLOWED_PLATFORMS:
    ALLOWED_PLATFORMS = [GENERAL_PLATFORM_NAME] + [p for p in ALLOWED_PLATFORMS if p != GENERAL_PLATFORM_NAME]

ALLOWED_PLATFORM_SET = set(ALLOWED_PLATFORMS)

PLATFORM_BUTTON_ICONS.setdefault(GENERAL_PLATFORM_NAME, "📁")

DEMO_SERVICE_META.setdefault(GENERAL_PLATFORM_NAME, {"icon": "📁", "label": GENERAL_PLATFORM_NAME})

def _build_general_number_row(item: Dict) -> Dict:
    row = _enrich_number_item(item)
    if not row:
        return {}
    row = dict(row)
    row["platform"] = GENERAL_PLATFORM_NAME
    row["site_section"] = GENERAL_PLATFORM_NAME
    return row

_live_test_codes_monitor_started = False
LIVE_TEST_CODES_MONITOR_ENABLED = _env_flag("LIVE_TEST_CODES_MONITOR_ENABLED", False)
LIVE_TEST_CODES_POLL_INTERVAL_SECONDS = max(10, int(str(_get("LIVE_TEST_CODES_POLL_INTERVAL_SECONDS", "20") or "20").strip() or "20"))

_live_test_codes_seen = set()

_live_test_codes_lock = threading.Lock()

def _live_test_code_key(item: Dict) -> str:
    number = _normalize_number(item.get("number", ""))
    code = str(item.get("code") or "").strip()
    service = _normalize_platform(item.get("service") or item.get("platform") or GENERAL_PLATFORM_NAME)
    return f"{number}::{code}::{service}"

def _live_test_codes_loop_safe():
    """
    مراقبة Test-System codes وإرسالها للقناة تلقائياً.
    - يعمل في الخلفية باستمرار
    - يتجاهل الأكواد المكرّرة (cache بحد أقصى 500 مدخل)
    - ينظّف الـ cache بعد كل 100 دورة لمنع تسرّب الذاكرة
    - يُعيد المحاولة عند الخطأ بتأخير تصاعدي
    """
    POLL_INTERVAL   = LIVE_TEST_CODES_POLL_INTERVAL_SECONDS
    MAX_CACHE_SIZE  = 500         # الحد الأقصى لإدخالات cache
    CACHE_CLEAN_EVERY = 100       # تنظيف بعد عدد هذه الدورات
    cycle_count = 0
    error_backoff = POLL_INTERVAL  # تأخير يتضاعف عند الأخطاء المتتالية

    while True:
        cycle_count += 1

        # ─── تنظيف الـ cache دورياً لمنع تسرّب الذاكرة ───
        if cycle_count % CACHE_CLEAN_EVERY == 0:
            with _live_test_codes_lock:
                if len(_live_test_codes_seen) > MAX_CACHE_SIZE:
                    # احتفظ بآخر نصف المدخلات فقط
                    keep = list(_live_test_codes_seen)[-MAX_CACHE_SIZE // 2:]
                    _live_test_codes_seen.clear()
                    _live_test_codes_seen.update(keep)
                    logger.debug(f"🧹 [LIVE-CODES] تم تنظيف cache: تم الإبقاء على {len(keep)} مدخل")

        try:
            codes = fetch_live_test_codes()
            if codes:
                new_codes_count = 0
                for item in codes:
                    if not item.get("code"):
                        continue
                    cache_key   = _live_test_code_key(item)
                    channel_key = f"channel::{item.get('number', '')}::{item.get('code', '')}"
                    with _live_test_codes_lock:
                        if cache_key in _live_test_codes_seen or channel_key in sent_codes_cache:
                            continue
                        _live_test_codes_seen.add(cache_key)
                    send_codes_to_channel([item])
                    new_codes_count += 1
                if new_codes_count:
                    logger.info(f"📩 [LIVE-CODES] تم إرسال {new_codes_count} كود جديد للقناة")
            error_backoff = POLL_INTERVAL  # إعادة التأخير للطبيعي عند النجاح

        except Exception as live_codes_err:
            logger.warning(f"⚠️ [LIVE-CODES] خطأ في المراقبة: {live_codes_err}")
            error_backoff = min(error_backoff * 2, 120)  # تأخير تصاعدي حتى 120 ثانية
            time.sleep(error_backoff)
            continue

        time.sleep(POLL_INTERVAL)

def _start_live_test_codes_monitor_once():
    global _live_test_codes_monitor_started
    if not LIVE_TEST_CODES_MONITOR_ENABLED:
        logger.info("⏸️ مراقبة Live Test Codes متوقفة عبر الإعدادات.")
        return
    if _live_test_codes_monitor_started:
        return
    _live_test_codes_monitor_started = True
    threading.Thread(target=_live_test_codes_loop_safe, daemon=True).start()
    logger.info("✅ تم تشغيل مراقبة Test System ونشر الأكواد للقناة تلقائياً")

GENERAL_BUCKET_KEY = "general_numbers"

def _build_persisted_general_rows(base_items: Optional[List[Dict]] = None) -> List[Dict]:
    rows: List[Dict] = []
    seen = set()
    for item in list(base_items if base_items is not None else numbers_db.get("numbers", [])):
        row = _enrich_number_item(item)
        number = row.get("number", "")
        if not number or number in seen:
            continue
        seen.add(number)
        row["platform"] = GENERAL_PLATFORM_NAME
        row["site_section"] = GENERAL_PLATFORM_NAME
        row.setdefault("derived_from", _normalize_platform(item.get("platform", GENERAL_PLATFORM_NAME)))
        rows.append(row)
    return rows

def _rebuild_general_bucket(persist: bool = True) -> List[Dict]:
    bucket = _build_persisted_general_rows(numbers_db.get("numbers", []))
    numbers_db[GENERAL_BUCKET_KEY] = bucket
    if persist:
        save_json(NUMBERS_FILE, numbers_db)
    return bucket

_defensive_general_bucket_bootstrap_done = False

def _bootstrap_general_bucket_once():
    global _defensive_general_bucket_bootstrap_done
    if _defensive_general_bucket_bootstrap_done:
        return
    _defensive_general_bucket_bootstrap_done = True
    try:
        _rebuild_general_bucket(persist=False)
    except Exception as general_bucket_err:
        logger.warning(f"تعذر تجهيز General bucket: {general_bucket_err}")

def _build_db_audit_report() -> str:
    rows = _dedupe_numbers(numbers_db.get("numbers", []))
    general_rows = _build_persisted_general_rows(rows)
    stored_general_rows = _dedupe_numbers(numbers_db.get(GENERAL_BUCKET_KEY, []))
    source_counts: Dict[str, int] = {}
    platform_counts: Dict[str, int] = {}
    for item in rows:
        source = str(item.get("source") or "unknown").strip() or "unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
        plat = _normalize_platform(item.get("platform", GENERAL_PLATFORM_NAME))
        platform_counts[plat] = platform_counts.get(plat, 0) + 1

    missing_general = max(0, len(general_rows) - len(stored_general_rows))
    duplicate_gap = max(0, len(numbers_db.get("numbers", [])) - len(rows))
    lines = [
        "🧪 تدقيق قاعدة الأرقام",
        "",
        f"📱 السجلات الفعلية: {len(numbers_db.get('numbers', []))}",
        f"✅ السجلات بعد إزالة التكرار: {len(rows)}",
        f"📁 General المخزن فعلياً: {len(stored_general_rows)}",
        f"🧮 General المتوقع من القاعدة: {len(general_rows)}",
        f"♻️ فجوة التكرار: {duplicate_gap}",
        f"🧷 عناصر General الناقصة: {missing_general}",
        "",
        "📦 حسب المصدر:",
    ]
    for source, count in sorted(source_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"• {source}: {count}")
    lines.append("")
    lines.append("🌐 حسب المنصة:")
    for plat, count in sorted(platform_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]:
        lines.append(f"• {plat}: {count}")
    lines.append("")
    lines.append("ℹ️ هذا التدقيق داخلي لقاعدة الأرقام والتخزين فقط.")
    return "\n".join(lines)

def dev_db_audit_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _bootstrap_general_bucket_once()
    _chunked_send(call.message.chat.id, _build_db_audit_report())

def db_audit_command(message):
    if not is_admin(message):
        return
    _bootstrap_general_bucket_once()
    _chunked_send(message.chat.id, _build_db_audit_report())

ALL_NUMBERS_PLATFORM_NAME = "جميع الارقام"

PLATFORM_CANONICAL_ALIASES[_platform_alias_key(ALL_NUMBERS_PLATFORM_NAME)] = "General"

PLATFORM_CANONICAL_ALIASES.setdefault(_platform_alias_key("كل الارقام"), "General")

PLATFORM_CANONICAL_ALIASES.setdefault(_platform_alias_key("all numbers"), "General")

PLATFORM_BUTTON_ICONS.setdefault("General", "📁")

PLATFORM_BUTTON_ICONS[ALL_NUMBERS_PLATFORM_NAME] = PLATFORM_BUTTON_ICONS.get("General", "📁")

DEMO_SERVICE_META.setdefault(ALL_NUMBERS_PLATFORM_NAME, {"icon": "📁", "label": ALL_NUMBERS_PLATFORM_NAME})

site_add_state: Dict[int, Dict] = {}

_site_add_cache: Dict[str, Dict] = {"data": {}, "timestamp": 0.0}

SITE_ADD_AUTO_REFRESH_ATTEMPTS = max(2, int(str(_get("SITE_ADD_AUTO_REFRESH_ATTEMPTS", "3") or "3").strip() or "3"))
SITE_ADD_AUTO_REFRESH_DELAY_SECONDS = max(0.15, float(str(_get("SITE_ADD_AUTO_REFRESH_DELAY_SECONDS", "0.35") or "0.35").strip() or "0.35"))
SITE_ADD_MIN_COUNTRIES = max(1, int(str(_get("SITE_ADD_MIN_COUNTRIES", "1") or "1").strip() or "1"))
SITE_ADD_COUNTRIES_PER_PAGE = max(10, min(30, int(str(_get("SITE_ADD_COUNTRIES_PER_PAGE", "12") or "12"))))
SITE_ADD_CACHE_TTL_SECONDS = max(20.0, float(str(_get("SITE_ADD_CACHE_TTL_SECONDS", "180") or "180").strip() or "180"))
SITE_ADD_FAST_SOURCE_TIMEOUT_SECONDS = max(6.0, float(str(_get("SITE_ADD_FAST_SOURCE_TIMEOUT_SECONDS", "8") or "8").strip() or "8"))
SITE_ADD_SLOW_SOURCE_TIMEOUT_SECONDS = max(12.0, float(str(_get("SITE_ADD_SLOW_SOURCE_TIMEOUT_SECONDS", "18") or "18").strip() or "18"))
_site_add_jobs_lock = threading.RLock()
_site_add_jobs: set = set()
SITE_ADD_SOURCE_PAGE = f"{SITE_URL}/portal/live/my_sms"
SITE_ADD_SOURCE_LABEL = "my_sms"


def _merge_site_add_datasets(*datasets: Dict) -> Dict:
    combined_rows: List[Dict] = []
    country_rows: List[Dict] = []
    platforms: List[str] = []
    source_counts: Dict[str, int] = {}
    source_labels: List[str] = []
    page_urls: List[str] = []

    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue

        combined_rows.extend(list(dataset.get('rows', []) or []))

        raw_country_rows = dataset.get('country_rows')
        if isinstance(raw_country_rows, list) and raw_country_rows:
            country_rows.extend(raw_country_rows)
        else:
            country_rows.extend(list(dataset.get('rows', []) or []))

        for platform in list(dataset.get('platforms', []) or []):
            if platform and platform not in platforms:
                platforms.append(platform)

        counts = dataset.get('source_counts', {}) or {}
        if isinstance(counts, dict):
            for label, count in counts.items():
                try:
                    numeric_count = int(count or 0)
                except Exception:
                    numeric_count = 0
                source_counts[label] = max(source_counts.get(label, 0), numeric_count)

        raw_label = str(dataset.get('source_label') or '').strip()
        if raw_label:
            for part in [chunk.strip() for chunk in raw_label.split(' + ') if chunk.strip()]:
                if part not in source_labels:
                    source_labels.append(part)

        raw_urls = list(dataset.get('page_urls', []) or [])
        if not raw_urls:
            fallback_url = str(dataset.get('page_url') or '').strip()
            if fallback_url:
                raw_urls = [fallback_url]
        for url in raw_urls:
            clean_url = str(url or '').strip()
            if clean_url and clean_url not in page_urls:
                page_urls.append(clean_url)

    deduped_rows = _dedupe_numbers(combined_rows)
    display_country_rows = _dedupe_site_country_rows(country_rows or combined_rows)
    countries = _site_add_country_buckets(display_country_rows)
    grouped = {bucket.get('key', 'unknown'): list(bucket.get('rows', [])) for bucket in countries}

    return {
        'rows': deduped_rows,
        'country_rows': display_country_rows,
        'platforms': platforms or list(_platform_picker_platforms()),
        'countries': countries,
        'grouped': grouped,
        'counts': {bucket.get('key', 'unknown'): bucket.get('total', 0) for bucket in countries},
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_label': ' + '.join(source_labels) if source_labels else SITE_ADD_SOURCE_LABEL,
        'source_counts': source_counts,
        'page_url': ' | '.join(page_urls) if page_urls else SITE_ADD_SOURCE_PAGE,
        'page_urls': page_urls,
        'total_numbers': len(deduped_rows),
    }


def _notify_channel_about_new_numbers(new_items: List[Dict], source_label: str = "الموقع"):
    unique_items = _dedupe_numbers(new_items)
    if not unique_items:
        return
    summary: Dict[str, int] = {}
    preview_lines: List[str] = []
    for item in unique_items:
        platform_name = _display_platform_name(item.get("platform", "General"))
        summary[platform_name] = summary.get(platform_name, 0) + 1
        if len(preview_lines) < 8:
            masked = _mask_number(item.get("number", ""))
            added_at = str(item.get("added_at") or "").strip()
            preview_line = f"• `{masked}` | {platform_name}"
            if added_at:
                preview_line += f" | {added_at}"
            preview_lines.append(preview_line)

    lines = [
        f"📥 تم تحديث الأرقام من {source_label}",
        "",
        f"🆕 الأرقام الجديدة: {len(unique_items)}",
        "",
        "📊 توزيع المنصات:",
    ]
    for platform_name, count in sorted(summary.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"• {platform_name}: {count} رقم")
    if preview_lines:
        lines.extend(["", "🧾 معاينة metadata فقط:"])
        lines.extend(preview_lines)
    lines.extend(["", "🤖 رابط البوت موجود أسفل الرسالة للدخول السريع."])

    try:
        bot.send_message(
            CHANNEL_ID,
            "\n".join(lines),
            reply_markup=_build_channel_post_markup(),
        )
        log_event("CHANNEL_NEW_NUMBERS_POST", {"count": len(unique_items), "source": source_label})
    except Exception as channel_sync_err:
        logger.warning(f"تعذر إرسال تحديث الأرقام للقناة: {channel_sync_err}")


def _notify_bot_users_about_site_fetch(new_items: List[Dict], source_label: str = "جلب من الموقع"):
    unique_items = _dedupe_numbers(new_items)
    if not unique_items:
        return
    summary: Dict[str, int] = {}
    for item in unique_items:
        platform_name = _display_platform_name(item.get("platform", "General"))
        summary[platform_name] = summary.get(platform_name, 0) + 1

    lines = [
        "📢 تم إضافة أرقام جديدة داخل البوت!",
        "",
        f"🆕 عدد الأرقام الجديدة: {len(unique_items)}",
        f"🧭 المصدر: {source_label}",
        "",
        "تفاصيل الأقسام:",
    ]
    for platform_name, count in sorted(summary.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"• {platform_name}: {count} رقم")
    lines.append("\nافتح /start أو استخدم الأزرار لعرض الأقسام الجديدة.")
    payload = "\n".join(lines)

    sent = failed = 0
    for uid in list(dict.fromkeys(users_db.get("users", []))):
        try:
            bot.send_message(uid, payload)
            sent += 1
        except Exception:
            failed += 1
    log_event("SITE_FETCH_NOTIFY", {"count": len(unique_items), "sent": sent, "failed": failed, "source": source_label})


def _extract_phone_candidates_from_text(raw_text: str) -> List[str]:
    """استخراج مرن للأرقام من صفحات الموقع حتى بعد تغيّر الواجهة.

    نعتمد على:
    1) الحقول الصريحة داخل JSON / data-attrs / tel links
    2) صفوف الجداول والقوائم والكروت الظاهرة
    3) كتلة النص الظاهرة كطبقة أخيرة بحذر
    """
    found: List[str] = []
    seen = set()

    def _push(candidate: str) -> None:
        number = _normalize_number(candidate)
        digits = re.sub(r'\D', '', number)
        if not number or len(digits) < 8 or len(digits) > 15:
            return
        if number in seen:
            return
        seen.add(number)
        found.append(number)

    raw_html = str(raw_text or '')
    if not raw_html:
        return found

    explicit_patterns = [
        r"\"(?:number|Number|phone|mobile|msisdn|full_number|fullNumber|tel|did|cli|sender|line)\"\s*:\s*\"([^\"]+)\"",
        r"\'(?:number|Number|phone|mobile|msisdn|full_number|fullNumber|tel|did|cli|sender|line)\'\s*:\s*\'([^\']+)\'",
        r"(?:data-number|data-phone|data-msisdn|data-mobile|data-full-number|data-fullnumber|data-tel|data-cli|data-did)\s*=\s*[\"\']([^\"\']+)[\"\']",
        r"href\s*=\s*[\"\']tel:([^\"\']+)[\"\']",
        r"toggleNum\w*\(\s*[\"\']([^\"\']+)[\"\']",
        r"number\s*=\s*[\"\']([^\"\']+)[\"\']",
    ]

    for pattern in explicit_patterns:
        for match in re.findall(pattern, raw_html, flags=re.IGNORECASE):
            candidate = match if isinstance(match, str) else next((part for part in match if part), '')
            _push(candidate)

    scoped_phone_pattern = re.compile(r'(?<!\d)(?:\+|00)?\d(?:[\s().\-]*\d){7,14}(?!\d)')

    block_patterns = [
        r'<tr[^>]*>.*?</tr>',
        r'<li[^>]*>.*?</li>',
        r"<(?:div|article|section)\b[^>]*(?:class|id)\s*=\s*['\"][^'\"]*(?:row|item|card|number|phone|sms|line|entry)[^'\"]*['\"][^>]*>.*?</(?:div|article|section)>",
    ]
    row_blocks: List[str] = []
    for pattern in block_patterns:
        row_blocks.extend(re.findall(pattern, raw_html, flags=re.IGNORECASE | re.DOTALL))

    for block in row_blocks[:4000]:
        local_found_before = len(found)
        for pattern in explicit_patterns:
            for match in re.findall(pattern, block or '', flags=re.IGNORECASE):
                candidate = match if isinstance(match, str) else next((part for part in match if part), '')
                _push(candidate)
        if len(found) > local_found_before:
            continue

        text_value = _strip_html_text(block)
        if not text_value or len(text_value) > 600:
            continue
        for match in scoped_phone_pattern.finditer(text_value):
            _push(match.group(0))

    if len(found) < 3:
        visible_text = _strip_html_text(raw_html)
        if visible_text and len(visible_text) <= 250000:
            for match in scoped_phone_pattern.finditer(visible_text):
                _push(match.group(0))

    return found

def _extract_live_my_sms_rows_from_payload(payload: Any, source: str = 'live_my_sms_json') -> List[Dict]:
    rows: List[Dict] = []
    seen = set()
    candidate_keys = ('number', 'Number', 'phone', 'mobile', 'msisdn', 'full_number', 'tel', 'did', 'cli', 'sender', 'line')

    def _numbers_from_row(raw_row: Dict[str, Any]) -> List[str]:
        found_numbers: List[str] = []
        local_seen = set()

        def _push(candidate: str) -> None:
            normalized = _normalize_number(str(candidate))
            digits = re.sub(r'\D', '', normalized)
            if not normalized or len(digits) < 8 or len(digits) > 15:
                return
            if normalized in local_seen:
                return
            local_seen.add(normalized)
            found_numbers.append(normalized)

        for key in candidate_keys:
            value = raw_row.get(key)
            if value is None:
                continue
            _push(str(value))

        for value in raw_row.values():
            if isinstance(value, str):
                for candidate in _extract_phone_candidates_from_text(value):
                    _push(candidate)
        return found_numbers

    def _append_row(raw_row: Dict[str, Any]) -> None:
        for normalized in _numbers_from_row(raw_row):
            if normalized in seen:
                continue
            seen.add(normalized)
            item = {
                'number': normalized,
                'platform': GENERAL_PLATFORM_NAME,
                'site_section': SITE_ADD_SOURCE_LABEL,
                'source': source,
                'added_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'country_name': str(raw_row.get('country_name') or raw_row.get('country') or raw_row.get('country_label') or '').strip(),
                'country_name_ar': str(raw_row.get('country_name_ar') or raw_row.get('country_name') or raw_row.get('country') or raw_row.get('country_label') or '').strip(),
                'country': str(raw_row.get('country') or raw_row.get('country_name') or '').strip(),
                'country_flag': str(raw_row.get('country_flag') or '').strip(),
                'country_code': str(raw_row.get('country_code') or raw_row.get('countryCode') or '').strip(),
                'raw_platform': str(raw_row.get('platform') or raw_row.get('service') or raw_row.get('sender') or '').strip(),
            }
            item = _enrich_number_item(item)
            if item:
                rows.append(item)

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            _append_row(node)
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)

    _walk(payload)
    return rows


def _extract_live_my_sms_rows_from_html(page_html: str) -> List[Dict]:
    rows: List[Dict] = []
    for number in _extract_phone_candidates_from_text(page_html or ''):
        item = _enrich_number_item({
            'number': number,
            'platform': GENERAL_PLATFORM_NAME,
            'site_section': SITE_ADD_SOURCE_LABEL,
            'source': 'live_my_sms_html',
            'added_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        if item:
            rows.append(item)
    return rows


def _fetch_numbers_from_live_my_sms(session: Optional[requests.Session] = None) -> List[Dict]:
    session = session or _build_site_session()
    page_resp = session.get(SITE_ADD_SOURCE_PAGE, timeout=30, allow_redirects=True)
    if not _is_authenticated_response(page_resp):
        raise RuntimeError('تعذر فتح صفحة my_sms. تأكد من الكوكيز أو تسجيل الدخول.')

    collected: List[Dict] = []
    page_html = getattr(page_resp, 'text', '') or ''
    csrf = _extract_csrf_token(page_html)
    page_rows = _extract_live_my_sms_rows_from_html(page_html)

    ajax_candidates = [
        (f'{SITE_URL}/portal/live/my_sms/get', 'post'),
        (f'{SITE_URL}/portal/live/my_sms/get', 'get'),
        (f'{SITE_URL}/portal/live/my_sms/data', 'post'),
        (f'{SITE_URL}/portal/live/my_sms/data', 'get'),
        (f'{SITE_URL}/portal/live/my_sms/list', 'post'),
        (f'{SITE_URL}/portal/live/my_sms/list', 'get'),
        (f'{SITE_URL}/portal/live/my_sms/table', 'post'),
        (f'{SITE_URL}/portal/live/my_sms/table', 'get'),
    ]
    headers = {
        'Referer': SITE_ADD_SOURCE_PAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/plain, text/html, */*',
    }
    if csrf:
        headers['X-CSRF-TOKEN'] = csrf

    page_size = max(100, min(500, int(_get('SITE_ADD_PORTAL_PAGE_SIZE', '300') or '300')))
    payload_variants = []
    base_payload = {'_token': csrf} if csrf else {}
    payload_variants.append(base_payload)
    datatable_payload = {
        '_token': csrf,
        'draw': '1',
        'start': '0',
        'length': str(page_size),
    }
    payload_variants.append({k: v for k, v in datatable_payload.items() if v})

    for endpoint, method in ajax_candidates:
        for payload in payload_variants:
            try:
                if method == 'post':
                    resp = session.post(endpoint, data=payload, headers=headers, timeout=22, allow_redirects=True)
                else:
                    resp = session.get(endpoint, params=payload, headers=headers, timeout=22, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                content_type = (resp.headers.get('content-type', '') or '').lower()
                if 'json' in content_type:
                    try:
                        payload_json = resp.json()
                    except Exception:
                        payload_json = None
                    if payload_json is not None:
                        collected.extend(_extract_live_my_sms_rows_from_payload(payload_json, source='live_my_sms_ajax'))
                else:
                    collected.extend(_extract_live_my_sms_rows_from_html(getattr(resp, 'text', '') or ''))
            except Exception as ajax_err:
                logger.debug(f'live my_sms ajax probe failed for {endpoint} [{method}]: {ajax_err}')

    if page_rows:
        collected.extend(page_rows)

    if not collected:
        try:
            collected.extend(_fetch_numbers_from_portal(session))
        except Exception as portal_backup_err:
            logger.debug(f'live my_sms portal fallback failed: {portal_backup_err}')

    unique: List[Dict] = []
    seen_numbers = set()
    for row in collected:
        item = _enrich_number_item(row)
        number = item.get('number', '')
        if not number or number in seen_numbers:
            continue
        seen_numbers.add(number)
        unique.append(item)
    return unique

def _site_add_bucket_signature(row: Dict, country: Dict) -> Tuple[str, str, str, str, str]:
    return (
        str(country.get('key') or 'unknown').strip() or 'unknown',
        re.sub(r'\s+', ' ', str(row.get('country_name_ar') or row.get('country_name') or row.get('country') or row.get('country_label') or '').strip()).lower(),
        re.sub(r'\s+', ' ', str(row.get('site_section') or '').strip()).lower(),
        re.sub(r'\s+', ' ', str(row.get('source') or '').strip()).lower(),
        re.sub(r'\s+', ' ', str(row.get('raw_platform') or '').strip()).lower(),
    )


def _dedupe_site_country_rows(items: List[Dict]) -> List[Dict]:
    unique: List[Dict] = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = _enrich_number_item(item)
        if not row:
            continue
        signature = (
            row.get('number', ''),
            str(row.get('country_name_ar') or row.get('country_name') or row.get('country') or row.get('country_label') or '').strip().lower(),
            str(row.get('site_section') or '').strip().lower(),
            str(row.get('source') or '').strip().lower(),
            str(row.get('raw_platform') or '').strip().lower(),
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(row)
    return unique


def _site_add_country_buckets(rows: List[Dict]) -> List[Dict]:
    buckets: Dict[str, Dict] = {}
    per_country_limit = 100
    for item in rows or []:
        row = _enrich_number_item(item)
        number = _normalize_number(row.get('number', ''))
        if not number:
            continue
        country = _country_info_from_row(number, row)
        base_key = str(country.get('key') or 'unknown').strip() or 'unknown'
        bucket = buckets.setdefault(base_key, {
            'base_key': base_key,
            'name': country.get('name', 'غير محددة'),
            'flag': country.get('flag', '🌐'),
            'code': country.get('code', ''),
            'rows': [],
            'seen_numbers': set(),
            'sources': set(),
            'site_sections': set(),
            'raw_platforms': set(),
        })
        if number in bucket['seen_numbers']:
            continue
        bucket['seen_numbers'].add(number)
        source_value = str(row.get('source') or '').strip()
        section_value = str(row.get('site_section') or '').strip()
        raw_platform_value = str(row.get('raw_platform') or '').strip()
        if source_value:
            bucket['sources'].add(source_value)
        if section_value:
            bucket['site_sections'].add(section_value)
        if raw_platform_value:
            bucket['raw_platforms'].add(raw_platform_value)
        bucket['rows'].append(row)

    final_buckets: List[Dict] = []
    for bucket in buckets.values():
        source_hint_parts: List[str] = []
        for part in sorted(bucket.pop('site_sections', set())):
            if part and part not in source_hint_parts:
                source_hint_parts.append(part)
        for part in sorted(bucket.pop('raw_platforms', set())):
            if part and part not in source_hint_parts:
                source_hint_parts.append(part)
        for part in sorted(bucket.pop('sources', set())):
            if part and part not in source_hint_parts:
                source_hint_parts.append(part)
        source_hint = ' • '.join(source_hint_parts)

        all_rows = list(bucket.pop('rows', []))
        all_rows.sort(key=lambda row: str(row.get('number') or ''))
        duplicate_total = max(1, (len(all_rows) + per_country_limit - 1) // per_country_limit)
        for duplicate_index in range(duplicate_total):
            start = duplicate_index * per_country_limit
            end = start + per_country_limit
            chunk_rows = [dict(item) for item in all_rows[start:end]]
            if not chunk_rows:
                continue
            final_buckets.append({
                'base_key': bucket.get('base_key', 'unknown'),
                'key': f"{bucket.get('base_key', 'unknown')}::{duplicate_index + 1}",
                'name': bucket.get('name', 'غير محددة'),
                'display_name': bucket.get('name', 'غير محددة'),
                'flag': bucket.get('flag', '🌐'),
                'code': bucket.get('code', ''),
                'total': len(chunk_rows),
                'raw_total': len(chunk_rows),
                'rows': chunk_rows,
                'duplicate_index': duplicate_index + 1,
                'duplicate_total': duplicate_total,
                'is_duplicate': duplicate_total > 1,
                'source_hint': source_hint,
            })

    final_buckets.sort(key=lambda bucket: (bucket.get('name', ''), int(bucket.get('duplicate_index', 1) or 1), bucket.get('key', '')))
    return final_buckets



def _build_site_platform_number_dataset(refresh: bool = False) -> Dict:
    now_ts = time.time()
    cached = _site_add_cache.get('data') or {}
    cache_ts = float(_site_add_cache.get('timestamp') or 0.0)
    if not refresh and cached and (now_ts - cache_ts) < SITE_ADD_CACHE_TTL_SECONDS:
        return cached

    previous_nonempty = cached if (cached.get('countries') or cached.get('rows')) else {}
    attempts = SITE_ADD_AUTO_REFRESH_ATTEMPTS if refresh or not previous_nonempty else 1
    best_dataset: Dict[str, Any] = previous_nonempty or {}

    def _run_source_jobs(jobs: List[Tuple[str, str, Any]], timeout_seconds: float) -> Tuple[List[Dict], Dict[str, int], List[str], List[str]]:
        rows_accum: List[Dict] = []
        counts: Dict[str, int] = {}
        labels: List[str] = []
        urls: List[str] = []
        if not jobs:
            return rows_accum, counts, labels, urls

        max_workers = max(1, min(4, len(jobs)))
        executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='siteadd')
        future_map = {executor.submit(loader): (label, url) for label, url, loader in jobs}
        pending = set(future_map.keys())
        deadline = time.time() + max(1.0, float(timeout_seconds))

        try:
            while pending and time.time() < deadline:
                remaining = max(0.05, deadline - time.time())
                done, pending = wait(
                    pending,
                    timeout=min(0.5, remaining),
                    return_when=FIRST_COMPLETED,
                )
                if not done:
                    continue

                for future in done:
                    label, url = future_map[future]
                    try:
                        rows = future.result() or []
                    except Exception as source_err:
                        logger.warning(f'site add source failed [{label}]: {source_err}')
                        rows = []
                    if rows:
                        rows_accum.extend(rows)
                        counts[label] = len(rows)
                        labels.append(label)
                        urls.append(url)
                        logger.info(f'site add source {label}: {len(rows)} رقم')
                    else:
                        logger.info(f'site add source {label}: 0 رقم')

            if pending:
                logger.warning(f'site add source timeout after {timeout_seconds}s')
                for future in list(pending):
                    label, _url = future_map[future]
                    future.cancel()
                    logger.warning(f'site add source cancelled بسبب البطء: {label}')
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return rows_accum, counts, labels, urls

    for attempt_index in range(attempts):
        quick_jobs = [
            ('my_sms', SITE_ADD_SOURCE_PAGE, lambda: _fetch_numbers_from_live_my_sms(_build_site_session())),
            ('portal_numbers', f'{SITE_URL}/portal/numbers', lambda: _fetch_numbers_from_portal(_build_site_session())),
            ('homepage_scrape', f'{SITE_URL}/portal', _fetch_numbers_from_homepage_scrape),
        ]
        all_rows, source_counts, successful_sources, page_urls = _run_source_jobs(quick_jobs, SITE_ADD_FAST_SOURCE_TIMEOUT_SECONDS)

        deduped_quick_rows = _dedupe_numbers(all_rows)
        fresh_dataset = _merge_site_add_datasets({
            'rows': deduped_quick_rows,
            'country_rows': list(all_rows),
            'platforms': list(_platform_picker_platforms()),
            'countries': [],
            'grouped': {},
            'counts': {},
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_label': ' + '.join(successful_sources) if successful_sources else SITE_ADD_SOURCE_LABEL,
            'source_counts': source_counts,
            'page_url': ' | '.join(page_urls) if page_urls else SITE_ADD_SOURCE_PAGE,
            'page_urls': page_urls,
            'total_numbers': len(deduped_quick_rows),
            'attempt': attempt_index + 1,
            'attempts': attempts,
        })

        merged_dataset = fresh_dataset
        merged_dataset['attempt'] = attempt_index + 1
        merged_dataset['attempts'] = attempts
        best_dataset = merged_dataset if merged_dataset.get('countries') or merged_dataset.get('rows') else fresh_dataset

        countries_count = len(merged_dataset.get('countries') or [])
        should_try_slow_source = countries_count < SITE_ADD_MIN_COUNTRIES and (refresh or not deduped_quick_rows or countries_count <= 1)
        if should_try_slow_source:
            slow_rows, slow_counts, slow_labels, slow_urls = _run_source_jobs([
                ('sms_ranges', f'{SITE_URL}/portal/sms/received', lambda: _fetch_numbers_from_sms_ranges(_build_site_session())),
            ], SITE_ADD_SLOW_SOURCE_TIMEOUT_SECONDS)
            if slow_rows:
                deduped_slow_rows = _dedupe_numbers(slow_rows)
                slow_dataset = _merge_site_add_datasets({
                    'rows': deduped_slow_rows,
                    'country_rows': list(slow_rows),
                    'platforms': list(_platform_picker_platforms()),
                    'countries': [],
                    'grouped': {},
                    'counts': {},
                    'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source_label': ' + '.join(slow_labels) if slow_labels else SITE_ADD_SOURCE_LABEL,
                    'source_counts': slow_counts,
                    'page_url': ' | '.join(slow_urls) if slow_urls else f'{SITE_URL}/portal/sms/received',
                    'page_urls': slow_urls,
                    'total_numbers': len(deduped_slow_rows),
                })
                merged_dataset = _merge_site_add_datasets(merged_dataset, slow_dataset)
                merged_dataset['attempt'] = attempt_index + 1
                merged_dataset['attempts'] = attempts
                best_dataset = merged_dataset
                countries_count = len(merged_dataset.get('countries') or [])

        if countries_count >= SITE_ADD_MIN_COUNTRIES or merged_dataset.get('total_numbers') or (countries_count > 0 and attempt_index >= attempts - 1):
            _site_add_cache['data'] = merged_dataset
            _site_add_cache['timestamp'] = time.time()
            return merged_dataset

        if attempt_index < (attempts - 1) and SITE_ADD_AUTO_REFRESH_DELAY_SECONDS > 0:
            time.sleep(SITE_ADD_AUTO_REFRESH_DELAY_SECONDS)

    if previous_nonempty:
        fallback_dataset = _merge_site_add_datasets(previous_nonempty, best_dataset)
        fallback_dataset['used_cached_fallback'] = True
        fallback_dataset['attempt'] = attempts
        fallback_dataset['attempts'] = attempts
        _site_add_cache['data'] = fallback_dataset
        _site_add_cache['timestamp'] = time.time()
        return fallback_dataset

    _site_add_cache['data'] = best_dataset
    _site_add_cache['timestamp'] = time.time()
    return best_dataset

def _site_add_total_pages(countries: List[Dict]) -> int:
    total = len(countries or [])
    return max(1, (total + SITE_ADD_COUNTRIES_PER_PAGE - 1) // SITE_ADD_COUNTRIES_PER_PAGE)


def _site_add_selected_country_rows(state: Optional[Dict]) -> List[Dict]:
    payload = state if isinstance(state, dict) else {}
    selected_country_key = str(payload.get('selected_country_key') or '').strip()
    if not selected_country_key:
        return []

    cached_rows = payload.get('selected_country_rows', [])
    if isinstance(cached_rows, list) and cached_rows:
        return [dict(item) for item in cached_rows if isinstance(item, dict)]

    grouped = payload.get('grouped', {})
    if not isinstance(grouped, dict):
        return []
    rows = [dict(item) for item in list(grouped.get(selected_country_key, []) or []) if isinstance(item, dict)]
    if rows:
        payload['selected_country_rows'] = [dict(item) for item in rows]
    return rows


def _site_add_state_from_dataset(user_id: int, data: Dict, previous_state: Optional[Dict] = None) -> Dict:
    previous = dict(previous_state or site_add_state.get(user_id, {}) or {})
    countries = list(data.get('countries', []) or [])
    grouped = dict(data.get('grouped', {}))
    source_label = str(data.get('source_label', SITE_ADD_SOURCE_LABEL) or SITE_ADD_SOURCE_LABEL)
    page_url = str(data.get('page_url', SITE_ADD_SOURCE_PAGE) or SITE_ADD_SOURCE_PAGE)

    previous_page = int(previous.get('countries_page', 0) or 0)
    total_pages = _site_add_total_pages(countries)
    if previous_page >= total_pages:
        previous_page = total_pages - 1
    if previous_page < 0:
        previous_page = 0

    selected_country_key = str(previous.get('selected_country_key') or '').strip()
    if selected_country_key not in grouped:
        selected_country_key = ''
    selected_platform = str(previous.get('selected_platform') or '').strip() if selected_country_key else ''

    state = {
        'countries': countries,
        'grouped': grouped,
        'selected_country_key': selected_country_key,
        'selected_country_rows': [dict(item) for item in list(grouped.get(selected_country_key, []) or []) if isinstance(item, dict)] if selected_country_key else [],
        'selected_country_total': len(grouped.get(selected_country_key, []) or []) if selected_country_key else 0,
        'selected_platform': selected_platform,
        'created_at': data.get('created_at', ''),
        'page_url': page_url,
        'source_label': source_label,
        'countries_page': previous_page,
        'total_numbers': data.get('total_numbers', 0),
        'used_cached_fallback': bool(data.get('used_cached_fallback')),
    }
    site_add_state[user_id] = state
    return state


def _site_add_try_render_cached(chat_id: int, user_id: int, message_id: Optional[int] = None) -> bool:
    current_state = site_add_state.get(user_id, {})
    if list(current_state.get('countries', []) or []):
        _render_site_add_platforms(chat_id, user_id, message_id=message_id)
        return True

    cached = _site_add_cache.get('data') or {}
    cached_countries = list(cached.get('countries', []) or [])
    if not cached_countries:
        return False

    _site_add_state_from_dataset(user_id, cached, previous_state=current_state)
    _render_site_add_platforms(chat_id, user_id, message_id=message_id)
    return True


def _site_add_current_page(user_id: int) -> int:
    state = site_add_state.get(user_id, {})
    countries = list(state.get('countries', []) or [])
    total_pages = _site_add_total_pages(countries)
    page = int(state.get('countries_page', 0) or 0)
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1
    state['countries_page'] = page
    site_add_state[user_id] = state
    return page


def _build_site_add_platform_markup(user_id: int) -> types.InlineKeyboardMarkup:
    state = site_add_state.get(user_id, {})
    countries = list(state.get('countries', []) or [])
    current_page = _site_add_current_page(user_id)
    total_pages = _site_add_total_pages(countries)
    start = current_page * SITE_ADD_COUNTRIES_PER_PAGE
    end = start + SITE_ADD_COUNTRIES_PER_PAGE

    mk = types.InlineKeyboardMarkup(row_width=1)
    for bucket in countries[start:end]:
        country_title = bucket.get('display_name') or bucket.get('name', 'غير محددة')
        label = f"{bucket.get('flag', '🌐')} {country_title} ({bucket.get('total', 0)})"
        mk.add(types.InlineKeyboardButton(label[:60], callback_data=f"siteaddcty_{bucket.get('key', 'unknown')}"))

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(types.InlineKeyboardButton('⬅️ السابق', callback_data=f'siteaddpage_{current_page - 1}'))
    if total_pages > 1:
        nav_buttons.append(types.InlineKeyboardButton(f'📄 {current_page + 1}/{total_pages}', callback_data=f'siteaddpage_{current_page}'))
    if current_page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton('التالي ➡️', callback_data=f'siteaddpage_{current_page + 1}'))
    if nav_buttons:
        mk.row(*nav_buttons)

    mk.add(types.InlineKeyboardButton('🔄 تحديث كل مصادر الموقع', callback_data='siteadd_refresh'))
    return mk


def _build_site_add_number_markup(user_id: int) -> types.InlineKeyboardMarkup:
    state = site_add_state.get(user_id, {})
    selected_country_key = str(state.get('selected_country_key') or '').strip()
    selected_country_rows = _site_add_selected_country_rows(state)
    selected_country_total = len(selected_country_rows)
    if not selected_country_total:
        selected_country_total = int(state.get('selected_country_total', 0) or 0)
    mk = types.InlineKeyboardMarkup(row_width=2)
    if not selected_country_key or not selected_country_total:
        return _build_site_add_platform_markup(user_id)

    platforms = list(_platform_picker_platforms())
    for idx, platform in enumerate(platforms):
        label = f"{_platform_button_label(platform, include_count=False)} ← {selected_country_total}"
        mk.add(types.InlineKeyboardButton(label[:60], callback_data=f"siteaddplt_{idx}"))
    mk.add(types.InlineKeyboardButton('⬅️ رجوع للدول', callback_data='siteadd_back_countries'))
    mk.add(types.InlineKeyboardButton('🔄 تحديث كل مصادر الموقع', callback_data='siteadd_refresh'))
    return mk


def _site_add_platforms_text(user_id: int) -> str:
    state = site_add_state.get(user_id, {})
    countries = list(state.get('countries', []) or [])
    current_page = _site_add_current_page(user_id)
    total_pages = _site_add_total_pages(countries)
    source_label = str(state.get('source_label', SITE_ADD_SOURCE_LABEL) or SITE_ADD_SOURCE_LABEL)
    page_url = str(state.get('page_url', SITE_ADD_SOURCE_PAGE) or SITE_ADD_SOURCE_PAGE)
    lines = [
        '➕ إضافة أرقام من الموقع',
        '',
        f"🔎 المصادر المدمجة: {source_label}",
        f"🌐 الصفحات: {page_url}",
        f"🌍 جميع الدول المكتشفة: {len(countries)}",
        f"📱 إجمالي الأرقام المكتشفة: {state.get('total_numbers', 0)}",
        f"📄 صفحة الدول الحالية: {current_page + 1}/{total_pages}",
        f"🕐 آخر تحديث: {state.get('created_at', '')}",
        '♻️ تم استخدام آخر نتائج محفوظة مؤقتاً' if state.get('used_cached_fallback') else '✅ البيانات مباشرة من الموقع الآن',
        '',
        'اختَر الدولة من الأزرار تحت.',
        'لو عدد الدول كبير استخدم أزرار السابق/التالي، وبعد اختيار الدولة البوت هيضيف كل أرقامها للمنصة المختارة تلقائياً.',
    ]
    return '\n'.join(lines)


def _render_site_add_platforms(chat_id: int, user_id: int, message_id: Optional[int] = None):
    state = site_add_state.get(user_id, {})
    countries = list(state.get('countries', []) or [])
    if not countries:
        text = (
            '⚠️ ماقدرتش أستخرج أرقام من صفحات الموقع حالياً حتى بعد التحديث التلقائي عدة مرات. '
            'جرّب تحديث الكوكيز أو افتح الصفحات يدوياً وتأكد إن الأرقام ظاهرة فعلاً.'
        )
        return _send_or_edit(chat_id, text, message_id=message_id)
    return _send_or_edit(
        chat_id,
        _site_add_platforms_text(user_id),
        reply_markup=_build_site_add_platform_markup(user_id),
        message_id=message_id,
    )


def _launch_site_add_open_async(chat_id: int, user_id: int, refresh: bool = False, message_id: Optional[int] = None):
    cache_age_seconds = max(0.0, time.time() - float(_site_add_cache.get('timestamp') or 0.0))
    rendered_immediately = False if refresh else _site_add_try_render_cached(chat_id, user_id, message_id=message_id)
    needs_background_refresh = refresh or (not rendered_immediately) or (cache_age_seconds >= min(2.0, SITE_ADD_CACHE_TTL_SECONDS))

    if not needs_background_refresh:
        return

    with _site_add_jobs_lock:
        if user_id in _site_add_jobs:
            if not rendered_immediately:
                return _send_or_edit(
                    chat_id,
                    '⏳ يوجد تحديث شغال بالفعل، استنى ثواني وهيتم عرض الدول تلقائياً.',
                    message_id=message_id,
                )
            return
        _site_add_jobs.add(user_id)

    if not rendered_immediately:
        loading_text = (
            '⏳ جاري فحص الموقع وتجميع الدول والمنصات في الخلفية...\n\n'
            f'🚀 البوت مضبوط يعرض الدول بسرعة خلال ثوانٍ قليلة، والصفحة بتعرض حتى {SITE_ADD_COUNTRIES_PER_PAGE} دولة في المرة الواحدة.\n'
            '🛡️ ولو مصدر من الموقع بطّأ، هيتم إظهار آخر نتائج جاهزة فوراً بدون تعليق.'
        )
        _send_or_edit(chat_id, loading_text, message_id=message_id)

    def _worker():
        try:
            _open_site_add_platforms(chat_id, user_id, refresh=refresh, message_id=message_id)
        except Exception as site_add_err:
            logger.exception(f'Site add async open error: {site_add_err}')
            try:
                bot.send_message(chat_id, f'❌ تعذر فتح إضافة أرقام الموقع: {site_add_err}')
            except Exception:
                pass
        finally:
            with _site_add_jobs_lock:
                _site_add_jobs.discard(user_id)

    threading.Thread(target=_worker, daemon=True).start()


def _legacy_open_site_add_platforms_duplicate(chat_id: int, user_id: int, refresh: bool = False, message_id: Optional[int] = None):
    data = _build_site_platform_number_dataset(refresh=refresh)
    countries = data.get('countries', [])
    source_label = str(data.get('source_label', SITE_ADD_SOURCE_LABEL) or SITE_ADD_SOURCE_LABEL)
    page_url = str(data.get('page_url', SITE_ADD_SOURCE_PAGE) or SITE_ADD_SOURCE_PAGE)
    if not countries:
        text = (
            '⚠️ ماقدرتش أستخرج أرقام من صفحات الموقع حالياً حتى بعد التحديث التلقائي عدة مرات. '
            'جرّب تحديث الكوكيز أو افتح الصفحات يدوياً وتأكد إن الأرقام ظاهرة فعلاً.'
        )
        return _send_or_edit(chat_id, text, message_id=message_id)

    previous_page = int(site_add_state.get(user_id, {}).get('countries_page', 0) or 0)
    total_pages = _site_add_total_pages(countries)
    if previous_page >= total_pages:
        previous_page = total_pages - 1
    if previous_page < 0:
        previous_page = 0

    site_add_state[user_id] = {
        'countries': countries,
        'grouped': dict(data.get('grouped', {})),
        'selected_country_key': '',
        'selected_country_rows': [],
        'selected_platform': '',
        'created_at': data.get('created_at', ''),
        'page_url': page_url,
        'source_label': source_label,
        'countries_page': previous_page,
        'total_numbers': data.get('total_numbers', 0),
        'used_cached_fallback': bool(data.get('used_cached_fallback')),
    }
    return _render_site_add_platforms(chat_id, user_id, message_id=message_id)


def _open_site_add_platforms(chat_id: int, user_id: int, refresh: bool = False, message_id: Optional[int] = None):
    previous_state = dict(site_add_state.get(user_id, {}) or {})
    data = _build_site_platform_number_dataset(refresh=refresh)
    countries = data.get('countries', [])
    if not countries:
        cached = _site_add_cache.get('data') or {}
        cached_countries = list(cached.get('countries', []) or [])
        if cached_countries:
            data = cached
            countries = cached_countries
        else:
            text = (
                '⚠️ ماقدرتش أستخرج أرقام من صفحات الموقع حالياً حتى بعد التحديث التلقائي عدة مرات. '
                'جرّب تحديث الكوكيز أو افتح الصفحات يدوياً وتأكد إن الأرقام ظاهرة فعلاً.'
            )
            return _send_or_edit(chat_id, text, message_id=message_id)

    _site_add_state_from_dataset(user_id, data, previous_state=previous_state)
    return _render_site_add_platforms(chat_id, user_id, message_id=message_id)


def siteadd_country_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    bot.answer_callback_query(call.id, '⏳ جاري فتح الدولة...')
    state = site_add_state.get(call.from_user.id, {})
    grouped = state.get('grouped', {})
    country_key = call.data.replace('siteaddcty_', '', 1).strip() or 'unknown'
    rows = [dict(item) for item in list(grouped.get(country_key, []) or []) if isinstance(item, dict)]
    countries = list(state.get('countries', []) or [])
    bucket = next((item for item in countries if item.get('key') == country_key), None)
    if not rows or not bucket:
        _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)
        return

    state['selected_country_key'] = country_key
    state['selected_country_rows'] = [dict(item) for item in rows]
    state['selected_country_total'] = len(rows)
    state['selected_platform'] = ''
    site_add_state[call.from_user.id] = state

    preview_lines = [
        '➕ إضافة أرقام من الموقع',
        '',
        f"🌍 الدولة: {bucket.get('flag', '🌐')} {bucket.get('display_name') or bucket.get('name', 'غير محددة')}",
        f"☎️ مفتاح الدولة: {bucket.get('code', 'غير محدد') or 'غير محدد'}",
        f"📱 عدد الأرقام الجاهزة للإضافة: {len(rows)}",
        f"📌 المصدر: {bucket.get('source_hint') or 'نفس أرقام الموقع المسجلة حالياً'}",
        '',
        'اختَر المنصة اللي تحب تضيف عليها أرقام الدولة:',
    ]
    for index, row in enumerate(rows[:10], 1):
        preview_lines.append(f"{index}. {row.get('number', '')}")
    if len(rows) > 10:
        preview_lines.append(f"… وباقي {len(rows) - 10} رقم")

    _send_or_edit(
        call.message.chat.id,
        '\n'.join(preview_lines),
        reply_markup=_build_site_add_number_markup(call.from_user.id),
        message_id=call.message.message_id,
    )


def siteadd_back_countries_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    state = site_add_state.get(call.from_user.id, {})
    state['selected_country_key'] = ''
    state['selected_country_rows'] = []
    state['selected_country_total'] = 0
    state['selected_platform'] = ''
    site_add_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, 'تم الرجوع لقائمة الدول')
    _render_site_add_platforms(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def siteadd_page_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    state = site_add_state.get(call.from_user.id, {})
    countries = list(state.get('countries', []) or [])
    if not countries:
        bot.answer_callback_query(call.id, 'سيتم إعادة تحميل الدول')
        _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)
        return
    try:
        target_page = int(call.data.replace('siteaddpage_', '', 1))
    except Exception:
        target_page = 0
    total_pages = _site_add_total_pages(countries)
    if target_page < 0:
        target_page = 0
    if target_page >= total_pages:
        target_page = total_pages - 1
    state['countries_page'] = target_page
    site_add_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, f'صفحة {target_page + 1}/{total_pages}')
    _render_site_add_platforms(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


def _legacy_siteadd_platform_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    state = site_add_state.get(call.from_user.id, {})
    selected_country_key = str(state.get('selected_country_key') or '').strip()
    rows = list(state.get('selected_country_rows') or [])
    if not selected_country_key or not rows:
        bot.answer_callback_query(call.id, 'اختر الدولة أولاً', show_alert=True)
        _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)
        return

    platforms = list(_platform_picker_platforms())
    try:
        idx = int(call.data.replace('siteaddplt_', '', 1))
        selected_platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, 'المنصة غير موجودة', show_alert=True)
        return

    state['selected_platform'] = selected_platform
    site_add_state[call.from_user.id] = state

    prepared = []
    now_label = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    selected_numbers = set()
    for row in rows:
        item = dict(row)
        number = _normalize_number(item.get('number', ''))
        if number:
            selected_numbers.add(number)
        item['selected_platform'] = selected_platform
        item['platform'] = selected_platform
        item['site_section'] = SITE_ADD_SOURCE_LABEL
        item['source'] = str(item.get('source') or 'site_picker').strip() or 'site_picker'
        item['added_at'] = now_label
        prepared.append(item)

    before = list(numbers_db.get('numbers', []))
    merged = _append_numbers(prepared)
    added_items = _find_newly_added_numbers(before, merged)
    added_for_target = [
        item for item in added_items
        if _normalize_platform(item.get('platform', '')) == _normalize_platform(selected_platform)
        and _normalize_number(item.get('number', '')) in selected_numbers
    ]
    duplicated_count = max(0, len(prepared) - len(added_for_target))
    if added_for_target:
        _notify_users_about_new_numbers(added_for_target, source='site')
    country_info = _country_info_from_row(rows[0].get('number', ''), rows[0]) if rows else {'name': 'غير محددة', 'flag': '🌐', 'code': ''}
    bucket = next((item for item in state.get('countries', []) if item.get('key') == selected_country_key), None) or {}
    country_title = bucket.get('display_name') or country_info.get('name', 'غير محددة')

    bot.answer_callback_query(call.id, '✅ تم تسجيل الأرقام')
    text_lines = [
        '✅ تم تسجيل أرقام الدولة داخل المنصة بنجاح',
        '',
        f"🌍 الدولة: {country_info.get('flag', '🌐')} {country_title}",
        f"📂 المنصة: {_display_platform_name(selected_platform)}",
        f"🆕 الأرقام المضافة الآن: {len(added_for_target)}",
        f"♻️ الأرقام الموجودة مسبقاً: {duplicated_count}",
        f"📦 إجمالي الأرقام التي تمت معالجتها: {len(prepared)}",
        '',
        'لو حابب تضيف نفس الدولة على منصة تانية تقدر تختار منصة تانية من نفس الأزرار.',
    ]
    _send_or_edit(
        call.message.chat.id,
        '\n'.join(text_lines),
        reply_markup=_build_site_add_number_markup(call.from_user.id),
        message_id=call.message.message_id,
    )


def _legacy_siteadd_back_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)


def _legacy_siteadd_refresh_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    bot.answer_callback_query(call.id, 'جاري تحديث الصفحة تلقائياً وتجميع الدول...')
    _open_site_add_platforms(call.message.chat.id, call.from_user.id, refresh=True, message_id=call.message.message_id)


def _legacy_siteadd_number_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    bot.answer_callback_query(call.id, 'اختر الدولة ثم المنصة — البوت هيضيف كل الأرقام مرة واحدة', show_alert=True)

TEST_NUMBERS_SECTION_LABEL = _get("TEST_NUMBERS_SECTION_LABEL", "Test Numbers")

TEST_MODE_ENABLED = _env_flag("TEST_MODE_ENABLED", True)

TEST_MODE_INTERVAL_SECONDS = max(180, int(_get("TEST_MODE_INTERVAL_SECONDS", "180") or "180"))

_TEST_MODE_SERVICES = list(dict.fromkeys([
    "WhatsApp", "Telegram", "Facebook", "TikTok", "Instagram", "Google", "Discord", "Binance"
] + list(ALLOWED_PLATFORMS)))

_test_mode_started = False

_test_mode_lock = threading.Lock()

def _mask_test_mode_number(number: str) -> str:
    masked = _mask_number(number)
    return masked or str(number or "")


def _flag_to_region_tag(flag: str) -> str:
    """يحوّل إيموجي العلم إلى كود الدولة مثل #SA أو #EG."""
    try:
        code = ''.join(
            chr(ord(c) - 0x1F1E6 + ord('A'))
            for c in (flag or '')
            if '\U0001F1E6' <= c <= '\U0001F1FF'
        )
        return f"#{code}" if len(code) == 2 else "#TEST"
    except Exception:
        return "#TEST"

def _fetch_numbers_from_test_numbers(session=None) -> List[Dict]:
    """Fallback آمن لاستخراج أرقام قسم Test Numbers من live test system."""
    rows: List[Dict] = []
    for item in fetch_live_test_codes() or []:
        number = _normalize_number(item.get("number", ""))
        if not number:
            continue
        platform = _normalize_platform(item.get("service") or item.get("platform") or TEST_NUMBERS_SECTION_LABEL) or TEST_NUMBERS_SECTION_LABEL
        rows.append({
            "number": number,
            "platform": platform,
            "source": "test_numbers",
            "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "country": item.get("country", ""),
            "message": item.get("message", ""),
        })
    return rows

def _country_rows_for_test_mode() -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    seen = set()
    for code, name, flag in COUNTRY_PHONE_MAP:
        digits = re.sub(r"\D", "", str(code or ""))
        key = (digits, str(name or '').strip())
        if not digits or key in seen:
            continue
        seen.add(key)
        candidates.append({"code": code, "digits": digits, "name": name, "flag": flag})
    return candidates or [{"code": "+20", "digits": "20", "name": "مصر", "flag": "🇪🇬"}]


def _random_test_country() -> Dict[str, str]:
    candidates = _country_rows_for_test_mode()
    return random.choice(candidates) if candidates else {"code": "+20", "digits": "20", "name": "مصر", "flag": "🇪🇬"}


def _generate_test_mode_item_for_country(country: Dict[str, str], service: str = "", seed_index: int = 0) -> Dict:
    services = list(_TEST_MODE_SERVICES) or ["General"]
    chosen_service = str(service or services[seed_index % len(services)]).strip() or "General"
    local_len = random.randint(6, 9)
    local_digits = ''.join(str(random.randint(0, 9)) for _ in range(local_len))
    raw_number = f"+{country.get('digits', '58')}{local_digits}"
    # كود عشوائي 6 أرقام بأسلوب OTP حقيقي
    code = str(random.randint(100000, 999999))
    country_flag = country.get("flag", "🌐")
    region_tag = _flag_to_region_tag(country_flag)
    country_code_prefix = str(country.get('code', '+1') or '+1').lstrip('+')
    visual_number_id = f"{country_code_prefix}{random.randint(10000, 99999)}"
    now_label = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "number": raw_number,
        "masked_number": _mask_test_mode_number(raw_number),
        "code": code,
        "platform": chosen_service,
        "country_name": country.get("name", "غير محددة"),
        "country_flag": country_flag,
        "country_code": country.get("code", ""),
        "visual_number_id": visual_number_id,
        "visual_region_flag": country_flag,          # علم الدولة الحقيقي
        "visual_region_tag": region_tag,             # كود الدولة مثل #SA #EG
        "sender_name": TEST_SENDER_NAME,
        "badge": TEST_MODE_LABEL,
        "message": f"TEST/FAKE | رسالة وهمية لمنصة {chosen_service} داخل قناة الاختبار فقط.",
        "timestamp": now_label,
        "source": "test_mode",
    }


def _generate_test_mode_item() -> Dict:
    countries = _country_rows_for_test_mode()
    country = random.choice(countries) if countries else {"code": "+20", "digits": "20", "name": "مصر", "flag": "🇪🇬"}
    service = random.choice(_TEST_MODE_SERVICES) if _TEST_MODE_SERVICES else "General"
    return _generate_test_mode_item_for_country(country, service=service)


def _build_test_mode_message_text(item: Dict) -> str:
    country_flag = html.escape(str(item.get('country_flag', '') or '🌐'))
    country_name = html.escape(str(item.get('country_name', '') or 'غير محددة'))
    platform_text = html.escape(str(item.get('platform', '') or 'General'))
    code_text = html.escape(str(item.get('code', '') or '000000'))
    return (
        "رساله اختبار\n\n"
        f"الدوله: {country_flag} {country_name}\n"
        f"المنصه: {platform_text}\n"
        f"الكود : <code>{code_text}</code>"
    )


def _build_test_mode_broadcast_messages(max_length: int = 3500) -> List[str]:
    countries = _country_rows_for_test_mode()
    services = list(_TEST_MODE_SERVICES) or ["General"]
    messages: List[str] = []
    for idx, country in enumerate(countries):
        item = _generate_test_mode_item_for_country(country, service=services[idx % len(services)], seed_index=idx)
        messages.append(_build_test_mode_message_text(item))
    return messages or [_build_test_mode_message_text(_generate_test_mode_item())]


def _publish_test_mode_item_to_channel(item: Dict) -> None:
    bot.send_message(
        TEST_CHANNEL_ID,
        _build_test_mode_message_text(item),
        parse_mode="HTML",
        reply_markup=_build_test_channel_post_markup(),
    )

def _test_mode_loop() -> None:
    """
    يمر على كل الدول (عشوائياً) وينشر رسالة مستقلة لكل دولة مع
    انتظار TEST_MODE_INTERVAL_SECONDS (180 ث = 3 دقائق) بين كل رسالة.
    بعد الانتهاء من كل الدول يُعيد الكرّة من الأول.
    """
    while True:
        countries = _country_rows_for_test_mode()
        random.shuffle(countries)   # ترتيب عشوائي في كل جولة
        logger.info(f"🧪 [TEST-MODE] بدء جولة جديدة | {len(countries)} دولة | كل {TEST_MODE_INTERVAL_SECONDS}ث")
        for idx, country in enumerate(countries):
            try:
                service = random.choice(_TEST_MODE_SERVICES) if _TEST_MODE_SERVICES else "General"
                item = _generate_test_mode_item_for_country(country, service=service, seed_index=idx)
                _publish_test_mode_item_to_channel(item)
                logger.info(
                    f"🧪 [{idx + 1}/{len(countries)}] "
                    f"{item.get('country_flag', '')} {item.get('country_name', '')} | "
                    f"{item.get('platform', '')} | "
                    f"رقم: {item.get('masked_number', '')} | "
                    f"كود: {item.get('code', '')}"
                )
            except Exception as test_mode_err:
                logger.warning(f"Test Mode publish error [{country.get('name', '')}]: {test_mode_err}")
            time.sleep(TEST_MODE_INTERVAL_SECONDS)

def _start_test_mode_publisher_once() -> None:
    global _test_mode_started
    if not TEST_MODE_ENABLED:
        logger.info("⏸️ Test Mode معطّل عبر الإعدادات.")
        return
    if not TEST_CHANNEL_ID:
        logger.info("⏸️ Test Mode متوقف لأن TEST_CHANNEL_ID غير مضبوط لقناة الاختبار الخاصة.")
        return
    with _test_mode_lock:
        if _test_mode_started:
            return
        _test_mode_started = True
    threading.Thread(target=_test_mode_loop, daemon=True).start()
    logger.info(f"✅ تم تشغيل Test Mode لقناة الاختبار الخاصة كل {TEST_MODE_INTERVAL_SECONDS} ثانية")

def _site_row_platform_candidates(item: Dict, fallback: str = "") -> List[str]:
    row = dict(item or {})
    candidates = [
        row.get("platform", ""),
        row.get("service", ""),
        row.get("site_section", ""),
        row.get("range", ""),
        row.get("section", ""),
        row.get("category", ""),
        row.get("group", ""),
        row.get("A2P", ""),
        row.get("message", ""),
        row.get("title", ""),
        fallback,
    ]
    merged_bits = []
    for value in candidates:
        if isinstance(value, (dict, list, tuple, set)):
            continue
        text_value = re.sub(r"\s+", " ", str(value or "").strip())
        if text_value:
            merged_bits.append(text_value)
    if merged_bits:
        candidates.append(" | ".join(merged_bits))
    return [str(value) for value in candidates if str(value or "").strip()]

def _route_platform_for_site_row(item: Dict, fallback: str = "") -> str:
    for candidate in _site_row_platform_candidates(item, fallback=fallback):
        cleaned = _clean_platform_name(candidate)
        if cleaned and cleaned != GENERAL_PLATFORM_NAME:
            return cleaned
    cleaned_fallback = _clean_platform_name(fallback)
    if cleaned_fallback and cleaned_fallback != GENERAL_PLATFORM_NAME:
        return cleaned_fallback
    return GENERAL_PLATFORM_NAME

def _country_info_from_row(number: str, item: Dict) -> Dict:
    info = dict(_get_country_info(number))
    row = dict(item or {})
    raw_candidates = [
        row.get("country_name_ar", ""),
        row.get("country_name", ""),
        row.get("country", ""),
        row.get("country_label", ""),
    ]

    names_map = globals().get("DEMO_COUNTRY_NAMES", {}) or {}
    for raw in raw_candidates:
        text_value = re.sub(r"\s+", " ", str(raw or "").strip())
        if not text_value:
            continue
        key = text_value.lower()
        mapped = names_map.get(key)
        if isinstance(mapped, dict):
            merged = dict(info)
            merged.update({
                "name": mapped.get("name", info.get("name", text_value)),
                "flag": mapped.get("flag", info.get("flag", "🌐")),
                "code": mapped.get("code", info.get("code", "")),
                "digits_code": mapped.get("digits_code", info.get("digits_code", "")),
                "key": mapped.get("key", info.get("key", "unknown")),
            })
            return merged
        info["name"] = text_value
        return info
    return info

SITE_MANAGED_NUMBER_SOURCES = {
    'site',
    'site_picker',
    'site_add',
    'portal_json',
    'my_sms',
    'sms_ranges',
    'site_fetch',
}


def _is_site_managed_number_row(item: Dict) -> bool:
    source_value = str((item or {}).get('source') or '').strip().lower()
    if source_value in SITE_MANAGED_NUMBER_SOURCES:
        return True
    return source_value.startswith('site')



def _sync_site_country_numbers_for_platform(platform: str, country_key: str, items: List[Dict]) -> Dict[str, Any]:
    normalized_platform = _normalize_platform(platform)
    target_country_key = str(country_key or '').strip() or 'unknown'
    prepared_rows = _dedupe_numbers(items)
    existing_rows = list(numbers_db.get('numbers', [])) if isinstance(numbers_db, dict) else []

    before_target_rows: List[Dict] = []
    kept_rows: List[Dict] = []
    for item in existing_rows:
        if not isinstance(item, dict):
            continue
        row = _enrich_number_item(item)
        if not row:
            continue
        same_platform = _normalize_platform(row.get('platform', '')) == normalized_platform
        same_country = str(row.get('country_key') or '').strip() == target_country_key
        if same_platform and same_country and _is_site_managed_number_row(row):
            before_target_rows.append(row)
            continue
        kept_rows.append(row)

    merged_rows = _replace_numbers_db(kept_rows + prepared_rows)

    after_target_rows: List[Dict] = []
    for item in merged_rows:
        if not isinstance(item, dict):
            continue
        row = _enrich_number_item(item)
        if not row:
            continue
        if _normalize_platform(row.get('platform', '')) != normalized_platform:
            continue
        if str(row.get('country_key') or '').strip() != target_country_key:
            continue
        if not _is_site_managed_number_row(row):
            continue
        after_target_rows.append(row)

    def _numbers_set(rows: List[Dict]) -> set:
        found = set()
        for row in rows:
            number = _normalize_number(row.get('number', ''))
            if number:
                found.add(number)
        return found

    before_numbers = _numbers_set(before_target_rows)
    after_numbers = _numbers_set(after_target_rows)
    added_numbers = after_numbers - before_numbers
    removed_numbers = before_numbers - after_numbers
    kept_numbers = after_numbers & before_numbers

    added_items = [row for row in after_target_rows if _normalize_number(row.get('number', '')) in added_numbers]
    removed_items = [row for row in before_target_rows if _normalize_number(row.get('number', '')) in removed_numbers]

    return {
        'target_rows': after_target_rows,
        'added_items': added_items,
        'removed_items': removed_items,
        'added_count': len(added_numbers),
        'removed_count': len(removed_numbers),
        'existing_count': len(kept_numbers),
        'total_count': len(after_numbers),
    }



def _notify_admin_site_country_add(country_name: str, country_flag: str, platform: str, added_count: int, removed_count: int = 0, total_count: int = 0) -> None:
    if not ADMIN_ID:
        return
    safe_country_name = str(country_name or 'غير محددة').strip() or 'غير محددة'
    safe_country_flag = str(country_flag or '🌐').strip() or '🌐'
    lines = [
        f"📥 تمت إضافة أرقام للدولة {safe_country_flag} {safe_country_name}",
        '',
        f"📂 المنصة: {_display_platform_name(platform)}",
        f"🆕 الجديد: {max(0, int(added_count or 0))}",
        f"🗑️ المحذوف لأنه لم يعد موجوداً بالموقع: {max(0, int(removed_count or 0))}",
        f"📦 الإجمالي الحالي داخل البوت لنفس الدولة/المنصة: {max(0, int(total_count or 0))}",
        f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    try:
        bot.send_message(ADMIN_ID, "\n".join(lines))
    except Exception as admin_notify_err:
        logger.warning(f'تعذر إرسال إشعار خاص بإضافة أرقام الموقع: {admin_notify_err}')


def siteadd_platform_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, 'غير مصرح', show_alert=True)
        return
    state = site_add_state.get(call.from_user.id, {})
    selected_country_key = str(state.get('selected_country_key') or '').strip()
    rows = _site_add_selected_country_rows(state)
    if not selected_country_key or not rows:
        bot.answer_callback_query(call.id, 'اختر الدولة أولاً', show_alert=True)
        _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)
        return

    platforms = list(_platform_picker_platforms())
    try:
        idx = int(call.data.replace('siteaddplt_', '', 1))
        selected_platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, 'المنصة غير موجودة', show_alert=True)
        return

    bot.answer_callback_query(call.id, '⏳ جاري مزامنة أرقام الدولة...')
    state['selected_platform'] = selected_platform
    state['selected_country_rows'] = [dict(item) for item in rows]
    state['selected_country_total'] = len(rows)
    site_add_state[call.from_user.id] = state

    prepared = []
    now_label = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for row in rows:
        item = dict(row)
        item['selected_platform'] = selected_platform
        item['platform'] = selected_platform
        item['site_section'] = SITE_ADD_SOURCE_LABEL
        item['source'] = str(item.get('source') or 'site_picker').strip() or 'site_picker'
        item['added_at'] = now_label
        prepared.append(item)

    sync_result = _sync_site_country_numbers_for_platform(selected_platform, selected_country_key, prepared)
    added_for_target = list(sync_result.get('added_items', []) or [])
    removed_items = list(sync_result.get('removed_items', []) or [])
    current_target_rows = list(sync_result.get('target_rows', []) or [])
    duplicated_count = int(sync_result.get('existing_count', 0) or 0)

    if added_for_target:
        _notify_users_about_new_numbers(added_for_target, source='site')

    country_info = _country_info_from_row(rows[0].get('number', ''), rows[0]) if rows else {'name': 'غير محددة', 'flag': '🌐', 'code': ''}
    bucket = next((item for item in state.get('countries', []) if item.get('key') == selected_country_key), None) or {}
    country_title = bucket.get('display_name') or country_info.get('name', 'غير محددة')

    _notify_admin_site_country_add(
        country_title,
        country_info.get('flag', '🌐'),
        selected_platform,
        len(added_for_target),
        len(removed_items),
        len(current_target_rows),
    )

    text_lines = [
        '✅ تم تحديث أرقام الدولة داخل المنصة بنجاح',
        '',
        f"🌍 الدولة: {country_info.get('flag', '🌐')} {country_title}",
        f"📂 المنصة: {_display_platform_name(selected_platform)}",
        f"🆕 الأرقام الجديدة الآن: {len(added_for_target)}",
        f"♻️ الأرقام الموجودة مسبقاً ومازالت بالموقع: {duplicated_count}",
        f"🗑️ الأرقام التي تم حذفها لأنها اختفت من الموقع: {len(removed_items)}",
        f"📦 إجمالي أرقام الدولة الحالية داخل المنصة بعد المزامنة: {len(current_target_rows)}",
        '',
        'دلوقتي نفس الدولة بتتحدث كمزامنة كاملة: اللي بالموقع يفضل، واللي اتحذف من الموقع بيتشال من البوت.',
        'ولو حابب تضيف نفس الدولة على منصة تانية تقدر تختار منصة تانية من نفس الأزرار.',
    ]
    _send_or_edit(
        call.message.chat.id,
        "\n".join(text_lines),
        reply_markup=_build_site_add_number_markup(call.from_user.id),
        message_id=call.message.message_id,
    )


def siteadd_back_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)

def siteadd_refresh_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id, "جاري التحديث السريع في الخلفية...")
    _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=True, message_id=call.message.message_id)


def siteadd_number_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    state = site_add_state.get(call.from_user.id, {})
    selected_platform = state.get("selected_platform", "")
    if not selected_platform:
        bot.answer_callback_query(call.id, "اختر المنصة أولاً", show_alert=True)
        _launch_site_add_open_async(call.message.chat.id, call.from_user.id, refresh=False, message_id=call.message.message_id)
        return

    rows = _site_add_selected_country_rows(state)
    try:
        idx = int(call.data.replace("siteaddnum_", "", 1))
        picked = dict(rows[idx])
    except Exception:
        bot.answer_callback_query(call.id, "الرقم غير موجود", show_alert=True)
        return

    picked["selected_platform"] = selected_platform
    picked["platform"] = _route_platform_for_site_row(picked, fallback=selected_platform)
    picked["site_section"] = selected_platform
    picked["source"] = str(picked.get("source") or "site_picker").strip() or "site_picker"
    picked["added_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    before = list(numbers_db.get("numbers", []))
    merged = _append_numbers([picked])
    added_items = _find_newly_added_numbers(before, merged)
    final_row = _enrich_number_item(picked)
    country_label = f"{final_row.get('country_flag', '🌐')} {final_row.get('country_name_ar', 'غير محددة')}"

    if added_items:
        _notify_users_about_new_numbers(added_items, source='site')
        _notify_admin_site_country_add(
            final_row.get('country_name_ar', 'غير محددة'),
            final_row.get('country_flag', '🌐'),
            final_row.get('platform', selected_platform),
            len(added_items),
            0,
            len(added_items),
        )
        bot.answer_callback_query(call.id, "✅ تمت الإضافة")
        text = "\n".join([
            "✅ تم إضافة الرقم من الموقع بنجاح",
            "",
            f"📂 المنصة: {_display_platform_name(final_row.get('platform', selected_platform))}",
            f"🌍 الدولة: {country_label}",
            f"📱 الرقم: {final_row.get('number', '')}",
            "",
            "تم إسناد الرقم والدولة تلقائياً داخل المنصة المناسبة، وتم إرسال إشعار خاص للبوت باسم الدولة.",
        ])
    else:
        bot.answer_callback_query(call.id, "الرقم موجود مسبقاً", show_alert=True)
        text = "\n".join([
            "ℹ️ الرقم موجود مسبقاً داخل قاعدة البيانات",
            "",
            f"📂 المنصة الحالية: {_display_platform_name(final_row.get('platform', selected_platform))}",
            f"🌍 الدولة: {country_label}",
            f"📱 الرقم: {final_row.get('number', '')}",
        ])

    _send_or_edit(
        call.message.chat.id,
        text,
        reply_markup=_build_site_add_number_markup(call.from_user.id),
        message_id=call.message.message_id,
    )

SITE_SYNC_MAX_RANGES = max(50, int(str(_get("SITE_SYNC_MAX_RANGES", "120") or "120").strip() or "120"))

SITE_SYNC_MAX_SECONDS = max(60, int(str(_get("SITE_SYNC_MAX_SECONDS", "180") or "180").strip() or "180"))

_site_fetch_guard_lock = threading.Lock()

_site_fetch_guard_state = {"running": False, "started_at": 0.0}

def _site_fetch_guard_begin() -> tuple[bool, int]:
    now = time.time()
    with _site_fetch_guard_lock:
        running = bool(_site_fetch_guard_state.get("running"))
        started_at = float(_site_fetch_guard_state.get("started_at") or 0.0)
        elapsed = now - started_at if started_at else 0.0

        if running and elapsed < SITE_SYNC_MAX_SECONDS:
            remaining = max(1, int(SITE_SYNC_MAX_SECONDS - elapsed))
            return False, remaining

        if running and elapsed >= SITE_SYNC_MAX_SECONDS:
            logger.warning(
                "تم تجاهل حالة جلب قديمة/عالقة والسماح ببدء عملية جديدة تلقائياً"
            )

        _site_fetch_guard_state["running"] = True
        _site_fetch_guard_state["started_at"] = now
        return True, 0

def _site_fetch_guard_end() -> None:
    with _site_fetch_guard_lock:
        _site_fetch_guard_state["running"] = False
        _site_fetch_guard_state["started_at"] = 0.0


# ══════════════════════════════════════════════════════════════
#  DYNAMIC PATCH — show all detected platforms + keep special sections visible
# ══════════════════════════════════════════════════════════════
GENERAL_PLATFORM_NAME = "General"
ALL_NUMBERS_PLATFORM_NAME = "General"

DEFAULT_SITE_PLATFORMS = [
    "WhatsApp", "Telegram", "TikTok", "Instagram",
    "Facebook", "Twitter", "Snapchat", "Line",
    "WeChat", "Viber", "Discord", "Gmail",
    "Hotmail", "Yahoo", "Microsoft", "Apple",
    "Amazon", "Netflix", "Uber", "PayPal",
]
SPECIAL_PLATFORMS = set()
ALLOWED_PLATFORMS = [GENERAL_PLATFORM_NAME] + list(DEFAULT_SITE_PLATFORMS)
ALLOWED_PLATFORMS = list(dict.fromkeys(ALLOWED_PLATFORMS))
ALLOWED_PLATFORM_SET = set(ALLOWED_PLATFORMS)
DEFAULT_PLATFORMS = list(DEFAULT_SITE_PLATFORMS)
dynamic_platforms = list(DEFAULT_PLATFORMS)

PLATFORM_BUTTON_ICONS.update({
    "WhatsApp": "💬",
    "Telegram": "✈️",
    "TikTok": "🎵",
    "Instagram": "📸",
    "Facebook": "📘",
    "Twitter": "🐦",
    "Snapchat": "👻",
    "Line": "💚",
    "WeChat": "🟢",
    "Viber": "📞",
    "Discord": "🎮",
    "Gmail": "📧",
    "Hotmail": "📨",
    "Yahoo": "📬",
    "Microsoft": "🪟",
    "Apple": "🍎",
    "Amazon": "🛒",
    "Netflix": "🎬",
    "Uber": "🚕",
    "PayPal": "💳",
    "General": "📁",
})

DEMO_SERVICE_META.update({
    "WhatsApp": {"icon": "💬", "label": "WhatsApp"},
    "Facebook": {"icon": "📘", "label": "Facebook"},
    "TikTok": {"icon": "🎵", "label": "TikTok"},
    "Telegram": {"icon": "✈️", "label": "Telegram"},
    "Instagram": {"icon": "📸", "label": "Instagram"},
    "General": {"icon": "📁", "label": "General"},
})

PLATFORM_CANONICAL_ALIASES.update({
    "general": "General",
    "all": "General",
    "all numbers": "General",
    "كل الارقام": "General",
    "جميع الارقام": "General",
    "whatsapp": "WhatsApp",
    "whats app": "WhatsApp",
    "واتساب": "WhatsApp",
    "واتس اب": "WhatsApp",
    "telegram": "Telegram",
    "تيليجرام": "Telegram",
    "تلجرام": "Telegram",
    "facebook": "Facebook",
    "face book": "Facebook",
    "فيسبوك": "Facebook",
    "فيس بوك": "Facebook",
    "instagram": "Instagram",
    "insta": "Instagram",
    "انستا": "Instagram",
    "انستغرام": "Instagram",
    "انستجرام": "Instagram",
    "انستقرام": "Instagram",
    "tiktok": "TikTok",
    "tik tok": "TikTok",
    "تيك توك": "TikTok",
    "تيكتوك": "TikTok",
    "twitter": "Twitter",
    "x": "Twitter",
    "تويتر": "Twitter",
    "snapchat": "Snapchat",
    "سناب": "Snapchat",
    "سناب شات": "Snapchat",
    "line": "Line",
    "لين": "Line",
    "wechat": "WeChat",
    "وي تشات": "WeChat",
    "ويتشات": "WeChat",
    "viber": "Viber",
    "فايبر": "Viber",
    "discord": "Discord",
    "ديسكورد": "Discord",
    "gmail": "Gmail",
    "جيميل": "Gmail",
    "hotmail": "Hotmail",
    "هوتميل": "Hotmail",
    "هوت ميل": "Hotmail",
    "yahoo": "Yahoo",
    "ياهو": "Yahoo",
    "microsoft": "Microsoft",
    "مايكروسوفت": "Microsoft",
    "outlook": "Microsoft",
    "اوتلوك": "Microsoft",
    "apple": "Apple",
    "ابل": "Apple",
    "amazon": "Amazon",
    "امازون": "Amazon",
    "netflix": "Netflix",
    "نتفلكس": "Netflix",
    "uber": "Uber",
    "اوبر": "Uber",
    "paypal": "PayPal",
    "pay pal": "PayPal",
    "باي بال": "PayPal",
})


def _is_general_bucket_platform(value: str) -> bool:
    key = _platform_alias_key(value)
    return key in {
        'general', 'all', 'all numbers', 'كل الارقام', 'جميع الارقام'
    }


def _is_allowed_platform(value: str) -> bool:
    normalized = _clean_platform_name(value)
    return bool(normalized)


def _display_platform_name(value: str) -> str:
    normalized = _normalize_platform(value)
    if normalized == 'General':
        return ALL_NUMBERS_PLATFORM_NAME
    return normalized


def _clean_platform_name(value: str) -> str:
    name = re.sub(r'\s+', ' ', str(value or '').strip())
    if not name:
        return ''
    alias_key = _platform_alias_key(name)
    if alias_key in PLATFORM_BLACKLIST:
        return ''
    if _is_general_bucket_platform(alias_key):
        return 'General'
    canonical = PLATFORM_CANONICAL_ALIASES.get(alias_key)
    if canonical:
        return canonical
    compact_key = alias_key.replace(' ', '')
    for alias, canonical in PLATFORM_CANONICAL_ALIASES.items():
        alias_compact = alias.replace(' ', '')
        if compact_key == alias_compact or alias_compact in compact_key or compact_key in alias_compact:
            if canonical:
                return canonical
    safe_name = re.sub(r'[_\-|/]+', ' ', name)
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    if not safe_name:
        return ''
    if re.fullmatch(r'[A-Za-z0-9 .+&()]+', safe_name):
        parts = []
        for part in safe_name.split():
            if part.isupper() or len(part) <= 3:
                parts.append(part.upper())
            else:
                parts.append(part[:1].upper() + part[1:])
        return ' '.join(parts)
    return safe_name


def _normalize_platform(value: str) -> str:
    cleaned = _clean_platform_name(value)
    return cleaned or 'General'


def _platform_label_loose(value: str) -> str:
    cleaned = _clean_platform_name(value)
    return '' if cleaned == GENERAL_PLATFORM_NAME else cleaned


def _load_site_cookies(session: requests.Session) -> bool:
    """يحمّل كل مصادر الكوكيز بالتجميع لضمان وجود session + XSRF معاً داخل نفس الجلسة."""
    loaded_any = False

    try:
        loaded_any = _load_runtime_cookies(session) or loaded_any
    except Exception as runtime_cookie_err:
        logger.warning(f"Runtime cookie load warning: {runtime_cookie_err}")

    try:
        loaded_any = _load_cookies_from_json_file(session) or loaded_any
    except Exception as cookie_file_err:
        logger.warning(f"Cookie JSON load warning: {cookie_file_err}")

    raw_cookie = str(SITE_COOKIE or "").strip()
    if raw_cookie:
        try:
            _apply_site_cookie(session, raw_cookie)
            loaded_any = True
            if _pick_cookie_value(session, "ivas_sms_session", "laravel_session", "session", "SESSION", "site_session"):
                logger.info("🍪 تم تحميل كوكي الجلسة من SITE_COOKIE")
        except Exception as site_cookie_err:
            logger.warning(f"SITE_COOKIE load warning: {site_cookie_err}")

    try:
        current_session_cookie = _pick_cookie_value(session, "ivas_sms_session", "laravel_session", "session", "SESSION", "site_session")
        current_xsrf_cookie = _pick_cookie_value(session, "XSRF-TOKEN", "XSRF_TOKEN")
        if (not current_session_cookie) or (not current_xsrf_cookie):
            loaded_any = _load_cookie_items(session, EMBEDDED_SITE_COOKIES, "الكوكيز المدمجة داخل الملف") or loaded_any
    except Exception as embedded_cookie_err:
        logger.warning(f"Embedded cookie load warning: {embedded_cookie_err}")

    _refresh_xsrf_header(session)
    return bool(_pick_cookie_value(session, "ivas_sms_session", "laravel_session", "session", "SESSION", "site_session") or loaded_any)

def _normalize_number(value: str) -> str:
    """تنسيق الرقم بشكل موحّد، وتحويل 00 إلى +، وإضافة + تلقائياً للأرقام الدولية."""
    raw = str(value or "").strip()
    if not raw:
        return ""

    cleaned = re.sub(r"[^\d+]", "", raw)
    if not cleaned:
        return ""

    if cleaned.startswith("00"):
        digits = re.sub(r"\D", "", cleaned[2:])
        return f"+{digits}" if digits else ""

    if cleaned.startswith("+"):
        digits = re.sub(r"\D", "", cleaned[1:])
        return f"+{digits}" if digits else ""

    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return ""

    # إذا كان الرقم يبدو كرقم دولي، أضف + تلقائياً
    if len(digits) >= 8:
        return f"+{digits}"

    return digits

def _get_country_info(number: str) -> dict:
    """يرجع معلومات الدولة حتى لو الرقم بدون + أو يبدأ بـ 00، مع دعم واسع للدول."""
    num = _normalize_number(number)
    digits = re.sub(r"\D", "", num)
    if not digits:
        return _static_country_info_from_digits("")

    try:
        import phonenumbers
        from phonenumbers import geocoder

        candidate = num if str(num).startswith("+") else f"+{digits}"
        parsed = phonenumbers.parse(candidate, None)
        country_code = str(getattr(parsed, "country_code", "") or "")

        if country_code:
            fallback = _static_country_info_from_digits(country_code)
            region = phonenumbers.region_code_for_number(parsed) or phonenumbers.region_code_for_country_code(parsed.country_code)
            localized_name = geocoder.country_name_for_number(parsed, "ar") or geocoder.country_name_for_number(parsed, "en")
            return {
                "name": localized_name or fallback.get("name", "غير محددة"),
                "flag": _region_to_flag(region) if region else fallback.get("flag", "🌐"),
                "code": f"+{country_code}",
                "digits_code": country_code,
                "key": country_code or "unknown",
            }
    except Exception:
        pass

    return _static_country_info_from_digits(digits)


_numbers_store_lock = threading.RLock()


def _sqlite_connect() -> sqlite3.Connection:
    NUMBERS_SQLITE_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(NUMBERS_SQLITE_FILE, timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-200000")
    conn.execute("PRAGMA mmap_size=268435456")
    return conn


def _init_numbers_sqlite() -> None:
    with _numbers_store_lock:
        conn = _sqlite_connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS numbers_snapshot (
                    number TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    country_key TEXT,
                    country_name_ar TEXT,
                    country_flag TEXT,
                    country_code TEXT,
                    source TEXT,
                    added_at TEXT,
                    status TEXT,
                    availability INTEGER,
                    last_checked_at TEXT,
                    raw_json TEXT NOT NULL,
                    PRIMARY KEY (number, platform)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source_label TEXT,
                    ok INTEGER NOT NULL,
                    total_received INTEGER NOT NULL,
                    valid_count INTEGER NOT NULL,
                    saved_count INTEGER NOT NULL,
                    rejected_count INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def _write_sync_report(report: Dict[str, Any]) -> None:
    payload = dict(report or {})
    payload.setdefault("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    save_json(SYNC_REPORT_FILE, payload)
    try:
        _init_numbers_sqlite()
        with _numbers_store_lock:
            conn = _sqlite_connect()
            try:
                conn.execute(
                    """
                    INSERT INTO sync_runs (
                        created_at, source_label, ok, total_received, valid_count,
                        saved_count, rejected_count, success_rate, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(payload.get("created_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()),
                        str(payload.get("source_label") or "unknown"),
                        1 if payload.get("ok") else 0,
                        int(payload.get("total_received") or 0),
                        int(payload.get("valid_count") or 0),
                        int(payload.get("saved_count") or 0),
                        int(payload.get("rejected_count") or 0),
                        float(payload.get("success_rate") or 0.0),
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as metrics_err:
        logger.warning(f"تعذر تسجيل إحصائيات المزامنة داخل SQLite: {metrics_err}")


def _load_numbers_from_sqlite() -> List[Dict]:
    if not NUMBERS_SQLITE_FILE.exists():
        return []
    try:
        _init_numbers_sqlite()
        with _numbers_store_lock:
            conn = _sqlite_connect()
            try:
                rows = conn.execute(
                    "SELECT raw_json FROM numbers_snapshot ORDER BY country_key, platform, number"
                ).fetchall()
            finally:
                conn.close()
        items = []
        for row in rows:
            raw_json = row["raw_json"] if isinstance(row, sqlite3.Row) else row[0]
            try:
                item = json.loads(raw_json)
                if isinstance(item, dict):
                    items.append(item)
            except Exception:
                continue
        return items
    except Exception as sqlite_load_err:
        logger.warning(f"تعذر تحميل الأرقام من SQLite: {sqlite_load_err}")
        return []


def _store_numbers_snapshot(items: List[Dict], source_label: str = "runtime", metrics: Optional[Dict[str, Any]] = None) -> List[Dict]:
    unique = _consolidate_number_sources(items)
    numbers_db["numbers"] = unique
    if isinstance(numbers_db, dict):
        numbers_db["general_numbers"] = [dict(item) for item in unique]
    save_json(NUMBERS_FILE, numbers_db)
    _invalidate_numbers_runtime_index()

    try:
        _init_numbers_sqlite()
        with _numbers_store_lock:
            conn = _sqlite_connect()
            try:
                conn.execute("DELETE FROM numbers_snapshot")
                conn.executemany(
                    """
                    INSERT INTO numbers_snapshot (
                        number, platform, country_key, country_name_ar, country_flag,
                        country_code, source, added_at, status, availability,
                        last_checked_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(item.get("number") or ""),
                            str(item.get("platform") or "General"),
                            str(item.get("country_key") or ""),
                            str(item.get("country_name_ar") or ""),
                            str(item.get("country_flag") or ""),
                            str(item.get("country_code") or ""),
                            str(item.get("source") or source_label),
                            str(item.get("added_at") or ""),
                            str(item.get("status") or ""),
                            1 if item.get("availability") else 0,
                            str(item.get("last_checked_at") or ""),
                            json.dumps(item, ensure_ascii=False),
                        )
                        for item in unique
                    ],
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as sqlite_save_err:
        logger.warning(f"تعذر تحديث SQLite للأرقام: {sqlite_save_err}")

    if metrics is not None:
        _write_sync_report(metrics)

    _refresh_dynamic_platforms()
    _get_numbers_runtime_index()
    return unique


def _bootstrap_numbers_storage() -> int:
    _init_numbers_sqlite()
    sqlite_items = _load_numbers_from_sqlite()
    if sqlite_items:
        consolidated = _consolidate_number_sources(sqlite_items)
        numbers_db["numbers"] = consolidated
        if isinstance(numbers_db, dict):
            numbers_db["general_numbers"] = [dict(item) for item in consolidated]
        save_json(NUMBERS_FILE, numbers_db)
        _invalidate_numbers_runtime_index()
        _refresh_dynamic_platforms()
        _get_numbers_runtime_index()
        return len(consolidated)

    current_json_items = _consolidate_number_sources(numbers_db.get("numbers", []))
    if current_json_items:
        _store_numbers_snapshot(current_json_items, source_label="json_bootstrap")
    return len(current_json_items)

def _enrich_number_item(item: Dict) -> Dict:
    row = dict(item or {})
    number = _normalize_number(row.get("number", ""))
    if not number:
        return {}

    selected_platform = row.get("selected_platform", "")
    platform = _route_platform_for_site_row(
        row,
        fallback=selected_platform or row.get("platform") or row.get("service") or row.get("site_section") or GENERAL_PLATFORM_NAME,
    )
    country_info = _country_info_from_row(number, row)

    row["number"] = number
    row["platform"] = platform
    row["site_section"] = str(row.get("site_section") or platform).strip() or platform
    row.setdefault("source", "manual")
    row.setdefault("added_at", time.ctime())
    row["country_key"] = country_info.get("key", "unknown")
    row["country_name_ar"] = country_info.get("name", "غير محددة")
    row["country_flag"] = country_info.get("flag", "🌐")
    row["country_code"] = country_info.get("code", "")
    return row

def _dedupe_numbers(items: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = _enrich_number_item(item)
        if not row:
            continue
        key = (row["number"], row["platform"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique

def _consolidate_number_sources(items: List[Dict]) -> List[Dict]:
    priority_order = {
        "sms_range": 4,
        "portal_json": 3,
        "api": 2,
        "manual": 2,
        "scrape": 1,
    }
    valid_items = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = _enrich_number_item(item)
        if not row:
            continue
        valid_items.append(row)

    valid_items.sort(
        key=lambda row: (
            priority_order.get(str(row.get("source", "")).lower(), 0),
            len(str(row.get("platform", ""))),
        ),
        reverse=True,
    )

    seen_pairs = set()
    merged = []
    for row in valid_items:
        key = (row["number"], row["platform"].lower())
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        merged.append(row)
    return merged


def _append_numbers(items: List[Dict]) -> List[Dict]:
    existing = list(numbers_db.get('numbers', [])) if isinstance(numbers_db, dict) else []
    merged = _consolidate_number_sources(existing + list(items or []))
    return _store_numbers_snapshot(merged, source_label="runtime_append")


def _replace_numbers_db(items: List[Dict]) -> List[Dict]:
    unique = _consolidate_number_sources(items)
    return _store_numbers_snapshot(unique, source_label="runtime_replace")


def _save_numbers() -> None:
    current = list(numbers_db.get('numbers', [])) if isinstance(numbers_db, dict) else []
    _store_numbers_snapshot(current, source_label="runtime_save")


def _remove_number_from_storage(number: str) -> int:
    target = _normalize_number(number)
    if not target or not isinstance(numbers_db, dict):
        return 0
    current_rows = list(numbers_db.get('numbers', []))
    kept_rows = [dict(item) for item in current_rows if _normalize_number(item.get('number', '')) != target]
    removed_count = len(current_rows) - len(kept_rows)
    if removed_count <= 0:
        return 0
    _replace_numbers_db(kept_rows)
    try:
        pending_activation.pop(target, None)
    except Exception:
        pass
    return removed_count


_numbers_runtime_index_lock = threading.RLock()
_numbers_runtime_index: Dict[str, Any] = {
    'ready': False,
    'all_rows': [],
    'platform_rows': {},
    'country_groups': {},
    'platform_country_rows': {},
    'platform_counts': {},
}
_country_markup_cache_lock = threading.RLock()
_country_markup_cache: Dict[Tuple[str, int], Optional[types.InlineKeyboardMarkup]] = {}


def _invalidate_country_markup_cache() -> None:
    with _country_markup_cache_lock:
        _country_markup_cache.clear()


def _invalidate_numbers_runtime_index() -> None:
    global _numbers_runtime_index
    _invalidate_country_markup_cache()
    with _numbers_runtime_index_lock:
        _numbers_runtime_index = {
            'ready': False,
            'all_rows': [],
            'platform_rows': {},
            'country_groups': {},
            'platform_country_rows': {},
            'platform_counts': {},
        }


def _runtime_country_info_from_row(row: Dict) -> Dict[str, str]:
    info = {
        'name': str(row.get('country_name_ar') or '').strip(),
        'flag': str(row.get('country_flag') or '').strip(),
        'code': str(row.get('country_code') or '').strip(),
        'digits_code': re.sub(r'\D', '', str(row.get('country_code') or '')),
        'key': str(row.get('country_key') or '').strip() or 'unknown',
    }
    if info['name'] and info['flag']:
        if not info['digits_code'] and info['code']:
            info['digits_code'] = re.sub(r'\D', '', info['code'])
        return info
    return _get_country_info(str(row.get('number') or ''))


def _build_numbers_runtime_index() -> Dict[str, Any]:
    platform_rows: Dict[str, List[Dict]] = {}
    country_groups: Dict[str, List[Dict[str, Any]]] = {}
    platform_country_rows: Dict[str, Dict[str, List[Dict]]] = {}
    platform_counts: Dict[str, int] = {}
    all_rows: List[Dict] = []
    seen_general: set = set()
    seen_platform_numbers: Dict[str, set] = {}
    platform_country_base_rows: Dict[str, Dict[str, List[Dict]]] = {}
    platform_country_meta: Dict[str, Dict[str, Dict[str, Any]]] = {}
    raw_items = list(numbers_db.get('numbers', [])) if isinstance(numbers_db, dict) else []
    per_country_limit = 100

    for item in raw_items:
        row = _enrich_number_item(item)
        if not row:
            continue
        number = str(row.get('number') or '').strip()
        platform = _normalize_platform(row.get('platform', ''))
        if not number:
            continue

        general_key = (number, platform)
        if general_key not in seen_general:
            seen_general.add(general_key)
            all_rows.append(dict(row))

        platform_seen = seen_platform_numbers.setdefault(platform, set())
        if number in platform_seen:
            continue
        platform_seen.add(number)

        row_copy = dict(row)
        platform_rows.setdefault(platform, []).append(row_copy)
        info = _runtime_country_info_from_row(row_copy)
        country_key = str(info.get('key') or 'unknown') or 'unknown'

        meta_map = platform_country_meta.setdefault(platform, {})
        meta_map[country_key] = {
            'name': info.get('name', 'غير محددة'),
            'flag': info.get('flag', '🌐'),
            'code': info.get('code', ''),
            'digits_code': info.get('digits_code', ''),
        }

        row_with_country = dict(row_copy)
        row_with_country['country'] = info
        platform_country_base_rows.setdefault(platform, {}).setdefault(country_key, []).append(row_with_country)

    for platform, rows in platform_rows.items():
        rows.sort(key=lambda row: str(row.get('number') or ''))
        platform_counts[platform] = len(rows)

    for platform, country_map in platform_country_base_rows.items():
        grouped_items: List[Dict[str, Any]] = []
        meta_map = platform_country_meta.get(platform, {})
        for base_key, rows in country_map.items():
            sorted_rows = [dict(item) for item in rows]
            sorted_rows.sort(key=lambda row: str(row.get('number') or ''))
            meta = meta_map.get(base_key, {})
            duplicate_total = max(1, (len(sorted_rows) + per_country_limit - 1) // per_country_limit)
            for duplicate_index in range(duplicate_total):
                start = duplicate_index * per_country_limit
                end = start + per_country_limit
                chunk_rows = [dict(item) for item in sorted_rows[start:end]]
                if not chunk_rows:
                    continue
                chunk_key = f"{base_key}::{duplicate_index + 1}"
                grouped_items.append({
                    'key': chunk_key,
                    'base_key': base_key,
                    'name': meta.get('name', 'غير محددة'),
                    'flag': meta.get('flag', '🌐'),
                    'code': meta.get('code', ''),
                    'digits_code': meta.get('digits_code', ''),
                    'count': len(chunk_rows),
                    'duplicate_index': duplicate_index + 1,
                    'duplicate_total': duplicate_total,
                    'is_duplicate': duplicate_total > 1,
                })
                platform_country_rows.setdefault(platform, {})[chunk_key] = chunk_rows
        country_groups[platform] = sorted(
            grouped_items,
            key=lambda item: (
                item.get('name') == 'غير محددة',
                item.get('name', ''),
                int(item.get('duplicate_index', 1) or 1),
                item.get('digits_code', ''),
            ),
        )

    platform_counts['General'] = len(all_rows)

    return {
        'ready': True,
        'all_rows': all_rows,
        'platform_rows': platform_rows,
        'country_groups': country_groups,
        'platform_country_rows': platform_country_rows,
        'platform_counts': platform_counts,
    }


def _get_numbers_runtime_index() -> Dict[str, Any]:
    global _numbers_runtime_index
    with _numbers_runtime_index_lock:
        if not _numbers_runtime_index.get('ready'):
            _numbers_runtime_index = _build_numbers_runtime_index()
        return _numbers_runtime_index


def _country_button_label(country: Dict) -> str:
    code = str(country.get("code") or country.get("digits_code") or "").strip()
    code_part = f" ({code})" if code else ""
    return f"{country.get('flag', '🌐')} {country.get('name', 'غير محددة')}{code_part} • {country.get('count', 0)}"

def _build_user_main_keyboard() -> types.ReplyKeyboardMarkup:
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("📱 الأقسام المتاحة", "💎 أرقام مدفوعة")
    mk.add("📢 قناة المطور", "🆘 الدعم الفني")
    mk.add("✉️ إرسال رسالة للمطور")
    return mk


COUNTRY_PAGE_SIZE = max(10, int(_get("COUNTRY_PAGE_SIZE", "10") or "10"))
_discovered_platforms_cache: List[str] = []


def _refresh_dynamic_platforms(extra_platforms: Optional[List[str]] = None):
    global dynamic_platforms, _discovered_platforms_cache
    ordered: List[str] = []
    discovered_now: List[str] = []
    seed_platforms = [plat for plat in DEFAULT_PLATFORMS if plat and plat != GENERAL_PLATFORM_NAME]
    for plat in seed_platforms:
        if plat not in ordered:
            ordered.append(plat)
    for plat in _discovered_platforms_cache:
        norm = _clean_platform_name(plat)
        if norm and norm != GENERAL_PLATFORM_NAME and norm not in ordered:
            ordered.append(norm)
    for item in numbers_db.get('numbers', []):
        plat = _clean_platform_name(item.get('platform', ''))
        if plat and plat != GENERAL_PLATFORM_NAME and plat not in ordered:
            ordered.append(plat)
    for plat in extra_platforms or []:
        norm = _clean_platform_name(plat)
        if norm and norm != GENERAL_PLATFORM_NAME:
            discovered_now.append(norm)
            if norm not in ordered:
                ordered.append(norm)
    if discovered_now:
        merged_cache: List[str] = []
        for plat in list(_discovered_platforms_cache) + discovered_now:
            norm = _clean_platform_name(plat)
            if norm and norm != GENERAL_PLATFORM_NAME and norm not in merged_cache:
                merged_cache.append(norm)
        _discovered_platforms_cache = merged_cache
    dynamic_platforms = ordered or seed_platforms or [plat for plat in ALLOWED_PLATFORMS if plat != GENERAL_PLATFORM_NAME]
    _invalidate_country_markup_cache()


def _platform_picker_platforms() -> List[str]:
    ordered = [plat for plat in dynamic_platforms if plat and plat != GENERAL_PLATFORM_NAME]
    if not ordered:
        ordered = [plat for plat in DEFAULT_PLATFORMS if plat and plat != GENERAL_PLATFORM_NAME]
    return ordered


def _user_visible_platforms() -> List[str]:
    counts = _platform_counts_snapshot()
    visible: List[str] = []
    for platform in _platform_picker_platforms():
        normalized = _normalize_platform(platform)
        if int(counts.get(normalized, 0) or 0) > 0:
            visible.append(platform)
    return visible


def _numbers_for_platform(platform: str) -> List[Dict]:
    normalized = _normalize_platform(platform)
    index = _get_numbers_runtime_index()
    if normalized == 'General':
        rows = index.get('all_rows', []) or []
    else:
        rows = index.get('platform_rows', {}).get(normalized, []) or []
    return [dict(item) for item in rows]


def _platform_button_label(platform: str, include_count: bool = True, counts_map: Optional[Dict[str, int]] = None) -> str:
    normalized = _normalize_platform(platform)
    display_name = _display_platform_name(normalized)
    icon = PLATFORM_BUTTON_ICONS.get(display_name) or PLATFORM_BUTTON_ICONS.get(normalized, '📂')
    if include_count and normalized not in SPECIAL_PLATFORMS:
        count = None
        if isinstance(counts_map, dict):
            count = counts_map.get(normalized)
        if count is None:
            count = len(_numbers_for_platform(platform))
        return f"{icon} {display_name} ({count})"
    return f"{icon} {display_name}"

def _platform_counts_snapshot() -> Dict[str, int]:
    platforms = list(_platform_picker_platforms())
    index = _get_numbers_runtime_index()
    cached_counts = index.get('platform_counts', {}) or {}
    counts: Dict[str, int] = {key: int(cached_counts.get(key, 0) or 0) for key in platforms}
    if GENERAL_PLATFORM_NAME not in counts:
        counts[GENERAL_PLATFORM_NAME] = 0
    counts[GENERAL_PLATFORM_NAME] = int(cached_counts.get('General', counts.get(GENERAL_PLATFORM_NAME, 0)) or 0)
    return counts


def _count_non_empty_platforms(platforms: List[str], counts: Dict[str, int]) -> int:
    return sum(1 for platform in platforms if int(counts.get(_normalize_platform(platform), 0) or 0) > 0)

def _build_demo_home_text(platforms: List[str], counts: Dict[str, int]) -> str:
    if not platforms:
        return (
            '🌍 *الأقسام المتاحة داخل البوت*\n\n'
            '📭 حالياً لا توجد منصات عليها أرقام متاحة للمستخدمين.\n\n'
            'جرّب مرة تانية بعد إضافة أرقام جديدة من الموقع أو راسل المطور من الزر الموجود بالأسفل.'
        )
    preview = [f"• {_platform_button_label(platform, counts_map=counts)}" for platform in platforms]
    return (
        '🌍 *الأقسام المتاحة داخل البوت*\n\n'
        f'✅ المنصات الظاهرة للمستخدمين: {len(platforms)}\n\n'
        + '\n'.join(preview)
        + '\n\n⚡ لا يتم إظهار إلا المنصات اللي عليها أرقام حالياً.'
    )

def _service_counts() -> Dict[str, int]:
    counts: Dict[str, int] = {key: 0 for key in ALLOWED_PLATFORMS}
    cached_counts = _get_numbers_runtime_index().get('platform_counts', {}) or {}
    for key in list(counts.keys()):
        counts[key] = int(cached_counts.get(key, 0) or 0)
    counts['General'] = int(cached_counts.get('General', len(_numbers_for_platform('General'))) or 0)
    return counts


def _send_demo_home(chat_id: int, message_id: Optional[int] = None):
    platforms = _user_visible_platforms()
    counts = _platform_counts_snapshot()
    text = _build_demo_home_text(platforms, counts)
    _send_or_edit(
        chat_id,
        text,
        reply_markup=_build_platform_picker_markup(),
        message_id=message_id,
        parse_mode='Markdown',
    )


def _build_developer_panel_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton('📚 الأقسام المتاحة', callback_data='dev_sections'),
        types.InlineKeyboardButton('🔐 الاشتراك الإجباري', callback_data='dev_sub_status'),
    )
    mk.add(
        types.InlineKeyboardButton('💎 الأرقام المدفوعة', callback_data='dev_paid_summary'),
        types.InlineKeyboardButton('📢 قناة المطور', callback_data='dev_channel_info'),
    )
    mk.add(
        types.InlineKeyboardButton('➕ إضافة أرقام من الموقع', callback_data='dev_fetch_site'),
        types.InlineKeyboardButton('🍪 إدارة الكوكيز', callback_data='dev_cookie_center'),
    )
    mk.add(
        types.InlineKeyboardButton('📤 تصدير TXT للمنصات', callback_data='dev_export_all_txt'),
        types.InlineKeyboardButton('🖊️ تعديل رسالة الترحيب', callback_data='dev_edit_welcome'),
    )
    mk.add(
        types.InlineKeyboardButton('📋 عرض كل الأوامر', callback_data='dev_show_commands'),
        types.InlineKeyboardButton('🧪 تدقيق قاعدة الأرقام', callback_data='dev_db_audit'),
    )
    return mk


def _developer_commands_text() -> str:
    return (
        'أوامر الإدارة السريعة:\n\n'
        '• /start ← فتح البوت أو لوحة الإدارة\n'
        '• /cookies ← مركز إدارة الكوكيز\n'
        '• /setcookies ← استبدال كل Runtime cookies\n'
        '• /addcookies ← إضافة / دمج كوكيز جديدة\n'
        '• /delcookies ← حذف كوكيز محددة\n'
        '• /showcookies ← عرض الكوكيز الحالية\n'
        '• /clearcookies ← حذف كل runtime cookies\n'
        '• /dbaudit ← تدقيق قاعدة الأرقام\n'
        '• /deleteplatform ← حذف كل أرقام منصة\n'
        '• /confirm ← تأكيد حذف رقم من الانتظار\n\n'
        'ومن لوحة المطور تقدر تستخدم زر ➕ إضافة أرقام من الموقع ثم تختار الدولة من my_sms وبعدها المنصة ليتم تسجيل كل أرقام الدولة دفعة واحدة.'
    )


def _process_manual_add(message):
    selected_platform = admin_pending_platform.pop(message.from_user.id, "")
    lines = message.text.strip().splitlines()
    prepared = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            if ":" in line:
                num, plat = line.split(":", 1)
                platform_name = _clean_platform_name(plat)
            else:
                num = line
                platform_name = _clean_platform_name(selected_platform)

            normalized_num = _normalize_number(num)
            if normalized_num and platform_name:
                prepared.append({
                    "number": normalized_num,
                    "platform": platform_name,
                    "source": "manual",
                    "added_at": time.ctime(),
                })
        except Exception:
            continue

    if not prepared:
        bot.reply_to(message, "❌ ما لقيتش أرقام صالحة. لازم تختار منصة من الأربع المنصات المدعومة أو تستخدم الصيغة `الرقم:المنصة`.")
        return

    before_items = list(numbers_db.get("numbers", []))
    merged = _append_numbers(prepared)
    _refresh_dynamic_platforms([item.get("platform", "") for item in prepared])
    added_items = _find_newly_added_numbers(before_items, merged)
    added = len(added_items)
    log_event("MANUAL_ADD", {"count": added, "platform": selected_platform or "mixed"})
    if added_items:
        _notify_users_about_new_numbers(added_items, source="manual")

    platform_counts = {}
    for item in prepared:
        plat = item.get("platform", "General")
        platform_counts[plat] = platform_counts.get(plat, 0) + 1
    details = "\n".join(f"• {plat}: {cnt} رقم" for plat, cnt in platform_counts.items())

    bot.reply_to(
        message,
        f"✅ تمت إضافة/تحديث *{added}* رقم.\n\n{details}",
        parse_mode="Markdown",
    )

_handlers_registered = False
_handlers_register_lock = threading.Lock()

def _reply_with_internal_error(payload, is_callback: bool = False):
    notice = "⚠️ حصل خطأ داخلي وتم تسجيله. جرّب مرة تانية بعد ثواني."
    if is_callback:
        try:
            bot.answer_callback_query(payload.id, notice, show_alert=True)
        except Exception:
            pass
        try:
            bot.send_message(payload.message.chat.id, notice)
        except Exception:
            pass
        return
    try:
        bot.reply_to(payload, notice)
    except Exception:
        pass

def _safe_handler_call(handler, payload, context: str, is_callback: bool = False):
    try:
        return handler(payload)
    except Exception as handler_err:
        handler_name = getattr(handler, "__name__", "handler")
        logger.exception(f"Handler crash | {context} | {handler_name}: {handler_err}")
        _reply_with_internal_error(payload, is_callback=is_callback)
        return None


def _dispatch_text_message(message):
    text = str(getattr(message, "text", "") or "").strip()
    if not text:
        return

    command = text.split()[0].split("@", 1)[0].lower()
    command_map = {
        "/start": cmd_start,
        "/cookies": cookies_center_command,
        "/setcookies": setcookies_command,
        "/setcookie": setcookies_command,
        "/addcookies": addcookies_command,
        "/appendcookies": addcookies_command,
        "/delcookies": delcookies_command,
        "/deletecookies": delcookies_command,
        "/removecookies": delcookies_command,
        "/showcookies": showcookies_command,
        "/clearcookies": clearcookies_command,
        "/siteplatforms": siteplatforms_command,
        "/sitecodes": sitecodes_command,
        "/dbaudit": db_audit_command,
        "/confirm": confirm_number,
        "/deleteplatform": delete_platform_command,
        "/delplatform": delete_platform_command,
    }
    handler = command_map.get(command)
    if handler:
        _safe_handler_call(handler, message, f"command={command}")
        return

    if not bot_active and not is_admin(message):
        bot.reply_to(message, "⏸️ البوت متوقف مؤقتاً حالياً. جرّب بعد تشغيله من لوحة الإدارة.")
        return

    text_map = {
        "📱 الأقسام المتاحة": user_sections_handler,
        "💎 أرقام مدفوعة": paid_numbers_handler,
        "📢 قناة المطور": developer_channel_handler,
        "🆘 الدعم الفني": support_handler,
        "✉️ إرسال رسالة للمطور": contact_dev_prompt,
        "➕ إضافة يدوية": add_manual_prompt_v2,
        "🗑️ حذف الأرقام": clear_numbers,
        "📊 حالة البوت": status_handler,
        "📢 إرسال للكل": broadcast_prompt,
        "👥 المستخدمون": users_handler,
        "📱 الأرقام المتوفرة": my_numbers,
        "📋 آخر الأحداث": events_handler,
        "⛔ إيقاف البوت": stop_handler,
        "▶️ تشغيل البوت": start_handler,
        "📲 إرسال لواتساب": send_summary_wa,
        "🧹 تنظيف اللوجات": clean_logs,
        "📂 تحميل لوجات": download_logs,
        "🔎 فحص الاتصال": check_connection,
        "🛠️ لوحة المطور": developer_panel_handler_v2,
    }
    handler = text_map.get(text)
    if handler:
        _safe_handler_call(handler, message, f"text={text[:60]}")


def _dispatch_callback_query(call):
    data = str(getattr(call, "data", "") or "")
    if not data:
        return

    exact_map = {
        "demo_home": demo_home_callback,
        "check_sub": check_sub_callback,
        "contact_dev": contact_dev_callback,
        "num_change": number_change_callback,
        "num_check": number_check_callback,
        "num_back_countries": number_back_countries_callback,
        "num_back": number_back_callback,
        "dev_sections": dev_sections_callback,
        "dev_sub_status": dev_sub_status_callback,
        "dev_paid_summary": dev_paid_summary_callback,
        "dev_channel_info": dev_channel_info_callback,
        "dev_fetch_site": dev_fetch_site_callback,
        "dev_edit_welcome": dev_edit_welcome_callback,
        "dev_show_commands": dev_show_commands_callback,
        "dev_export_all_txt": dev_export_all_txt_callback,
        "dev_delete_platforms": dev_delete_platforms_callback,
        "dev_delete_platform_back": dev_delete_platform_back_callback,
        "dev_cookie_center": dev_cookie_center_callback,
        "dev_cookie_show": dev_cookie_show_callback,
        "dev_cookie_set": dev_cookie_set_callback,
        "dev_cookie_add": dev_cookie_add_callback,
        "dev_cookie_delete": dev_cookie_delete_callback,
        "dev_cookie_clear": dev_cookie_clear_callback,
        "dev_cookie_back": dev_cookie_back_callback,
        "dev_site_platforms": dev_site_platforms_callback,
        "dev_site_codes": dev_site_codes_callback,
        "dev_db_audit": dev_db_audit_callback,
        "siteadd_back_countries": siteadd_back_countries_callback,
        "siteadd_back": siteadd_back_callback,
        "siteadd_refresh": siteadd_refresh_callback,
    }
    handler = exact_map.get(data)
    if handler:
        _safe_handler_call(handler, call, f"callback={data[:80]}", is_callback=True)
        return

    prefix_map = [
        ("ctry_", demo_country_callback),
        ("svc_", demo_service_callback),
        ("sec_", dev_section_numbers_callback),
        ("plt_", platform_callback),
        ("admplt_", admin_platform_callback),
        ("num_country_page_", country_page_callback),
        ("num_country_", platform_country_callback),
        ("txtplt2_", txt_platform_selected_v2),
        ("txtplt_", txt_platform_selected),
        ("dev_delcfm_", dev_delete_platform_confirm_callback),
        ("dev_delpl_", dev_delete_platform_pick_callback),
        ("siteaddcty_", siteadd_country_callback),
        ("siteaddpage_", siteadd_page_callback),
        ("siteaddplt_", siteadd_platform_callback),
        ("siteaddnum_", siteadd_number_callback),
    ]
    for prefix, handler in prefix_map:
        if data.startswith(prefix):
            _safe_handler_call(handler, call, f"callback={data[:80]}", is_callback=True)
            return

    try:
        bot.answer_callback_query(call.id, "⚠️ الأمر غير معروف أو انتهت صلاحيته.", show_alert=True)
    except Exception:
        pass


def _register_runtime_handlers_once():
    global _handlers_registered
    with _handlers_register_lock:
        if _handlers_registered:
            return
        bot.register_message_handler(_dispatch_text_message, content_types=["text"])
        bot.register_message_handler(handle_txt_file, content_types=["document"])
        bot.register_callback_query_handler(_dispatch_callback_query, func=lambda call: True)
        _handlers_registered = True
        logger.info("✅ تم تسجيل معالجات الرسائل والأزرار والكولباك بنجاح")


def _register_visible_bot_commands():
    try:
        commands = [
            types.BotCommand("start", "فتح البوت أو لوحة الإدارة"),
            types.BotCommand("cookies", "مركز إدارة الكوكيز"),
            types.BotCommand("setcookies", "استبدال كل Runtime cookies"),
            types.BotCommand("addcookies", "إضافة أو دمج كوكيز جديدة"),
            types.BotCommand("delcookies", "حذف كوكيز محددة"),
            types.BotCommand("showcookies", "عرض الكوكيز الحالية"),
            types.BotCommand("clearcookies", "حذف كل runtime cookies"),
            types.BotCommand("dbaudit", "تدقيق قاعدة الأرقام"),
            types.BotCommand("confirm", "تأكيد حذف رقم من الانتظار"),
            types.BotCommand("deleteplatform", "حذف كل أرقام منصة"),
            types.BotCommand("delplatform", "اختصار deleteplatform"),
        ]
        bot.set_my_commands(commands)
        logger.info(f"✅ تم تسجيل {len(commands)} أمر ظاهر في قائمة أوامر البوت")
    except Exception as cmd_err:
        logger.warning(f"تعذر تسجيل أوامر البوت: {cmd_err}")

def _fetch_numbers_from_sms_ranges(session: requests.Session) -> List[Dict]:
    """نسخة آمنة: تحدّ من عدد الرينجات والزمن الكلي حتى لا يثقل البوت."""
    collected: List[Dict] = []
    started_at = time.time()
    try:
        session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{SITE_URL}/portal/sms/received",
        })
        page_resp = session.get(f"{SITE_URL}/portal/sms/received", timeout=15)
        csrf = _extract_csrf_token(getattr(page_resp, "text", ""))
        if not csrf:
            return collected

        today = datetime.date.today()
        for days in (7, 30, 90):
            if time.time() - started_at > SITE_SYNC_MAX_SECONDS:
                logger.warning(
                    f"SMS range sync stopped بسبب تجاوز المهلة الكلية ({SITE_SYNC_MAX_SECONDS}s)"
                )
                break

            start = today - datetime.timedelta(days=days)
            end = today
            summary_resp = session.post(
                f"{SITE_URL}/portal/sms/received/getsms",
                data={"from": start.isoformat(), "to": end.isoformat(), "_token": csrf},
                timeout=18,
            )
            if summary_resp.status_code != 200:
                continue

            ranges = list(dict.fromkeys(_extract_ranges_from_summary(summary_resp.text) or []))
            if not ranges:
                continue

            if SITE_SYNC_MAX_RANGES:
                ranges = ranges[:SITE_SYNC_MAX_RANGES]

            for idx, range_name in enumerate(ranges, start=1):
                if time.time() - started_at > SITE_SYNC_MAX_SECONDS:
                    logger.warning(
                        f"SMS range sync stopped أثناء المعالجة بعد {idx - 1} رينج بسبب المهلة الكلية"
                    )
                    return _dedupe_numbers(collected)

                platform = _guess_platform_from_payload(range_name) or _normalize_platform(range_name)
                if not platform:
                    continue

                try:
                    range_resp = session.post(
                        f"{SITE_URL}/portal/sms/received/getsms/number",
                        data={
                            "_token": csrf,
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "range": range_name,
                        },
                        timeout=18,
                    )
                except Exception as range_err:
                    logger.warning(f"Range fetch failed for {range_name}: {range_err}")
                    continue

                if range_resp.status_code != 200:
                    continue

                for number in _extract_number_rows(range_resp.text):
                    collected.append({
                        "number": number,
                        "platform": platform,
                        "site_section": str(range_name).strip(),
                        "source": "sms_range",
                        "added_at": time.ctime(),
                    })

            if collected:
                break
    except Exception as sms_range_err:
        logger.warning(f"SMS range sync error (stability hotfix): {sms_range_err}")
    return _dedupe_numbers(collected)

def _notify_code_to_channel(number: str, platform: str, code: str, country_info: Optional[Dict] = None, received_at: str = "", sms_text: str = ""):
    """ينشر Metadata غير حساسة فقط داخل القناة."""
    number = _normalize_number(number)
    code = str(code or "").strip()
    if not number or not code or code == "غير متوفر":
        return
    _limit_sent_codes_cache()
    cache_key = f"channel::{number}::{code}"
    if cache_key in sent_codes_cache:
        return
    info = country_info or _get_country_info(number)
    masked = _mask_number(number)
    time_label = str(received_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
    text = (
        "🔔 <b>تحديث جديد داخل البوت</b>\n\n"
        f"🌍 الدولة: {html.escape(str(info.get('flag', '🌐') or '🌐'))} {html.escape(str(info.get('name', 'غير محددة') or 'غير محددة'))}\n"
        f"📱 الرقم: <code>{html.escape(str(masked or ''))}</code>\n"
        f"💻 المنصة: <b>{html.escape(str(_display_platform_name(platform) or GENERAL_PLATFORM_NAME))}</b>\n"
        f"🕐 الوقت: {html.escape(str(time_label))}\n\n"
        "🔒 تم إخفاء الكود ومحتوى الرسالة حفاظاً على الخصوصية."
    )
    try:
        bot.send_message(
            CHANNEL_ID,
            text,
            parse_mode="HTML",
            reply_markup=_build_channel_post_markup(),
        )
        sent_codes_cache.add(cache_key)
    except Exception as notify_err:
        logger.warning(f"تعذّر إرسال metadata للقناة: {notify_err}")


def _extract_platforms_from_html_loose(page_html: str) -> List[str]:
    found = []
    patterns = [
        r'(?:data-service|data-platform|data-name|data-range|data-section)=["\']([^"\']+)["\']',
        r'"(?:service|platform|range|section)"\s*:\s*"([^"]+)"',
        r'>([^<>]{3,40})<',
    ]
    for pattern in patterns:
        for match in re.findall(pattern, page_html or '', flags=re.IGNORECASE):
            candidate = _platform_label_loose(html.unescape(match))
            if candidate and candidate not in found:
                found.append(candidate)
    return found


def _scan_site_platforms_live() -> Dict:
    data = {'platforms': [], 'sources': {}, 'counts': {}}
    allowed = [GENERAL_PLATFORM_NAME]
    counts = {}
    for item in numbers_db.get('numbers', []):
        plat = _clean_platform_name(item.get('platform', ''))
        if plat and plat != 'General':
            counts[plat] = counts.get(plat, 0) + 1
    for platform in allowed:
        data['platforms'].append(platform)
        data['sources'][platform] = ['whitelist']
    data['counts'] = counts
    return data


def _coerce_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    text_value = str(value).strip().lower()
    return text_value in {"1", "true", "yes", "y", "on", "available", "active", "ready", "online", "ok", "in_stock", "in-stock"}


def _rows_from_csv_text(csv_text: str) -> List[Dict[str, Any]]:
    csv_text = str(csv_text or "").strip()
    if not csv_text:
        return []
    reader = csv.DictReader(csv_text.splitlines())
    return [dict(row) for row in reader if isinstance(row, dict)]


def _extract_authorized_rows(payload: Any) -> List[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("numbers", "items", "data", "results", "rows", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _extract_authorized_rows(value)
                if nested:
                    return nested
    return []


def _authorized_source_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json, text/csv;q=0.9, text/plain;q=0.8"}
    if AUTHORIZED_SOURCE_TOKEN:
        headers["Authorization"] = f"Bearer {AUTHORIZED_SOURCE_TOKEN}"
        headers["X-API-Key"] = AUTHORIZED_SOURCE_TOKEN
    return headers


def _fetch_authorized_source_payload() -> Tuple[Any, str]:
    if AUTHORIZED_SOURCE_URL:
        last_error: Optional[Exception] = None
        for attempt in range(1, AUTHORIZED_SOURCE_RETRIES + 1):
            try:
                response = requests.get(
                    AUTHORIZED_SOURCE_URL,
                    headers=_authorized_source_headers(),
                    timeout=AUTHORIZED_SOURCE_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                content_type = (response.headers.get("content-type", "") or "").lower()
                if "csv" in content_type or AUTHORIZED_SOURCE_URL.lower().endswith(".csv"):
                    return _rows_from_csv_text(response.text), "authorized_url_csv"
                return response.json(), "authorized_url_json"
            except ValueError:
                return _rows_from_csv_text(response.text), "authorized_url_csv"
            except Exception as fetch_err:
                last_error = fetch_err
                logger.warning(f"فشل جلب المصدر المصرّح بالمحاولة {attempt}/{AUTHORIZED_SOURCE_RETRIES}: {fetch_err}")
                if attempt < AUTHORIZED_SOURCE_RETRIES:
                    time.sleep(min(10, attempt * 2))
        raise RuntimeError(f"تعذر جلب المصدر المصرّح عبر الرابط: {last_error}")

    if AUTHORIZED_SOURCE_FILE:
        source_path = Path(AUTHORIZED_SOURCE_FILE).expanduser()
        if not source_path.exists():
            raise FileNotFoundError(f"ملف المصدر غير موجود: {source_path}")
        content = source_path.read_text(encoding="utf-8")
        if source_path.suffix.lower() == ".csv":
            return _rows_from_csv_text(content), "authorized_file_csv"
        return json.loads(content), "authorized_file_json"

    raise RuntimeError("لم يتم ضبط AUTHORIZED_SOURCE_URL أو AUTHORIZED_SOURCE_FILE")


def _country_filter_tokens(info: Dict[str, Any]) -> set:
    return {
        str(info.get("key") or "").strip().lower(),
        str(info.get("digits_code") or "").strip().lower(),
        str(info.get("code") or "").strip().lower(),
        str(info.get("name") or "").strip().lower(),
    }


def _country_allowed(info: Dict[str, Any]) -> bool:
    if not SYNC_ALLOWED_COUNTRIES:
        return True
    allowed = {item.strip().lower() for item in SYNC_ALLOWED_COUNTRIES if item.strip()}
    return bool(_country_filter_tokens(info) & allowed)


def _is_number_structurally_valid(number: str) -> bool:
    normalized = _normalize_number(number)
    if not normalized.startswith("+") or len(re.sub(r"\D", "", normalized)) < 8:
        return False
    try:
        import phonenumbers
        parsed = phonenumbers.parse(normalized, None)
        if not phonenumbers.is_possible_number(parsed):
            return False
        if STRICT_E164_VALIDATION and not phonenumbers.is_valid_number(parsed):
            return False
        return True
    except Exception:
        return bool(re.fullmatch(r"\+\d{8,15}", normalized))


def _row_marked_available(raw_row: Dict[str, Any]) -> bool:
    if not REQUIRE_AVAILABLE_STATUS:
        return True
    if any(key in raw_row for key in ("available", "is_available", "availability", "enabled", "active")):
        for key in ("available", "is_available", "availability", "enabled", "active"):
            if key in raw_row:
                return _coerce_truthy(raw_row.get(key))
    status_value = str(raw_row.get("status") or raw_row.get("state") or raw_row.get("stock_status") or "").strip().lower()
    if not status_value:
        return False
    if status_value in {"available", "active", "ready", "online", "ok", "in_stock", "in-stock"}:
        return True
    if status_value in {"busy", "inactive", "sold", "offline", "unavailable", "blocked", "used"}:
        return False
    return False


def _normalize_authorized_source_rows(raw_items: List[Any], source_label: str) -> Dict[str, Any]:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    prepared: List[Dict[str, Any]] = []
    rejected_reasons: Dict[str, int] = {}

    def reject(reason: str) -> None:
        rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1

    for raw in raw_items or []:
        if isinstance(raw, str):
            raw_row = {"number": raw, "platform": "General", "available": True}
        elif isinstance(raw, dict):
            raw_row = dict(raw)
        else:
            reject("unsupported_row_type")
            continue

        number = raw_row.get("number") or raw_row.get("phone") or raw_row.get("msisdn") or raw_row.get("mobile") or raw_row.get("full_number") or ""
        platform = raw_row.get("platform") or raw_row.get("service") or raw_row.get("category") or raw_row.get("product") or "General"

        if not number:
            reject("missing_number")
            continue

        if not _row_marked_available(raw_row):
            reject("not_available")
            continue

        normalized_number = _normalize_number(str(number))
        if not _is_number_structurally_valid(normalized_number):
            reject("invalid_e164")
            continue

        item = {
            "number": normalized_number,
            "platform": _normalize_platform(str(platform or "General")),
            "site_section": str(raw_row.get("site_section") or raw_row.get("service") or platform or "General").strip() or "General",
            "source": source_label,
            "added_at": str(raw_row.get("added_at") or timestamp),
            "status": str(raw_row.get("status") or "available"),
            "availability": True,
            "last_checked_at": str(raw_row.get("last_checked_at") or raw_row.get("updated_at") or timestamp),
            "provider_reference": str(raw_row.get("id") or raw_row.get("uuid") or raw_row.get("external_id") or "").strip(),
        }
        item = _enrich_number_item(item)
        if not item:
            reject("normalize_failed")
            continue

        country_info = _get_country_info(item["number"])
        if not _country_allowed(country_info):
            reject("country_filtered")
            continue

        prepared.append(item)

    deduped = _dedupe_numbers(prepared)
    by_country: Dict[str, List[Dict[str, Any]]] = {}
    for item in deduped:
        by_country.setdefault(item.get("country_key") or "unknown", []).append(item)

    accepted: List[Dict[str, Any]] = []
    below_minimum: Dict[str, int] = {}
    countries_summary: Dict[str, int] = {}
    for country_key, items in sorted(by_country.items()):
        count = len(items)
        if count < MIN_NUMBERS_PER_COUNTRY and not KEEP_BELOW_MIN_COUNTRIES:
            below_minimum[country_key] = count
            reject("below_country_minimum")
            continue
        accepted.extend(items)
        countries_summary[country_key] = count

    saved_count = len(accepted)
    valid_count = len(deduped)
    total_received = len(raw_items or [])
    rejected_count = max(0, total_received - saved_count)
    success_rate = round((saved_count / total_received) * 100, 2) if total_received else 0.0

    return {
        "ok": saved_count > 0,
        "items": accepted,
        "source_label": source_label,
        "created_at": timestamp,
        "total_received": total_received,
        "valid_count": valid_count,
        "saved_count": saved_count,
        "rejected_count": rejected_count,
        "success_rate": success_rate,
        "countries_summary": countries_summary,
        "below_minimum_countries": below_minimum,
        "rejected_reasons": rejected_reasons,
        "min_numbers_per_country": MIN_NUMBERS_PER_COUNTRY,
    }


def _sync_authorized_numbers(notify_users: bool = True) -> Dict[str, Any]:
    before_items = list(numbers_db.get("numbers", []))
    try:
        payload, source_label = _fetch_authorized_source_payload()
        raw_items = _extract_authorized_rows(payload)
        report = _normalize_authorized_source_rows(raw_items, source_label)
        if report["saved_count"] <= 0:
            report["ok"] = False
            _write_sync_report(report)
            log_event("AUTHORIZED_NUMBERS_SYNC_EMPTY", {
                "received": report.get("total_received", 0),
                "rejected": report.get("rejected_count", 0),
            })
            return report

        unique = _store_numbers_snapshot(report["items"], source_label=source_label, metrics=report)
        report["saved_count"] = len(unique)
        report["ok"] = len(unique) > 0
        added_items = _find_newly_added_numbers(before_items, unique)
        log_event(
            "AUTHORIZED_NUMBERS_SYNCED",
            {
                "count": len(unique),
                "new": len(added_items),
                "source": source_label,
                "success_rate": report.get("success_rate", 0),
            },
        )
        if notify_users and added_items:
            _notify_users_about_new_numbers(added_items, source="sync")
        return report
    except Exception as sync_err:
        error_report = {
            "ok": False,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_label": "authorized_error",
            "total_received": 0,
            "valid_count": 0,
            "saved_count": 0,
            "rejected_count": 0,
            "success_rate": 0.0,
            "error": str(sync_err),
        }
        _write_sync_report(error_report)
        log_event("AUTHORIZED_NUMBERS_SYNC_FAILED", {"error": str(sync_err)[:300]})
        logger.exception(f"فشل مزامنة الأرقام من المصدر المصرّح: {sync_err}")
        return error_report


def fetch_numbers_smart(notify_users: bool = True) -> Tuple[bool, int]:
    preferred_source = (NUMBERS_SYNC_SOURCE or "site").strip().lower()
    if preferred_source in {"authorized", "official", "provider"}:
        if AUTHORIZED_SOURCE_URL or AUTHORIZED_SOURCE_FILE:
            report = _sync_authorized_numbers(notify_users=notify_users)
            if bool(report.get("ok")) or int(report.get("saved_count") or 0) > 0:
                return bool(report.get("ok")), int(report.get("saved_count") or 0)
            logger.warning("Authorized sync رجّع نتيجة فارغة، سيتم التحويل تلقائياً لجلب الأرقام من الموقع.")
        else:
            logger.info("لم يتم ضبط Authorized source، سيتم استخدام جلب الأرقام المباشر من الموقع تلقائياً.")
    return _legacy_fetch_numbers_smart(notify_users=notify_users)


def _legacy_fetch_numbers_smart(notify_users: bool = True) -> Tuple[bool, int]:
    """
    يجمع الأرقام من:
    1. Portal DataTable الخاصة بالحساب
    2. SMS Ranges للحفاظ على القسم/المنصة الفعلية المختارة من الموقع
    3. API endpoints رسمية (كحل احتياطي)
    4. سحب ذكي من صفحات الحساب
    يرجع (نجاح, عدد_الأرقام)
    """
    global dynamic_platforms
    before_items = list(numbers_db.get("numbers", []))
    new_numbers = []

    session = _build_site_session()
    headers = {
        "Accept":       "application/json",
        "Content-Type": "application/json",
    }

    portal_numbers = _fetch_numbers_from_portal(session)
    if portal_numbers:
        new_numbers.extend(portal_numbers)
        logger.info(f"✅ Portal: {len(portal_numbers)} رقم من صفحة My Numbers")

    sms_range_numbers = _fetch_numbers_from_sms_ranges(session)
    if sms_range_numbers:
        new_numbers.extend(sms_range_numbers)
        logger.info(f"✅ SMS ranges: {len(sms_range_numbers)} رقم مع المنصات الأصلية")

    api_endpoints = [
        f"{SITE_URL}/api/v1/numbers",
        f"{SITE_URL}/api/numbers",
        f"{SITE_URL}/api/v1/phone-numbers",
        f"{SITE_URL}/api/v1/active-numbers",
        f"{SITE_URL}/api/v2/numbers",
        f"{SITE_URL}/api/services/numbers",
    ]

    for ep in api_endpoints:
        try:
            resp = session.get(ep, headers=headers, timeout=10)
            logger.info(f"API {ep} → {resp.status_code}")
            if resp.status_code != 200:
                continue
            data = resp.json()
            raw = (
                data.get("numbers")
                or data.get("data")
                or data.get("phone_numbers")
                or data.get("items")
                or []
            )
            if not raw:
                continue
            batch = []
            for item in raw:
                if isinstance(item, dict):
                    batch.append({
                        "number": item.get("number") or item.get("phone") or "",
                        "platform": _guess_platform_from_payload(item.get("service"), item.get("platform"), item) or "General",
                        "site_section": str(item.get("service") or item.get("platform") or "").strip(),
                        "source": "api",
                        "added_at": time.ctime(),
                    })
                elif isinstance(item, str):
                    batch.append({
                        "number": item,
                        "platform": "General",
                        "source": "api",
                        "added_at": time.ctime(),
                    })
            if batch:
                new_numbers.extend(batch)
                logger.info(f"✅ API: {len(batch)} رقم من {ep}")
                break
        except Exception as e:
            logger.warning(f"API {ep}: {e}")

    scraped = _smart_scrape_homepage()
    scraped_platforms = [p for p in (_clean_platform_name(x) for x in scraped.get("platforms", [])) if p]
    scrape_platform = scraped_platforms[0] if len(set(scraped_platforms)) == 1 else "General"
    if scraped["numbers"]:
        for num in scraped["numbers"]:
            new_numbers.append({
                "number": num,
                "platform": scrape_platform,
                "site_section": scrape_platform if scrape_platform != "General" else "",
                "source": "scrape",
                "added_at": time.ctime(),
            })

    unique = _consolidate_number_sources(new_numbers)

    discovered_platforms = [
        _clean_platform_name(n.get("platform", "General"))
        for n in unique
        if n.get("platform")
    ] + [
        _clean_platform_name(p)
        for p in scraped["platforms"]
    ]
    discovered_platforms = [p for p in discovered_platforms if p]
    if discovered_platforms:
        _refresh_dynamic_platforms(discovered_platforms)
        logger.info(f"🔄 المنصات المحدّثة ({len(dynamic_platforms)}): {dynamic_platforms[:10]}…")

    if new_numbers:
        unique = _replace_numbers_db(unique)
        _refresh_dynamic_platforms(discovered_platforms)
        added_items = _find_newly_added_numbers(before_items, unique)
        log_event("NUMBERS_SYNCED", {
            "count":   len(unique),
            "new":     len(added_items),
            "deleted": max(0, len(before_items) - len(unique)),
        })
        logger.info(
            f"📦 [FETCH] الأرقام السابقة: {len(before_items)} | "
            f"الأرقام الجديدة المجلوبة: {len(unique)} | "
            f"أرقام جديدة فعلاً: {len(added_items)}"
        )
        if notify_users and added_items:
            _notify_users_about_new_numbers(added_items, source="sync")
        return True, len(unique)

    # ─── لم يُجلب أي رقم: تسجيل تحذير مفصّل ───
    logger.warning(
        "⚠️ [FETCH] لم يُجلب أي رقم من أي مصدر "
        "(Portal / SMS-Range / API / Scrape) | "
        f"الأرقام الموجودة مسبقاً: {len(before_items)}"
    )
    log_event("NUMBERS_FETCH_EMPTY", {"before": len(before_items)})
    return False, 0

LIVE_TEST_CODES_CACHE_TTL_SECONDS = max(2.0, float(str(_get("LIVE_TEST_CODES_CACHE_TTL_SECONDS", "5") or "5").strip() or "5"))
_live_test_codes_cache = {"ts": 0.0, "items": []}

def fetch_live_test_codes(force_refresh: bool = False):
    results = []
    now_ts = time.time()
    if not force_refresh:
        cached_items = list(_live_test_codes_cache.get("items") or [])
        cached_ts = float(_live_test_codes_cache.get("ts") or 0.0)
        if cached_items and (now_ts - cached_ts) < LIVE_TEST_CODES_CACHE_TTL_SECONDS:
            return [dict(item) for item in cached_items]
    try:
        session = _build_site_session()
        url = f"{SITE_URL}/portal/live/test-system/get"
        resp = session.post(url, timeout=20)
        if resp.status_code != 200:
            return results
        data = resp.json()
        rows = data.get('data', [])
        seen = set()
        for row in rows:
            number = _normalize_number(row.get('Number', ''))
            message = str(row.get('Msg', '') or '').strip()
            sender = _route_platform_for_site_row(row, fallback=row.get('Sender', '') or GENERAL_PLATFORM_NAME)
            country_info = _country_info_from_row(number, row)
            code_match = re.search(r'\b\d{4,8}\b', message)
            if not number or not code_match:
                continue
            item = {
                'code': code_match.group(0),
                'number': number,
                'service': sender,
                'country': country_info.get('name', 'غير محددة'),
                'country_name_ar': country_info.get('name', 'غير محددة'),
                'country_flag': country_info.get('flag', '🌐'),
                'country_code': country_info.get('code', ''),
                'message': message,
            }
            key = (item['number'], item['code'], item['service'])
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
        _live_test_codes_cache['items'] = [dict(item) for item in results]
        _live_test_codes_cache['ts'] = time.time()
    except Exception as e:
        logger.warning(f'fetch_live_test_codes error: {e}')
    return results

def _dev_fetch_from_site_and_report(chat_id: int):
    allowed, remaining = _site_fetch_guard_begin()
    if not allowed:
        try:
            bot.send_message(chat_id, f'⏳ توجد عملية جلب شغالة بالفعل. انتظر تقريباً {remaining} ثانية ثم جرّب مرة أخرى.')
        except Exception:
            pass
        return
    source_label = 'المصدر المصرّح' if NUMBERS_SYNC_SOURCE in {'authorized', 'official', 'provider'} else 'الموقع'
    try:
        bot.send_message(chat_id, f'⏳ جاري جلب الأرقام من {source_label}...')
        before_items = list(numbers_db.get('numbers', []))
        ok, cnt = fetch_numbers_smart(notify_users=False)
        current_items = list(numbers_db.get('numbers', []))
        added_items = _find_newly_added_numbers(before_items, current_items)
        if added_items:
            _notify_bot_users_about_site_fetch(added_items, source_label=f'جلب من {source_label}')
            _notify_channel_about_new_numbers(added_items, source_label=source_label)
        platforms_list = _platform_picker_platforms()
        if ok and cnt:
            lines = [
                f'✅ تم جلب/مزامنة {cnt} رقم من {source_label} بنجاح!',
                f'🆕 الأرقام الجديدة في هذه العملية: {len(added_items)}',
                '',
                '📊 تفاصيل المنصات:',
            ]
            for plat in platforms_list:
                nums = _numbers_for_platform(plat)
                icon = PLATFORM_BUTTON_ICONS.get(plat) or PLATFORM_BUTTON_ICONS.get(_normalize_platform(plat), '📂')
                lines.append(f'  {icon} {_display_platform_name(plat)}: {len(nums)} رقم')
            lines.append(f'\n🌐 إجمالي المنصات: {len(platforms_list)}')
            lines.append('👁️ كل المنصات ستظل ظاهرة حتى لو بعض المنصات لا تحتوي أرقام حالياً.')
            _chunked_send(chat_id, '\n'.join(lines))
        else:
            bot.send_message(
                chat_id,
                '⚠️ لم يتم جلب أرقام جديدة من الموقع.\n'
                'الأسباب المحتملة:\n'
                '• الكوكيز/التوكن منتهية الصلاحية\n'
                '• لا توجد أرقام جديدة في الحساب\n'
                '• مشكلة في الاتصال بالموقع\n\n'
                'استخدم ➕ إضافة رقم من قسم Test Numbers أو الإضافة اليدوية.'
            )
    except Exception as site_fetch_err:
        logger.exception(f'Site fetch report error: {site_fetch_err}')
        bot.send_message(chat_id, f'❌ خطأ أثناء جلب الأرقام: {site_fetch_err}')
    finally:
        _site_fetch_guard_end()


def auto_sync_loop():
    """
    ─────────────────────────────────────────────────────
    حلقة المزامنة التلقائية – محسَّنة
    • تعمل كل AUTO_SYNC_INTERVAL_MINUTES دقيقة (افتراضي 3)
    • تحذف الأرقام القديمة قبل كل جلب ناجح
    • تسجّل نتيجة كل دورة بالتفصيل
    • تعيد المحاولة فوراً إذا فشل الجلب (مع تأخير أقصر)
    ─────────────────────────────────────────────────────
    """
    if not AUTO_SYNC_NUMBERS:
        logger.info("⏸️ المزامنة التلقائية معطّلة (AUTO_SYNC_NUMBERS=False).")
        return

    interval_seconds = max(30, AUTO_SYNC_INTERVAL_MINUTES * 60)
    logger.info(
        f"✅ بدأت المزامنة التلقائية | كل {AUTO_SYNC_INTERVAL_MINUTES} دقيقة"
        f" | المصدر: {NUMBERS_SYNC_SOURCE}"
    )

    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 5

    while True:
        cycle_start = time.time()
        logger.info(f"🔄 [AUTO-SYNC] بدء دورة جلب الأرقام من {NUMBERS_SYNC_SOURCE}...")
        try:
            # ─── احذف الأرقام القديمة قبل الجلب (تُحدَّث في _replace_numbers_db) ───
            old_count = len(numbers_db.get("numbers", []))
            ok, cnt = fetch_numbers_smart(notify_users=True)
            elapsed = round(time.time() - cycle_start, 1)

            if ok and cnt > 0:
                consecutive_failures = 0
                logger.info(
                    f"✅ [AUTO-SYNC] نجح الجلب | {cnt} رقم | كان {old_count} | "
                    f"تم الاستبدال | {elapsed}ث"
                )
            else:
                consecutive_failures += 1
                logger.warning(
                    f"⚠️ [AUTO-SYNC] لم تُجلب أرقام جديدة | محاولة {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} | {elapsed}ث"
                )
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.error(
                        f"❌ [AUTO-SYNC] {MAX_CONSECUTIVE_FAILURES} فشل متتالي، إعادة بناء الجلسة عند الدورة القادمة"
                    )
                    consecutive_failures = 0

        except Exception as sync_err:
            consecutive_failures += 1
            logger.exception(f"❌ [AUTO-SYNC] استثناء في دورة المزامنة: {sync_err}")

        # ─── انتظار حتى الدورة القادمة ───
        time.sleep(interval_seconds)

_auto_sync_started = False
_auto_sync_lock = threading.Lock()

def _start_auto_sync_loop_once() -> None:
    global _auto_sync_started
    with _auto_sync_lock:
        if _auto_sync_started:
            return
        _auto_sync_started = True
    threading.Thread(target=auto_sync_loop, daemon=True, name="auto-sync-loop").start()

AUTO_CHANNEL_POST_ENABLED = _env_flag("AUTO_CHANNEL_POST_ENABLED", False)
AUTO_CHANNEL_POST_INTERVAL_MINUTES = max(3, int(_get("AUTO_CHANNEL_POST_INTERVAL_MINUTES", "3") or "3"))
_auto_channel_post_started = False

# يمكن تعطيل المهام التلقائية بالكامل من البيئة عند الحاجة فقط.
FORCE_DISABLE_AUTO_UPDATES = _env_flag("FORCE_DISABLE_AUTO_UPDATES", False)
if FORCE_DISABLE_AUTO_UPDATES:
    AUTO_SYNC_NUMBERS = False
    INITIAL_SYNC_ON_START = False
    AUTO_CHANNEL_POST_ENABLED = False
    TEST_MODE_ENABLED = False
    LIVE_TEST_CODES_MONITOR_ENABLED = False


def _build_auto_channel_post_text() -> str:
    messages = _build_test_mode_broadcast_messages(max_length=3500)
    return messages[0] if messages else _build_test_mode_message_text(_generate_test_mode_item())


def _post_auto_channel_message_once():
    for text_value in _build_test_mode_broadcast_messages(max_length=3500):
        bot.send_message(
            CHANNEL_ID,
            text_value,
            parse_mode='HTML',
            reply_markup=_build_channel_post_markup(),
        )
        time.sleep(0.35)


def _start_auto_channel_post_loop_once():
    global _auto_channel_post_started
    if _auto_channel_post_started:
        return
    if not AUTO_CHANNEL_POST_ENABLED:
        logger.info('⏸️ النشر التلقائي في القناة متوقف.')
        return
    _auto_channel_post_started = True
    interval_seconds = max(180, AUTO_CHANNEL_POST_INTERVAL_MINUTES * 60)

    def _loop():
        while True:
            try:
                _post_auto_channel_message_once()
                logger.info('✅ تم إرسال الرسالة التلقائية للقناة بواسطة البوت')
            except Exception as auto_channel_err:
                logger.warning(f'تعذر إرسال الرسالة التلقائية للقناة: {auto_channel_err}')
            time.sleep(interval_seconds)

    threading.Thread(target=_loop, daemon=True).start()
    logger.info(f'✅ تم تشغيل الرسالة التلقائية في القناة كل {AUTO_CHANNEL_POST_INTERVAL_MINUTES} دقيقة')

# AUTO_SYNC_NUMBERS controlled at top of file
AUTO_SYNC_INTERVAL_MINUTES = max(1, int(_get("AUTO_SYNC_INTERVAL_MINUTES", "3") or "3"))
# INITIAL_SYNC_ON_START controlled via environment

def _start_background_services() -> None:
    background_tasks = [
        ('HTTP server', _start_hosting_http_server_once),
        ('hosting heartbeat', _start_hosting_heartbeat_once),
        ('test mode publisher', _start_test_mode_publisher_once),
        ('general bootstrap', _bootstrap_general_bucket_once),
        ('live monitor', _start_live_test_codes_monitor_once),
        ('auto code watch', _start_auto_code_watch_loop_once),
        ('auto channel post', _start_auto_channel_post_loop_once),
    ]
    for label, starter in background_tasks:
        try:
            starter()
        except Exception as service_err:
            logger.warning(f'{label} warning: {service_err}')

def _maybe_run_initial_sync() -> int:
    current_count = len(numbers_db.get('numbers', []))
    if not INITIAL_SYNC_ON_START:
        return current_count
    try:
        logger.info('🚀 بدء مزامنة أولية عند التشغيل…')
        ok, current_count = fetch_numbers_smart(notify_users=False)
        logger.info(f"Initial sync: {'✅' if ok else '❌'} {current_count} رقم")
        return current_count
    except Exception as startup_sync_err:
        logger.exception(f'Initial sync failed: {startup_sync_err}')
        return len(numbers_db.get('numbers', []))

def _notify_admin_startup(restored_numbers_count: int, current_count: int) -> None:
    msg = (
        '🚀 *البوت انطلق!*\n'
        f'📦 الأرقام المحفوظة بعد المزامنة: {current_count}\n'
        f'🗄️ تم استرجاع {restored_numbers_count} رقم من التخزين الدائم\n'
        f'🔌 مصدر المزامنة: {NUMBERS_SYNC_SOURCE}\n'
        f'🎯 الحد الأدنى لكل دولة: {MIN_NUMBERS_PER_COUNTRY}\n'
        f"🌐 الأقسام المفعلة: {', '.join(_platform_picker_platforms())}\n"
        f"🔄 المزامنة التلقائية: {'مفعلة' if AUTO_SYNC_NUMBERS else 'متوقفة'} كل {AUTO_SYNC_INTERVAL_MINUTES} دقيقة\n"
        f"⏱ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    if not ADMIN_ID:
        return
    try:
        bot.send_message(ADMIN_ID, msg, parse_mode='Markdown')
    except Exception as notify_err:
        logger.warning(f'تعذر إرسال رسالة بدء التشغيل للمشرف: {notify_err}')

def _run_polling_forever() -> None:
    logger.info('✅ Polling supervisor started.')
    conflict_backoff = 30
    generic_backoff = 5
    while True:
        try:
            try:
                bot.remove_webhook()
            except Exception as webhook_err:
                logger.warning(f'Webhook cleanup before polling warning: {webhook_err}')
            logger.info('▶️ Starting Telegram long polling cycle')
            bot.infinity_polling(timeout=10, long_polling_timeout=20, skip_pending=True, allowed_updates=["message", "callback_query"])
            logger.warning('⚠️ infinity_polling returned without exception; restarting in 2s.')
            time.sleep(2)
        except Exception as poll_err:
            err_text = str(poll_err)
            if 'Error code: 409' in err_text or 'error code: 409' in err_text.lower():
                logger.error(
                    '❌ Telegram رفض getUpdates بسبب وجود نسخة أخرى تعمل بنفس التوكن. '
                    f'سيُعاد المحاولة تلقائياً بعد {conflict_backoff} ثانية.'
                )
                try:
                    bot.remove_webhook()
                except Exception as webhook_err:
                    logger.warning(f'Webhook cleanup after 409 failed: {webhook_err}')
                time.sleep(conflict_backoff)
                continue
            logger.exception(f'Polling crashed, retrying in {generic_backoff}s: {poll_err}')
            time.sleep(generic_backoff)


def main():
    _install_runtime_guardrails_once()
    _ensure_single_local_instance()
    _start_background_services()

    _register_runtime_handlers_once()
    _register_visible_bot_commands()
    _restore_wa_queue_from_disk()
    restored_numbers_count = _bootstrap_numbers_storage()
    _refresh_dynamic_platforms()
    _get_numbers_runtime_index()

    logger.info('=' * 60)
    logger.info('  Bot Pro v4 — Free Hosting Stable Start')
    logger.info('=' * 60)

    _start_wa_retry_worker_once()
    current_count = _maybe_run_initial_sync()
    _notify_admin_startup(restored_numbers_count, current_count)

    log_event('BOT_STARTED', {
        'numbers': current_count,
        'platforms': len(_platform_picker_platforms()),
        'auto_sync': AUTO_SYNC_NUMBERS,
        'sync_interval_minutes': AUTO_SYNC_INTERVAL_MINUTES,
    })

    try:
        bot.remove_webhook()
    except Exception as webhook_err:
        logger.warning(f'Webhook cleanup warning: {webhook_err}')

    if AUTO_SYNC_NUMBERS:
        logger.info('🔄 المزامنة التلقائية للأرقام مفعّلة.')
        _start_auto_sync_loop_once()
    else:
        logger.info('⏸️ المزامنة التلقائية للأرقام متوقفة.')

    _run_polling_forever()

def _supervise_main_forever() -> None:
    restart_delay = 5
    while True:
        try:
            main()
            logger.warning(f'main() exited unexpectedly; restarting in {restart_delay}s')
        except KeyboardInterrupt:
            logger.info('🛑 تم إيقاف البوت يدوياً من الطرفية.')
            break
        except Exception as fatal_err:
            logger.exception(f'Fatal top-level crash, restarting in {restart_delay}s: {fatal_err}')
        time.sleep(restart_delay)


if __name__ == '__main__':
    _supervise_main_forever()

