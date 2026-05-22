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
import json
import time
import atexit
import queue
import logging
import threading
import datetime
import requests
import urllib.parse
import html
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from telebot import TeleBot, types

# ══════════════════════════════════════════════
#  الإعدادات المدمجة مباشرةً في الملف
#  (يمكن تجاوزها بمتغيرات البيئة)
# ══════════════════════════════════════════════

def _env_required(name: str):
    value = os.getenv(name, "").strip()
    return value

# ─── قيم افتراضية مضمّنة ───────────────────
_DEFAULTS = {
    "BOT_TOKEN":   "8666549632:AAE3Yr5_HpcjBEEYlV2D-mv2kitpkORmOSg",
    "ADMIN_ID":    "7231690686",
    "SITE_URL":    "https://www.ivasms.com",
    "SITE_COOKIE": "eyJpdiI6IkpxUFpQbFhQMzNJeDlHV1hpbG05ZlE9PSIsInZhbHVlIjoiUW05ZCtGMUExTmtBUFNwR0ExV2tQOWVxc2NNQklXZTNxVm45cVRjcXM5emJvSUxrdW5uanRJMlduT0I5U3hqdmp1Y0hPMDVCNms3dkNVcG9Sa2pMS0F4RmFPUmg5blhkZXdCTGN0WHViMXVLeFBEbk83amNCYlFGWS80R0lMbGV5eGJLWDd2ZnNJOGlqb0pjWUhjbHFzS0VIeG5sSWlwd0UzTnI5aWdBMGkwZW1sN3Z6bUp3Q0RBUXFiWC9INFova2xERXpKeHllQUNTZ1FvQnN5ME5FeHlwN2lzNHhrQWRjK3BRbFUvck5sS2QzSHJRWUQ2MkQyY2NLVDdjLzlINFpMZ0VyaUVZenVIcjNaSWNVMFVkY2c9PSIsIm1hYyI6IjY4OWZiNGU1OTVkYWIwY2NlODcxYWY4NjY1MWQ2MWU0OWM1ZWRkMWJhMGJiZmQzYzY3NDNlZWY5Y2MxZTE2NmUiLCJ0YWciOiIifQ==",
    "SITE_COOKIE_FILE": "",
    "SITE_EMAIL":  "fareesaltmimii57@gmail.com",
    "SITE_PASS":   "Vr9bxG7R!mjrRZ",
}

# تم دمج ملف الكوكيز داخل نفس ملف البوت حتى يعمل بدون أي JSON خارجي.
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
        "value": "eyJpdiI6Ii9rcmhaem5KYmYwRm5TWkNjb2E4ckE9PSIsInZhbHVlIjoiaGxPakJFQU1HaWg4S05GNU5WS1ZoUHJiT0VVazhlMzJsM3hGN0N3cEZvTTh2QVFNSkJBbWNvampzMUJSU3U5Z0dJT1pZV0dUYnBBclA1SmNVWVBkTE5ieEN1TnNZTGxVSjgxenFQUkxLN0g2UWtWV0huQmFlM1k1KzBFQnZzSnYiLCJtYWMiOiIwY2JhYzgxNzE0YThhNzQyNDYxOGZmMDM5MDFjZGMzMzQ4NWJhY2I3ODM0N2ExN2U5MTBmNTdiNWUzYmQ4NjM1IiwidGFnIjoiIn0%3D",
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
        "value": "eyJpdiI6IkRZbDNmRnhwZDRqVnBFeENZMnN2N3c9PSIsInZhbHVlIjoiZ0FpVmtNeXBLbm56TG9jOWp4M2FHTXVBN1hCQTYyUnZFN2ZGQlEvM3YyWVpWYW94M1NaQ2hHK083UVorSFFlU0pFbFZ2V3B1aU1GeVUvZnZHdnBEckNPOHB1aFVISnJKY1ZmZWpSUWJHdlZ6dm9CMG9adWQrMGIrRFhjWlJQOC8iLCJtYWMiOiI2NGNlOTI5ZWVlNGVhZWVlNDYwMzk4OGIxNGI5M2E1ZDQwMjlmNDVlOWRhMDNmZTA5OWJkNTExODEzOGQ0Mjg0IiwidGFnIjoiIn0%3D",
        "origin": "https://www.ivasms.com",
    },
]

def _get(key: str, fallback: str = "") -> str:
    """يقرأ المتغير من البيئة أولاً، وإن لم يجده يرجع القيمة المدمجة."""
    return os.getenv(key, "").strip() or _DEFAULTS.get(key, fallback)

BOT_TOKEN        = _get("BOT_TOKEN")
ADMIN_ID         = int(_get("ADMIN_ID", "0") or "0")
SITE_URL         = _get("SITE_URL", "https://www.ivasms.com")
API_TOKEN        = _get("API_TOKEN", "")
SITE_COOKIE      = _get("SITE_COOKIE")
SITE_COOKIE_FILE = _get("SITE_COOKIE_FILE", "")
SITE_EMAIL       = _get("SITE_EMAIL")
SITE_PASS        = _get("SITE_PASS")

# واتساب (أساسي + احتياطي)
WA_NUMBER_1      = _get("WA_NUMBER_1", "")   # رقم أساسي
WA_APIKEY_1      = _get("WA_APIKEY_1", "")
WA_NUMBER_2      = _get("WA_NUMBER_2", "")   # رقم احتياطي
WA_APIKEY_2      = _get("WA_APIKEY_2", "")

SUPPORT_USERNAME = _get("SUPPORT_USERNAME", "@P_n_ij")

# ══════════════════════════════════════════════
#  المسارات والملفات
# ══════════════════════════════════════════════
BASE_DIR    = Path(__file__).parent
LOGS_DIR    = BASE_DIR / "logs"
DATA_DIR    = BASE_DIR / "data"
BACKUP_DIR  = BASE_DIR / "backups"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE    = DATA_DIR / "users.json"
NUMBERS_FILE  = DATA_DIR / "numbers.json"
EVENTS_FILE   = DATA_DIR / "events.json"
WA_QUEUE_FILE = DATA_DIR / "wa_queue.json"
BOT_LOCK_FILE = DATA_DIR / "bot.lock"
PAID_NUMBERS_FILE = DATA_DIR / "paid_numbers.json"

# ══════════════════════════════════════════════
#  ثوابت المطور
# ══════════════════════════════════════════════
DEVELOPER_USERNAME        = "P_n_ij"
DEVELOPER_CHANNEL         = "@fz_z_Z"
CHANNEL_ID                = -1002249882059
REQUIRED_CHANNEL_USERNAME = "fz_z_Z"

# ══════════════════════════════════════════════
#  إعداد نظام اللوجات (لوجات دوّارة متعددة)
# ══════════════════════════════════════════════
def setup_logging() -> logging.Logger:
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
    main_file_h.setLevel(logging.DEBUG)

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

    # --- تطبيق على الـ root logger ---
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(logging.DEBUG)
    root.addHandler(console_h)
    root.addHandler(main_file_h)
    root.addHandler(daily_h)
    root.addHandler(error_h)

    return logging.getLogger("BotPro")


logger = setup_logging()


def _cookie_host() -> str:
    return urllib.parse.urlparse(SITE_URL).hostname or "www.ivasms.com"



def _refresh_xsrf_header(session: requests.Session):
    xsrf = session.cookies.get("XSRF-TOKEN") or session.cookies.get("XSRF_TOKEN")
    if xsrf:
        session.headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf)



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



def _load_site_cookies(session: requests.Session) -> bool:
    if _load_cookie_items(session, EMBEDDED_SITE_COOKIES, "الكوكيز المدمجة داخل الملف"):
        return True
    return _load_cookies_from_json_file(session)



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


def _build_site_session() -> requests.Session:
    """يبني Session موحدة تدعم Bearer token أو cookie session للموقع مع محاولة auto-login."""
    session = requests.Session()
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
    })

    if API_TOKEN:
        session.headers["Authorization"] = f"Bearer {API_TOKEN}"

    loaded_from_file = _load_site_cookies(session)
    if not loaded_from_file:
        _apply_site_cookie(session, SITE_COOKIE or "")

    try:
        probe = session.get(f"{SITE_URL}/portal", timeout=12, allow_redirects=True)
        if _is_authenticated_response(probe):
            logger.info("✅ تم التحقق من جلسة الموقع بنجاح")
            return session
    except Exception as probe_err:
        logger.warning(f"Site probe warning: {probe_err}")

    if SITE_EMAIL and SITE_PASS:
        _login_site_with_credentials(session)

    return session

# ══════════════════════════════════════════════
#  مساعدات حفظ / تحميل JSON
# ══════════════════════════════════════════════
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
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
    except Exception as e:
        logger.error(f"save_json({path}): {e}")


# ══════════════════════════════════════════════
#  تحميل قواعد البيانات
# ══════════════════════════════════════════════
users_db        = load_json(USERS_FILE,        {"users": []})
numbers_db      = load_json(NUMBERS_FILE,      {"numbers": []})
events_db       = load_json(EVENTS_FILE,       {"events": []})
paid_numbers_db = load_json(PAID_NUMBERS_FILE, {"numbers": []})
wa_queue   = load_json(WA_QUEUE_FILE, {"pending": []})

# جلسات مؤقتة للمستخدمين داخل البوت
user_number_state: Dict[int, Dict] = {}
admin_pending_platform: Dict[int, str] = {}

# ══════════════════════════════════════════════
#  WhatsApp – إرسال مع Fallback + Queue
# ══════════════════════════════════════════════
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


# ══════════════════════════════════════════════
#  حفظ الأحداث (Event Logger)
# ══════════════════════════════════════════════
def log_event(event_type: str, details: dict):
    """يحفظ حدثاً في events.json ويضمن حد أقصى 500 حدث"""
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type":      event_type,
        **details,
    }
    events_db["events"].append(entry)
    if len(events_db["events"]) > 500:
        events_db["events"] = events_db["events"][-500:]
    save_json(EVENTS_FILE, events_db)
    logger.info(f"EVENT [{event_type}]: {details}")


def _normalize_number(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw)
    if cleaned.startswith("+"):
        cleaned = "+" + re.sub(r"\D", "", cleaned[1:])
    else:
        cleaned = re.sub(r"\D", "", cleaned)
    return cleaned


def _normalize_platform(value: str) -> str:
    cleaned = _clean_platform_name(value)
    if cleaned:
        return cleaned
    fallback = re.sub(r"\s+", " ", str(value or "").strip())
    return fallback or "General"


def _dedupe_numbers(items: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        number = _normalize_number(item.get("number", ""))
        platform = _normalize_platform(item.get("platform", "General"))
        if not number:
            continue
        key = (number, platform.lower())
        if key in seen:
            continue
        seen.add(key)
        row = dict(item)
        row["number"] = number
        row["platform"] = platform
        row.setdefault("source", "manual")
        row.setdefault("added_at", time.ctime())
        unique.append(row)
    return unique


def _replace_numbers_db(items: List[Dict]) -> List[Dict]:
    unique = _dedupe_numbers(items)
    numbers_db["numbers"] = unique
    save_json(NUMBERS_FILE, numbers_db)
    return unique


def _append_numbers(items: List[Dict]) -> List[Dict]:
    existing = numbers_db.get("numbers", []) if isinstance(numbers_db, dict) else []
    merged = _dedupe_numbers(existing + (items or []))
    numbers_db["numbers"] = merged
    save_json(NUMBERS_FILE, numbers_db)
    return merged


def _refresh_dynamic_platforms(extra_platforms: Optional[List[str]] = None):
    global dynamic_platforms
    collected = []
    for item in numbers_db.get("numbers", []):
        plat = _normalize_platform(item.get("platform", "General"))
        if plat:
            collected.append(plat)
    for plat in extra_platforms or []:
        norm = _normalize_platform(plat)
        if norm:
            collected.append(norm)
    dynamic_platforms = list(dict.fromkeys(collected + DEFAULT_PLATFORMS))


def _numbers_for_platform(platform: str) -> List[Dict]:
    target = _normalize_platform(platform).lower()
    rows = []
    for item in numbers_db.get("numbers", []):
        if _normalize_platform(item.get("platform", "General")).lower() == target:
            rows.append({
                "number": _normalize_number(item.get("number", "")),
                "platform": _normalize_platform(item.get("platform", "General")),
                "source": item.get("source", "manual"),
                "added_at": item.get("added_at", ""),
                "site_section": item.get("site_section", ""),
            })
    return _dedupe_numbers(rows)


SPECIAL_PLATFORMS = {"زخرفة", "تحميل TikTok", "تحميل Instagram"}
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
    "زخرفة": "🎨",
    "تحميل TikTok": "📥",
    "تحميل Instagram": "📥",
}


def _platform_button_label(platform: str, include_count: bool = True) -> str:
    platform = _normalize_platform(platform)
    icon = PLATFORM_BUTTON_ICONS.get(platform, "📂")
    if include_count and platform not in SPECIAL_PLATFORMS:
        return f"{icon} {platform} ({len(_numbers_for_platform(platform))})"
    return f"{icon} {platform}"


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
    entries = []
    pattern = re.compile(
        r"<tr>\s*<td><span class=\"cli-tag\">(.*?)</span></td>\s*<td><div class=\"msg-text\">(.*?)</div></td>\s*<td class=\"time-cell\">(.*?)</td>",
        re.IGNORECASE | re.DOTALL,
    )
    for sender, message, time_cell in pattern.findall(sms_html or ""):
        message_text = _strip_html_text(message)
        code_match = re.search(r"(?<!\d)(\d{4,8})(?!\d)", message_text)
        entries.append({
            "sender": _strip_html_text(sender),
            "message": message_text,
            "time": _strip_html_text(time_cell),
            "code": code_match.group(1) if code_match else "",
        })
    return entries


def _fetch_latest_sms_for_number(number: str, platform_hint: str = "") -> Optional[Dict]:
    target = _normalize_number(number).lstrip("+")
    if not target:
        return None

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
            return None

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
                    if candidate_digits == target:
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
                    })
                    return latest
    except Exception as sms_err:
        logger.warning(f"فشل فحص الكود للرقم {number}: {sms_err}")

    return None


# ══════════════════════════════════════════════
#  قائمة المنصات الافتراضية (تُدمج مع ما يُسحب)
# ══════════════════════════════════════════════
DEFAULT_PLATFORMS = [
    "WhatsApp", "Telegram", "TikTok", "Instagram",
    "Facebook", "Twitter", "Snapchat", "Line",
    "WeChat", "Viber", "Discord", "Gmail",
    "Hotmail", "Yahoo", "Microsoft", "Apple",
    "Amazon", "Netflix", "Uber", "PayPal",
    "زخرفة", "تحميل TikTok", "تحميل Instagram",
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

# قائمة المنصات الديناميكية (تُحدَّث من الموقع)
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


def _clean_platform_name(value: str) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    if not name:
        return ""

    alias_key = _platform_alias_key(name)
    if alias_key in PLATFORM_BLACKLIST:
        return ""

    if ("تحميل" in alias_key or "download" in alias_key) and any(token in alias_key for token in ("instagram", "insta", "انستا", "انست", "انستغرام", "انستقرام")):
        return "تحميل Instagram"
    if ("تحميل" in alias_key or "download" in alias_key) and any(token in alias_key for token in ("tiktok", "tik tok", "تيك توك", "تيكتوك")):
        return "تحميل TikTok"
    if any(token in alias_key for token in ("زخرف", "decor")):
        return "زخرفة"

    if alias_key in PLATFORM_CANONICAL_ALIASES:
        return PLATFORM_CANONICAL_ALIASES[alias_key]

    compact_key = alias_key.replace(" ", "")
    for alias, canonical in PLATFORM_CANONICAL_ALIASES.items():
        if compact_key == alias.replace(" ", ""):
            return canonical

    if len(name) < 2 or len(name) > 60:
        return ""
    if not re.search(r"[A-Za-z\u0600-\u06FF]", name):
        return ""

    cleaned = re.sub(r"[^\w\s\u0600-\u06FF()+.&@-]", " ", name, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_|")
    if not cleaned:
        return ""
    if re.search(r"[\u0600-\u06FF]", cleaned):
        return cleaned
    if re.search(r"[A-Z]", cleaned):
        return cleaned
    return cleaned.title()


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


# ══════════════════════════════════════════════
#  سحب المنصات والأرقام بذكاء من الموقع
# ══════════════════════════════════════════════
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

        result["numbers"] = list(dict.fromkeys(found_numbers))[:200]
        logger.info(
            f"📊 الصفحة: {len(result['platforms'])} منصة، "
            f"{len(result['numbers'])} رقم"
        )

    except ImportError:
        logger.error("❌ beautifulsoup4 غير مثبت! شغّل: pip install beautifulsoup4")
    except Exception as e:
        logger.error(f"_smart_scrape_homepage: {e}")

    return result


def _portal_numbers_datatable_params(length: int = 200) -> dict:
    return {
        "draw": "1",
        "start": "0",
        "length": str(length),
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
    collected = []
    endpoint = f"{SITE_URL}/portal/numbers"
    try:
        resp = session.get(
            endpoint,
            params=_portal_numbers_datatable_params(300),
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=20,
        )
        logger.info(f"Portal datatable {endpoint} → {resp.status_code}")
        if resp.status_code == 200 and "json" in (resp.headers.get("content-type", "").lower()):
            payload = resp.json()
            for item in payload.get("data", []):
                if not isinstance(item, dict):
                    continue
                number = str(item.get("Number") or item.get("number") or item.get("phone") or "").strip()
                platform = _guess_platform_from_payload(
                    item.get("range"),
                    item.get("platform"),
                    item.get("service"),
                    item.get("A2P"),
                    item,
                ) or "General"
                if not number:
                    continue
                collected.append({
                    "number": number,
                    "platform": platform,
                    "site_section": str(item.get("range") or item.get("platform") or item.get("service") or "").strip(),
                    "source": "portal_json",
                    "added_at": time.ctime(),
                })
    except Exception as portal_err:
        logger.warning(f"Portal datatable error: {portal_err}")
    return collected



def _fetch_numbers_from_sms_ranges(session: requests.Session) -> List[Dict]:
    collected = []
    try:
        session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{SITE_URL}/portal/sms/received",
        })
        page_resp = session.get(f"{SITE_URL}/portal/sms/received", timeout=20)
        csrf = _extract_csrf_token(getattr(page_resp, "text", ""))
        if not csrf:
            return collected

        today = datetime.date.today()
        for days in (7, 30, 90):
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
            if not ranges:
                continue

            for range_name in ranges:
                platform = _guess_platform_from_payload(range_name) or _normalize_platform(range_name)
                if not platform:
                    continue
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
        logger.warning(f"SMS range sync error: {sms_range_err}")
    return _dedupe_numbers(collected)


def _consolidate_number_sources(items: List[Dict]) -> List[Dict]:
    priority_order = {
        "sms_range": 4,
        "portal_json": 3,
        "api": 2,
        "manual": 2,
        "scrape": 1,
    }

    valid_items = []
    specific_numbers = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        number = _normalize_number(item.get("number", ""))
        platform = _normalize_platform(item.get("platform", "General")) or "General"
        if not number:
            continue
        row = dict(item)
        row["number"] = number
        row["platform"] = platform
        row.setdefault("source", "manual")
        row.setdefault("added_at", time.ctime())
        valid_items.append(row)
        if platform.lower() != "general":
            specific_numbers.add(number)

    valid_items.sort(
        key=lambda row: (
            1 if _normalize_platform(row.get("platform", "General")).lower() != "general" else 0,
            priority_order.get(str(row.get("source", "")).lower(), 0),
            len(_normalize_platform(row.get("platform", "General"))),
        ),
        reverse=True,
    )

    merged = []
    seen_pairs = set()
    for row in valid_items:
        number = row["number"]
        platform = _normalize_platform(row.get("platform", "General")) or "General"
        if platform.lower() == "general" and number in specific_numbers:
            continue
        key = (number, platform.lower())
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        row["platform"] = platform
        merged.append(row)

    return merged


def _number_item_key(item: Dict) -> Tuple[str, str]:
    number = _normalize_number(item.get("number", ""))
    platform = _normalize_platform(item.get("platform", "General")).lower()
    return number, platform


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


def _notify_users_about_new_numbers(new_items: List[Dict], source: str = "sync"):
    if not new_items:
        return
    summary = {}
    for item in new_items:
        platform = _normalize_platform(item.get("platform", "General")) or "General"
        summary[platform] = summary.get(platform, 0) + 1

    lines = [
        "📢 تم إضافة أرقام جديدة داخل البوت!",
        "",
        f"🆕 عدد الأرقام الجديدة: {len(new_items)}",
        f"🧭 المصدر: {'إضافة يدوية' if source == 'manual' else 'مزامنة تلقائية'}",
        "",
        "تفاصيل الأقسام:",
    ]
    for platform, count in sorted(summary.items()):
        lines.append(f"• {platform}: {count} رقم")
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


def fetch_numbers_smart(notify_users: bool = True) -> Tuple[bool, int]:
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
        _refresh_dynamic_platforms()
        added_items = _find_newly_added_numbers(before_items, unique)
        log_event("NUMBERS_SYNCED", {"count": len(unique), "new": len(added_items)})
        if notify_users and added_items:
            _notify_users_about_new_numbers(added_items, source="sync")
        return True, len(unique)

    return False, 0


def auto_sync_loop():
    """يجلب الأرقام تلقائياً كل 30 دقيقة"""
    while True:
        time.sleep(30 * 60)
        logger.info("🔄 مزامنة تلقائية للأرقام…")
        ok, cnt = fetch_numbers_smart()
        logger.info(f"Auto-sync: {'✅' if ok else '❌'} {cnt} رقم")


# ══════════════════════════════════════════════
#  بوت تيليجرام
# ══════════════════════════════════════════════

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set it in your hosting environment variables.")
if not ADMIN_ID:
    logger.warning("ADMIN_ID is not set. Admin-only commands will not work correctly until you set ADMIN_ID.")

bot        = TeleBot(BOT_TOKEN)
bot_active = True   # مفتاح تشغيل/إيقاف الاستجابة


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


# ══════════════════════════════════════════════
#  قاموس الدول الشامل (كود الاتصال → اسم + علم)
# ══════════════════════════════════════════════
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

def _get_country_info(number: str) -> dict:
    """يرجع dict يحتوي name و flag و code بناءً على رقم الهاتف."""
    num = _normalize_number(number)
    # ترتيب من الأطول للأقصر لضمان المطابقة الدقيقة
    for prefix, name, flag in sorted(COUNTRY_PHONE_MAP, key=lambda x: len(x[0]), reverse=True):
        clean = prefix.lstrip("+")
        if num.startswith(prefix) or num.startswith(clean):
            return {"name": name, "flag": flag, "code": prefix}
    return {"name": "غير محددة", "flag": "🌐", "code": ""}

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


def _platform_picker_platforms() -> List[str]:
    discovered = {
        _normalize_platform(item.get("platform", "General"))
        for item in numbers_db.get("numbers", [])
    }
    extras = sorted((set(dynamic_platforms) | discovered) - set(DEFAULT_PLATFORMS) - {""})
    ordered = []
    for platform in list(DEFAULT_PLATFORMS) + extras:
        normalized = _normalize_platform(platform)
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def _build_user_main_keyboard() -> types.ReplyKeyboardMarkup:
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("📱 الأقسام المتاحة", "💎 أرقام مدفوعة")
    mk.add("📥 تحميل فيديو", "🎨 زخرفة الاسم")
    mk.add("📢 قناة المطور", "🆘 الدعم الفني")
    mk.add("✉️ إرسال رسالة للمطور")
    return mk


def _build_developer_panel_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("📚 أقسام الموقع", callback_data="dev_sections"),
        types.InlineKeyboardButton("🔐 الاشتراك الإجباري", callback_data="dev_sub_status"),
    )
    mk.add(
        types.InlineKeyboardButton("💎 الأرقام المدفوعة", callback_data="dev_paid_summary"),
        types.InlineKeyboardButton("📢 قناة المطور", callback_data="dev_channel_info"),
    )
    return mk


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

# قائمة الدول مبنية ديناميكياً من COUNTRY_PHONE_MAP (80+ دولة)
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
    """يبني قاموس أسماء الدول للبحث من COUNTRY_PHONE_MAP."""
    names = {}
    for code, name, flag in COUNTRY_PHONE_MAP:
        key = code.lstrip("+").replace(" ", "_")
        names[key] = [name]
    return names

DEMO_COUNTRY_NAMES = _build_country_names_map()


def _service_counts() -> Dict[str, int]:
    counts: Dict[str, int] = {key: 0 for key in DEMO_SERVICE_META.keys()}
    for item in numbers_db.get("numbers", []):
        platform = _normalize_platform(item.get("platform", ""))
        if platform in counts:
            counts[platform] += 1
    return counts


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


def _send_demo_home(chat_id: int, message_id: Optional[int] = None):
    platforms = _platform_picker_platforms()
    non_empty = sum(1 for platform in platforms if _numbers_for_platform(platform))
    text = (
        "🌍 *أقسام الموقع المتاحة*\n\n"
        f"📚 إجمالي الأقسام: {len(platforms)}\n"
        f"✅ الأقسام اللي عليها أرقام: {non_empty}\n"
        f"📭 الأقسام بدون أرقام: {max(0, len(platforms) - non_empty)}\n\n"
        "يشمل ذلك أقسام الأرقام + أقسام *الزخرفة* و *تحميل TikTok* و *تحميل Instagram*.\n"
        "اضغط على أي قسم من الأزرار تحت، ولو القسم عليه أرقام هيفتح لك مباشرة."
    )
    _send_or_edit(
        chat_id,
        text,
        reply_markup=_build_platform_picker_markup(),
        message_id=message_id,
        parse_mode="Markdown",
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


@bot.callback_query_handler(func=lambda c: c.data == "demo_home")
def demo_home_callback(call):
    bot.answer_callback_query(call.id)
    _send_demo_home(call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def demo_service_callback(call):
    service = call.data[4:]
    if service not in DEMO_SERVICE_META:
        bot.answer_callback_query(call.id, "الخدمة غير متاحة", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _send_demo_countries(call.message.chat.id, service, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ctry_"))
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


# ── /start ──────────────────────────────────
@bot.message_handler(commands=["start"])
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
        bot.send_message(
            message.chat.id,
            (
                "👋 أهلاً بك\n\n"
                "تم تحميل أقسام الموقع الحالية لك مباشرة.\n"
                "اختَر أي قسم من تحت، ولو القسم عليه أرقام هتقدر تغيّر الرقم وتفحص آخر كود."
            ),
            reply_markup=_build_user_main_keyboard(),
        )
        _send_demo_home(message.chat.id)
        return

    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("🔄 مزامنة الأرقام", "➕ إضافة يدوية")
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
            "استخدم الأزرار أدناه."
        ),
        reply_markup=mk,
    )


# ── مزامنة الأرقام ──────────────────────────
@bot.message_handler(func=lambda m: m.text == "🔄 مزامنة الأرقام" and is_admin(m))
def sync_handler(message):
    bot.reply_to(
        message,
        "🛡️ وضع الأمان مفعّل.\n\n"
        "تم تعطيل مزامنة الأرقام وجلبها تلقائياً من داخل هذه النسخة.\n"
        "استخدم ➕ إضافة يدوية أو استيراد ملف TXT فقط.",
    )


# ── إضافة يدوية ─────────────────────────────
@bot.message_handler(func=lambda m: m.text == "➕ إضافة يدوية" and is_admin(m))
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


@bot.callback_query_handler(func=lambda c: c.data.startswith("admplt_"))
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
                platform_name = _normalize_platform(plat)
            else:
                num = line
                platform_name = _normalize_platform(selected_platform or "General")

            normalized_num = _normalize_number(num)
            if normalized_num:
                prepared.append({
                    "number": normalized_num,
                    "platform": platform_name,
                    "source": "manual",
                    "added_at": time.ctime(),
                })
        except Exception:
            continue

    if not prepared:
        bot.reply_to(message, "❌ ما لقيتش أرقام صالحة.\nلو هتبعت بدون `:المنصة` لازم تختار منصة الأول.")
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


# ── حذف الأرقام ─────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🗑️ حذف الأرقام" and is_admin(m))
def clear_numbers(message):
    count = len(numbers_db["numbers"])
    numbers_db["numbers"] = []
    save_json(NUMBERS_FILE, numbers_db)
    log_event("NUMBERS_CLEARED", {"deleted": count})
    bot.reply_to(message, f"🗑️ تم حذف {count} رقم.")


# ── حالة البوت ──────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📊 حالة البوت")
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
        f"📟 واتساب: {'✅ مفعّل' if wa_ok else '❌ غير مهيأ'}\n"
        f"📬 رسائل واتساب معلّقة: {pending}\n"
        f"⏱ وقت التشغيل: {uptime}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")


# ── إيقاف / تشغيل ───────────────────────────
@bot.message_handler(func=lambda m: m.text == "⛔ إيقاف البوت" and is_admin(m))
def stop_handler(message):
    global bot_active
    bot_active = False
    log_event("BOT_PAUSED", {"by": message.from_user.id})
    bot.reply_to(message, "⛔ *تم إيقاف البوت مؤقتاً.*", parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "▶️ تشغيل البوت" and is_admin(m))
def start_handler(message):
    global bot_active
    bot_active = True
    log_event("BOT_RESUMED", {"by": message.from_user.id})
    bot.reply_to(message, "▶️ *تم تشغيل البوت بنجاح!*", parse_mode="Markdown")


# ── إرسال للكل ──────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📢 إرسال للكل" and is_admin(m))
def broadcast_prompt(message):
    bot.reply_to(message, "📢 أرسل الرسالة للإذاعة:")
    bot.register_next_step_handler(message, _broadcast_exec)


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


# ── عدد المستخدمين ───────────────────────────
@bot.message_handler(func=lambda m: m.text == "👥 المستخدمون" and is_admin(m))
def users_handler(message):
    bot.reply_to(message, f"👥 المستخدمون المسجلون: *{len(users_db['users'])}*", parse_mode="Markdown")


# ── عرض الأرقام ─────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📱 الأرقام المتوفرة")
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


# ── آخر الأحداث ─────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📋 آخر الأحداث" and is_admin(m))
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


# ── إرسال ملخص لواتساب ──────────────────────
@bot.message_handler(func=lambda m: m.text == "📲 إرسال لواتساب" and is_admin(m))
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


# ── تنظيف اللوجات ───────────────────────────
@bot.message_handler(func=lambda m: m.text == "🧹 تنظيف اللوجات" and is_admin(m))
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


# ── تحميل آخر لوج ───────────────────────────
@bot.message_handler(func=lambda m: m.text == "📂 تحميل لوجات" and is_admin(m))
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


# ── فحص الاتصال ─────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🔎 فحص الاتصال" and is_admin(m))
def check_connection(message):
    try:
        r = requests.get(SITE_URL, timeout=8)
        site_ok = f"✅ {r.status_code}"
    except Exception as e:
        site_ok = f"❌ {e}"
    try:
        me = bot.get_me()
        tg_ok = f"✅ @{me.username}"
    except Exception as e:
        tg_ok = f"❌ {e}"
    text = (
        f"🔎 *فحص الاتصال:*\n"
        f"🌐 الموقع: {site_ok}\n"
        f"🤖 تيليجرام: {tg_ok}\n"
        f"📟 واتساب أساسي: {'✅' if WA_NUMBER_1 else '⚠️ غير مهيأ'}\n"
        f"📟 واتساب احتياطي: {'✅' if WA_NUMBER_2 else '⚠️ غير مهيأ'}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")


# ── طلب رقم (مستخدم عادي) ───────────────────
def _build_platform_picker_markup() -> types.InlineKeyboardMarkup:
    platforms = _platform_picker_platforms()
    mk = types.InlineKeyboardMarkup(row_width=2)
    for idx, platform in enumerate(platforms):
        mk.add(types.InlineKeyboardButton(_platform_button_label(platform), callback_data=f"plt_{idx}"))
    return mk


def _build_number_actions_markup() -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data="num_change"))
    mk.add(types.InlineKeyboardButton("🔍 فحص الكود", callback_data="num_check"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع للمنصات", callback_data="num_back"))
    return mk


def _open_special_platform_section(chat_id: int, platform: str, user_id: Optional[int] = None, message_id: Optional[int] = None) -> bool:
    platform = _normalize_platform(platform)
    if platform not in SPECIAL_PLATFORMS:
        return False

    if user_id is not None:
        user_number_state.pop(user_id, None)

    if platform == "زخرفة":
        if message_id:
            try:
                bot.edit_message_text("🎨 تم فتح قسم الزخرفة.", chat_id, message_id)
            except Exception:
                pass
        msg = bot.send_message(chat_id, "🎨 أرسل الاسم أو النص الذي تريد زخرفته الآن.")
        bot.register_next_step_handler(msg, _show_decorated_names)
        return True

    source_platform = "TikTok" if "TikTok" in platform else "Instagram"
    if message_id:
        try:
            bot.edit_message_text(f"📥 تم فتح قسم تحميل {source_platform}.", chat_id, message_id)
        except Exception:
            pass
    msg = bot.send_message(chat_id, f"🔗 أرسل رابط فيديو {source_platform} الآن.")
    bot.register_next_step_handler(msg, lambda m, src=source_platform: _process_video_download(m, src))
    return True


def _render_user_number_card(chat_id: int, user_id: int, message_id: Optional[int] = None):
    state = user_number_state.get(user_id) or {}
    platform = _normalize_platform(state.get("platform", ""))
    if not platform:
        text = "🌐 اختر القسم من الأقسام الموجودة في الموقع:"
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=_build_platform_picker_markup())
        else:
            bot.send_message(chat_id, text, reply_markup=_build_platform_picker_markup())
        return

    avail = _numbers_for_platform(platform)
    if not avail:
        state["platform"] = platform
        state["index"] = 0
        state.pop("number", None)
        user_number_state[user_id] = state
        text = (
            f"📂 *القسم:* {platform}\n\n"
            "📭 *هذا القسم لا يوجد عليه أرقام حالياً.*\n\n"
            "تقدر ترجع للمنصات أو تراسل المطور من الأزرار تحت."
        )
        mk = types.InlineKeyboardMarkup(row_width=1)
        mk.add(types.InlineKeyboardButton("↩️ رجوع للمنصات", callback_data="num_back"))
        mk.add(types.InlineKeyboardButton("✉️ إرسال رسالة للمطور", callback_data="contact_dev"))
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=mk)
        else:
            bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=mk)
        return

    index = int(state.get("index", 0)) % len(avail)
    state["index"] = index
    state["platform"] = platform
    state["number"] = avail[index]["number"]
    user_number_state[user_id] = state

    country_info = _get_country_info(avail[index]['number'])
    text = (
        f"📱 *القسم:* {platform}\n"
        f"🌍 *الدولة:* {country_info['flag']} {country_info['name']}\n"
        f"🔢 *الرقم الحالي:*\n`{avail[index]['number']}`\n\n"
        f"📦 *الترتيب:* {index + 1} من {len(avail)}\n"
        "استخدم الأزرار اللي تحت لتغيير الرقم أو فحص آخر كود."
    )

    if message_id:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode="Markdown",
            reply_markup=_build_number_actions_markup(),
        )
    else:
        bot.send_message(
            chat_id,
            text,
            parse_mode="Markdown",
            reply_markup=_build_number_actions_markup(),
        )


@bot.message_handler(func=lambda m: m.text == "🛒 طلب رقم")
def request_number(message):
    bot.reply_to(message, "⚠️ هذه الميزة غير مفعلة في النسخة الآمنة. يمكنك استعراض الأقسام المتاحة أو التواصل مع المطور.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("plt_"))
def platform_callback(call):
    platforms = _platform_picker_platforms()
    try:
        idx = int(call.data.split("_", 1)[1])
        platform = platforms[idx]
    except Exception:
        bot.answer_callback_query(call.id, "القسم غير صالح", show_alert=True)
        return
    if _open_special_platform_section(call.message.chat.id, platform, user_id=call.from_user.id, message_id=call.message.message_id):
        bot.answer_callback_query(call.id, f"تم فتح قسم {platform}")
        return
    user_number_state[call.from_user.id] = {"platform": platform, "index": 0}
    bot.answer_callback_query(call.id, f"تم فتح قسم {platform}")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "num_change")
def number_change_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    platform = _normalize_platform(state.get("platform", ""))
    if not platform:
        bot.answer_callback_query(call.id, "اختر القسم أولاً", show_alert=True)
        _send_demo_home(call.message.chat.id, message_id=call.message.message_id)
        return
    avail = _numbers_for_platform(platform)
    if not avail:
        bot.answer_callback_query(call.id, "هذا القسم لا يوجد عليه أرقام حالياً", show_alert=True)
        _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)
        return
    state["index"] = (int(state.get("index", 0)) + 1) % len(avail)
    user_number_state[call.from_user.id] = state
    bot.answer_callback_query(call.id, "✅ تم تغيير الرقم")
    _render_user_number_card(call.message.chat.id, call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "num_back")
def number_back_callback(call):
    user_number_state.pop(call.from_user.id, None)
    bot.answer_callback_query(call.id)
    _send_demo_home(call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "num_check")
def number_check_callback(call):
    state = user_number_state.get(call.from_user.id) or {}
    number = _normalize_number(state.get("number", ""))
    platform = _normalize_platform(state.get("platform", ""))
    if not number:
        bot.answer_callback_query(call.id, "اختر رقم أولاً", show_alert=True)
        return
    bot.answer_callback_query(call.id, "⏳ جاري فحص آخر كود...")
    data = _fetch_latest_sms_for_number(number, platform)
    if not data:
        bot.send_message(
            call.message.chat.id,
            f"🔍 نتيجة فحص الكود\n\nالقسم: {platform}\nالرقم: {number}\n\nلا يوجد كود جديد حالياً.",
        )
        return
    sms_text = (data.get("text") or data.get("message") or "").strip()
    code = str(data.get("code") or "").strip() or "غير متوفر"
    received_at = data.get("date") or data.get("created_at") or data.get("time") or "غير محدد"
    reply = (
        "🔍 نتيجة فحص الكود\n\n"
        f"القسم: {platform}\n"
        f"الرقم: {number}\n"
        f"الكود: {code}\n"
        f"الوقت: {received_at}"
    )
    if sms_text:
        reply += f"\n\nنص الرسالة:\n{sms_text[:1000]}"
    bot.send_message(call.message.chat.id, reply)


# ── الدعم الفني ──────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🆘 الدعم الفني")
def support_handler(message):
    bot.reply_to(message, f"🆘 للدعم الفني تواصل مع: {SUPPORT_USERNAME}")


@bot.message_handler(func=lambda m: m.text == "📱 الأقسام المتاحة")
def user_sections_handler(message):
    if not _require_subscription(message):
        return
    _send_demo_home(message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
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


@bot.message_handler(func=lambda m: m.text == "📢 قناة المطور")
def developer_channel_handler(message):
    if not _require_subscription(message):
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        f"📢 الانضمام إلى {DEVELOPER_CHANNEL}",
        url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME}",
    ))
    bot.send_message(message.chat.id, f"📢 قناة المطور الرسمية\n\nالقناة: {DEVELOPER_CHANNEL}\nالمطور: @{DEVELOPER_USERNAME}", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == "contact_dev")
def contact_dev_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✉️ أرسل رسالتك الآن ليتم تحويلها إلى المطور.")
    bot.register_next_step_handler(msg, _send_to_developer)


@bot.message_handler(func=lambda m: m.text in ("✉️ راسل المطور", "✉️ إرسال رسالة للمطور"))
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


@bot.message_handler(func=lambda m: m.text == "📥 تحميل فيديو")
def download_video_menu(message):
    if not _require_subscription(message):
        return
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🎵 TikTok", callback_data="dl_tiktok"),
        types.InlineKeyboardButton("📸 Instagram", callback_data="dl_instagram"),
    )
    bot.send_message(message.chat.id, "📥 اختر المنصة التي تريد التحميل منها:", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data in ("dl_tiktok", "dl_instagram"))
def download_platform_callback(call):
    platform = "TikTok" if call.data == "dl_tiktok" else "Instagram"
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"🔗 أرسل رابط فيديو {platform} الآن.")
    bot.register_next_step_handler(msg, lambda m: _process_video_download(m, platform))


def _process_video_download(message, platform: str):
    url_text = (message.text or "").strip()
    if not url_text.startswith("http"):
        bot.reply_to(message, "❌ الرابط غير صالح.")
        return
    wait_msg = bot.reply_to(message, f"⏳ جاري معالجة رابط {platform}...")
    try:
        api_url = f"https://api.vevioz.com/api/button/mp4?url={urllib.parse.quote(url_text)}"
        resp = requests.get(api_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        video_link = ""
        if resp.status_code == 200:
            try:
                data = resp.json()
                video_link = data.get("url") or data.get("link") or data.get("links", {}).get("mp4") or ""
            except Exception:
                video_link = ""
        if video_link:
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("⬇️ تحميل الفيديو", url=video_link))
            bot.edit_message_text(f"✅ تم تجهيز رابط تحميل فيديو {platform}.", message.chat.id, wait_msg.message_id, reply_markup=mk)
        else:
            bot.edit_message_text("⚠️ تعذر استخراج رابط التحميل مباشرة. جرّب لاحقاً أو استخدم أداة خارجية موثوقة.", message.chat.id, wait_msg.message_id)
    except Exception as e:
        try:
            bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة: {e}", message.chat.id, wait_msg.message_id)
        except Exception:
            bot.reply_to(message, f"❌ حدث خطأ: {e}")


ARABIC_DECORATIONS = [
    "★ {name} ★", "✿ {name} ✿", "꧁ {name} ꧂", "♛ {name} ♛", "𖣔 {name} 𖣔",
    "彡 {name} 彡", "『 {name} 』", "【 {name} 】", "❖ {name} ❖", "✧ {name} ✧",
    "♚ {name} ♚", "✪ {name} ✪", "⚡ {name} ⚡", "☬ {name} ☬", "ꕥ {name} ꕥ",
    "༺ {name} ༻", "♥ {name} ♥", "☾ {name} ☽", "➳ {name} ➳", "⌁ {name} ⌁",
    "𓆩 {name} 𓆪", "༒ {name} ༒", "⫷ {name} ⫸", "⋆ {name} ⋆", "⟦ {name} ⟧",
    "✰ {name} ✰", "𑁍 {name} 𑁍", "☀ {name} ☀", "☁ {name} ☁", "⚜ {name} ⚜",
]

ENGLISH_DECORATIONS = [
    "PRO {name}", "VIP {name}", "KING {name}", "QUEEN {name}", "MR {name}",
    "MS {name}", "THE {name}", "Xx {name} xX", "_ {name} _", "~ {name} ~",
    "[ {name} ]", "< {name} >", "( {name} )", "* {name} *", "+ {name} +",
    "# {name} #", "! {name} !", "$ {name} $", "% {name} %", "@ {name} @",
    "DEV {name}", "ELITE {name}", "LEGEND {name}", "GHOST {name}", "WOLF {name}",
    "LORD {name}", "NOVA {name}", "FIRE {name}", "ICE {name}", "SKY {name}",
]


@bot.message_handler(func=lambda m: m.text == "🎨 زخرفة الاسم")
def name_decoration_prompt(message):
    if not _require_subscription(message):
        return
    msg = bot.reply_to(message, "🎨 أرسل الاسم أو النص الذي تريد زخرفته.")
    bot.register_next_step_handler(msg, _show_decorated_names)


def _show_decorated_names(message):
    name = (message.text or "").strip()
    if not name:
        bot.reply_to(message, "❌ لم ترسل اسماً صالحاً.")
        return
    lines = ["🎨 30 اسم مزخرف عربي:\n"]
    for i, pattern in enumerate(ARABIC_DECORATIONS, 1):
        lines.append(f"{i:02d}- {pattern.format(name=name)}")
    lines.append("\n🔤 30 اسم مزخرف إنجليزي:\n")
    for i, pattern in enumerate(ENGLISH_DECORATIONS, 1):
        lines.append(f"{i:02d}- {pattern.format(name=name)}")
    _chunked_send(message.chat.id, "\n".join(lines))


@bot.message_handler(func=lambda m: m.text == "💎 أرقام مدفوعة")
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


@bot.message_handler(func=lambda m: m.text == "🛠️ لوحة المطور" and is_admin(m))
def developer_panel_handler(message):
    bot.send_message(message.chat.id, "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:", reply_markup=_build_developer_panel_markup())


@bot.callback_query_handler(func=lambda c: c.data == "dev_sections")
def dev_sections_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📚 أقسام الموقع الحالية:", reply_markup=_build_sections_markup())


@bot.callback_query_handler(func=lambda c: c.data.startswith("sec_"))
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


@bot.callback_query_handler(func=lambda c: c.data == "dev_sub_status")
def dev_sub_status_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"🔐 الاشتراك الإجباري: مفعّل\n📢 القناة: {DEVELOPER_CHANNEL}\n🆔 Channel ID: {CHANNEL_ID}")


@bot.callback_query_handler(func=lambda c: c.data == "dev_paid_summary")
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


@bot.callback_query_handler(func=lambda c: c.data == "dev_channel_info")
def dev_channel_info_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"👑 المطور: @{DEVELOPER_USERNAME}\n📢 القناة: {DEVELOPER_CHANNEL}\n🆔 Channel ID: {CHANNEL_ID}")


# ══════════════════════════════════════════════
#  uptime helper
# ══════════════════════════════════════════════
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
        if BOT_LOCK_FILE.exists():
            existing_pid = BOT_LOCK_FILE.read_text(encoding="utf-8").strip()
            if existing_pid.isdigit():
                try:
                    os.kill(int(existing_pid), 0)
                    raise RuntimeError(f"يوجد تشغيل محلي آخر للبوت بنفس الجهاز (PID: {existing_pid}).")
                except OSError:
                    BOT_LOCK_FILE.unlink(missing_ok=True)
            else:
                BOT_LOCK_FILE.unlink(missing_ok=True)
        BOT_LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(_release_bot_lock)
    except RuntimeError:
        raise
    except Exception as lock_err:
        logger.warning(f"تعذر إنشاء ملف القفل المحلي: {lock_err}")


# ══════════════════════════════════════════════
#  التشغيل الرئيسي
# ══════════════════════════════════════════════
def main():
    _ensure_single_local_instance()
    _restore_wa_queue_from_disk()

    logger.info("=" * 60)
    logger.info("  Bot Pro v3 — Starting…")
    logger.info("=" * 60)

    # بدء خيط إعادة إرسال واتساب في الخلفية
    t = threading.Thread(target=_wa_retry_worker, daemon=True)
    t.start()

    # ✅ [SAFE] جلب الأرقام التلقائي عند البدء معطّل
    ok, cnt = False, len(numbers_db.get('numbers', []))
    msg = (
        f"🚀 *البوت انطلق!*\n"
        f"📦 الأرقام المحفوظة: {cnt}\n"
        f"🌐 المنصات: {len(dynamic_platforms)}\n"
        f"⏱ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    if ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
        except Exception as notify_err:
            logger.warning(f"تعذر إرسال رسالة بدء التشغيل للمشرف: {notify_err}")
    log_event("BOT_STARTED", {"numbers": cnt, "platforms": len(dynamic_platforms)})

    # تنظيف أي Webhook قديم إن وجد
    try:
        bot.remove_webhook()
    except Exception as webhook_err:
        logger.warning(f"Webhook cleanup warning: {webhook_err}")

    # ✅ [SAFE] المزامنة التلقائية معطّلة - استخدم زر 🔄 مزامنة الأرقام في لوحة المطور
    # threading.Thread(target=auto_sync_loop, daemon=True).start()  # DISABLED

    logger.info("✅ Polling started…")
    conflict_backoff = 30
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception as poll_err:
            err_text = str(poll_err)
            if "Error code: 409" in err_text or "error code: 409" in err_text.lower():
                logger.error(
                    "❌ Telegram رفض getUpdates بسبب وجود نسخة أخرى تعمل بنفس التوكن. "
                    f"سيُعاد المحاولة تلقائياً بعد {conflict_backoff} ثانية."
                )
                try:
                    bot.remove_webhook()
                except Exception as webhook_err:
                    logger.warning(f"Webhook cleanup after 409 failed: {webhook_err}")
                time.sleep(conflict_backoff)
                continue
            logger.exception(f"Polling crashed, retrying in 5s: {poll_err}")
            time.sleep(5)




# ── رفع ملف TXT وإضافة أرقام ─────────────────────────────
@bot.message_handler(content_types=['document'])
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


@bot.callback_query_handler(func=lambda c: c.data.startswith("txtplt_"))
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




# ── منع إنشاء منصات جديدة ─────────────────────────────
def _platform_exists(platform):
    existing = set()
    for n in numbers_db.get("numbers", []):
        existing.add(_normalize_platform(n.get("platform", "")))
    return platform in existing


# ── تخزين الأرقام بانتظار التفعيل ─────────────────────
pending_activation = {}


# ── تعديل الإضافة ليقبل فقط منصات موجودة ─────────────
def _filter_existing_platforms(prepared):
    prepared_filtered = []
    for item in prepared:
        plat = _normalize_platform(item.get("platform"))
        if not _platform_exists(plat):
            continue
        prepared_filtered.append(item)
    return prepared_filtered


# ── أمر تأكيد الرقم ───────────────────────────────────
@bot.message_handler(commands=['confirm'])
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


# ── تنظيف تلقائي للأرقام غير المؤكدة ─────────────────
def cleanup_pending():
    now = time.time()
    to_delete = []

    for num, data in pending_activation.items():
        if now - data["time"] > 600:
            to_delete.append(num)

    for num in to_delete:
        pending_activation.pop(num, None)




# ── إرسال الأكواد تلقائيًا إلى القناة ─────────────────────────
CHANNEL_USERNAME = "@fz_z_Z"

sent_codes_cache = set()

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


if __name__ == "__main__":
    # ✅ [SAFE] إرسال الأكواد التلقائي معطّل
    # start_auto_sender()  # DISABLED
    main()


# --- ADD THIS TO YOUR ORIGINAL FILE ---

import re
import time
import threading

CHANNEL_USERNAME = "@fz_z_Z"

def fetch_live_test_codes():
    results = []
    try:
        session = _build_site_session()
        url = f"{SITE_URL}/portal/live/test-system/get"
        resp = session.post(url, timeout=20)

        if resp.status_code != 200:
            return results

        data = resp.json()
        rows = data.get("data", [])

        for row in rows:
            number = row.get("Number", "")
            message = row.get("Msg", "")
            sender = row.get("Sender", "")
            country = row.get("Country", "")

            code_match = re.search(r"\b\d{4,8}\b", message)

            if code_match:
                results.append({
                    "code": code_match.group(0),
                    "number": number,
                    "service": sender,
                    "country": country,
                    "message": message
                })

    except Exception as e:
        print("Error:", e)

    return results


def send_codes_to_channel(codes):
    for item in codes:
        country_info = _get_country_info(item.get('number', ''))
        country_text = f"{country_info['flag']} {item.get('country') or country_info['name']}"
        text = (
            f"📩 كود جديد\n\n"
            f"🌍 الدولة: {country_text}\n"
            f"📱 الرقم: {item['number']}\n"
            f"🏷 الخدمة: {item['service']}\n"
            f"🔑 الكود: {item['code']}\n\n"
            f"💬 الرسالة:\n{item['message']}"
        )

        try:
            bot.send_message(CHANNEL_USERNAME, text)
        except Exception as e:
            print("Send error:", e)


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


# --- RUN THREAD ---
# ✅ [SAFE] خيط live_codes_loop معطّل تلقائياً
# threading.Thread(target=live_codes_loop, daemon=True).start()  # DISABLED


# ═══════════════════════════════════════════════════════════════
#  ✅ [SAFE ADDITIONS] — لا يتم تعديل أي كود قديم، فقط إضافات
# ═══════════════════════════════════════════════════════════════

# ── أيقونات المنصات الإضافية (بنفس اسمها في الموقع) ──────────
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

# دمج الأيقونات الجديدة مع القديمة (القديمة لها الأولوية)
for _plat, _icon in _EXTRA_PLATFORM_ICONS.items():
    if _plat not in PLATFORM_BUTTON_ICONS:
        PLATFORM_BUTTON_ICONS[_plat] = _icon

# أسماء المنصات كنماذج لإضافتها ديناميكياً إلى PLATFORM_CANONICAL_ALIASES
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

# دمج الـ aliases الجديدة مع القديمة
for _alias, _canonical in _EXTRA_PLATFORM_ALIASES.items():
    if _alias not in PLATFORM_CANONICAL_ALIASES:
        PLATFORM_CANONICAL_ALIASES[_alias] = _canonical


# ══════════════════════════════════════════════════════════════
#  📥 جلب أرقام الموقع يدوياً — زر في لوحة المطور
# ══════════════════════════════════════════════════════════════

def _dev_fetch_from_site_and_report(chat_id: int):
    """يجلب الأرقام من الموقع (بناءً على طلب يدوي) ويرسل تقريراً نصياً."""
    try:
        bot.send_message(chat_id, "⏳ جاري جلب الأرقام من الموقع...")
        ok, cnt = fetch_numbers_smart(notify_users=False)
        platforms_list = _platform_picker_platforms()
        if ok and cnt:
            lines = [f"✅ تم جلب {cnt} رقم من الموقع بنجاح!", "", "📊 تفاصيل المنصات:"]
            for plat in platforms_list:
                nums = _numbers_for_platform(plat)
                if nums:
                    icon = PLATFORM_BUTTON_ICONS.get(plat, "📂")
                    lines.append(f"  {icon} {plat}: {len(nums)} رقم")
            lines.append(f"\n🌐 إجمالي المنصات: {len(platforms_list)}")
            bot.send_message(chat_id, "\n".join(lines))
        else:
            bot.send_message(
                chat_id,
                "⚠️ لم يتم جلب أرقام جديدة من الموقع.\n"
                "الأسباب المحتملة:\n"
                "• الكوكيز/التوكن منتهية الصلاحية\n"
                "• لا توجد أرقام جديدة في الحساب\n"
                "• مشكلة في الاتصال بالموقع\n\n"
                "استخدم ➕ إضافة يدوية بدلاً من ذلك."
            )
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء جلب الأرقام: {e}")


@bot.callback_query_handler(func=lambda c: c.data == "dev_fetch_site")
def dev_fetch_site_callback(call):
    """معطّل في النسخة الآمنة."""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "🛡️ هذا الزر معطّل في النسخة الآمنة.\nاستخدم الإضافة اليدوية أو استيراد TXT فقط.",
    )


# إضافة زر "📥 جلب أرقام الموقع" إلى لوحة المطور عبر override للدالة القديمة
_original_build_developer_panel_markup = _build_developer_panel_markup

def _build_developer_panel_markup() -> types.InlineKeyboardMarkup:
    mk = _original_build_developer_panel_markup()
    mk.add(types.InlineKeyboardButton("📤 تصدير TXT لكل المنصات", callback_data="dev_export_all_txt"))
    return mk


# ══════════════════════════════════════════════════════════════
#  📤 تصدير ملف TXT لكل منصة — زر في لوحة المطور
# ══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "dev_export_all_txt")
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


# ══════════════════════════════════════════════════════════════
#  📨 إرسال ملف TXT بعد كل إضافة يدوية (override للدالة القديمة)
# ══════════════════════════════════════════════════════════════

_original_process_manual_add = _process_manual_add

def _process_manual_add(message):
    """نسخة موسّعة: تُشغّل الكود القديم ثم ترسل ملف TXT بالأرقام المضافة."""
    # احفظ حالة قبل الإضافة
    before_items_snapshot = list(numbers_db.get("numbers", []))

    # تنفيذ الدالة الأصلية
    _original_process_manual_add(message)

    # استخرج الأرقام المضافة فعلياً
    after_items = numbers_db.get("numbers", [])
    added_items = _find_newly_added_numbers(before_items_snapshot, after_items)

    if not added_items:
        return  # لا جديد

    # بناء ملف TXT للأرقام المضافة مصنّفة حسب المنصة
    platform_groups: dict = {}
    for item in added_items:
        plat = item.get("platform", "General")
        platform_groups.setdefault(plat, []).append(item)

    import io
    lines = [
        f"📋 أرقام مضافة حديثاً",
        f"⏱ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"📱 عدد الأرقام: {len(added_items)}",
        f"🌐 المنصات: {len(platform_groups)}",
        "",
    ]
    for plat, items in platform_groups.items():
        icon = PLATFORM_BUTTON_ICONS.get(plat, "📂")
        lines.append(f"{'='*40}")
        lines.append(f"{icon} {plat} ({len(items)} رقم)")
        lines.append(f"{'='*40}")
        for item in items:
            country = _get_country_info(item.get("number", ""))
            lines.append(
                f"{country['flag']} {item['number']}  |  {country['name']}"
            )
        lines.append("")

    content = "\n".join(lines).encode("utf-8")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        bot.send_document(
            message.chat.id,
            ("added_numbers_" + timestamp + ".txt", io.BytesIO(content), "text/plain"),
            caption=(
                f"📨 ملف الأرقام المضافة يدوياً\n"
                f"✅ {len(added_items)} رقم جديد على {len(platform_groups)} منصة"
            ),
        )
    except Exception as send_err:
        logger.warning(f"تعذّر إرسال ملف TXT بعد الإضافة اليدوية: {send_err}")


# ── تسجيل الدالة الجديدة كـ handler للخطوة التالية ─────────
# (نُعيد ربط الـ handler بحيث يستخدم النسخة الجديدة)
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


# ══════════════════════════════════════════════════════════════
#  📨 إرسال ملف TXT بعد استيراد TXT (override txt_platform_selected)
# ══════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════
#  🔧 تحديث developer_panel_handler ليستخدم الـ markup الجديد
# ══════════════════════════════════════════════════════════════

def developer_panel_handler_v2(message):
    """نسخة محدّثة من لوحة المطور تتضمن أزرار الجلب والتصدير."""
    bot.send_message(
        message.chat.id,
        "🛠️ لوحة المطور\n\nاختر القسم الذي تريد إدارته:",
        reply_markup=_build_developer_panel_markup()
    )
