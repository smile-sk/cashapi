"""CashAPI - API-аптека. Микро-утилиты по подписке для RapidAPI/Zyla.

Первая и вторая партии «таблеток»: валидаторы, генераторы, экстракторы,
кодеки, текстовые инструменты. Каждый эндпоинт - отдельная лёгкая утилита;
/openapi.json импортируется маркетплейсом автоматически.
"""
import base64
import csv
import hashlib
import io
import ipaddress
import json
import random
import re
import secrets
import time
import unicodedata
import uuid as uuid_lib
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(
    title="CashAPI Micro Utilities",
    version="0.2.0",
    description="Микро-утилиты: валидаторы, генераторы, экстракторы, кодеки, текстовые инструменты.",
)


# ---------------- health ----------------
@app.get("/healthz")
def healthz():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


# ---------------- validators ----------------
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+\d{6,15}$")


@app.get("/v1/validate/email")
def validate_email(email: str = Query(...)):
    return {"valid": bool(EMAIL_RE.match(email)), "email": email}


@app.get("/v1/validate/ip")
def validate_ip(ip: str = Query(...)):
    try:
        addr = ipaddress.ip_address(ip)
        return {
            "valid": True,
            "version": addr.version,
            "is_private": addr.is_private,
            "is_loopback": addr.is_loopback,
        }
    except ValueError:
        return {"valid": False, "ip": ip}


@app.get("/v1/validate/phone")
def validate_phone(phone: str = Query(...)):
    return {"valid": bool(PHONE_RE.match(phone)), "phone": phone}


@app.get("/v1/validate/card")
def validate_card(number: str = Query(...)):
    digits = re.sub(r"\D", "", number)
    if not (13 <= len(digits) <= 19):
        return {"valid": False, "reason": "length"}
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return {"valid": total % 10 == 0, "brand": "unknown"}


# Длины IBAN по ISO 13616 (основные страны)
IBAN_LENGTHS = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BR": 29, "BY": 28, "CH": 21, "CR": 22, "CY": 28,
    "CZ": 24, "DE": 22, "DK": 18, "DO": 28, "EE": 20, "ES": 24, "FI": 18,
    "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27,
    "GT": 28, "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IQ": 23, "IS": 26,
    "IT": 27, "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21,
    "LT": 20, "LU": 20, "LV": 21, "MC": 27, "MD": 24, "ME": 22, "MK": 19,
    "MR": 27, "MT": 31, "MU": 30, "NL": 18, "NO": 15, "PK": 24, "PL": 28,
    "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22, "SA": 24, "SC": 31,
    "SD": 18, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "ST": 25, "TL": 23,
    "TN": 24, "TR": 26, "UA": 29, "VA": 22, "VG": 24, "XK": 20,
}


@app.get("/v1/validate/iban")
def validate_iban(iban: str = Query(...)):
    clean = re.sub(r"[\s-]", "", iban or "").upper()
    if len(clean) < 15 or len(clean) > 34:
        return {"valid": False, "reason": "length", "iban": iban}
    cc = clean[:2]
    if cc in IBAN_LENGTHS and len(clean) != IBAN_LENGTHS[cc]:
        return {"valid": False, "reason": f"length_for_{cc}", "country": cc}
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", clean):
        return {"valid": False, "reason": "format"}
    rearranged = clean[4:] + clean[:4]
    digits = "".join(str(ord(c) - 55) if "A" <= c <= "Z" else c for c in rearranged)
    return {"valid": int(digits) % 97 == 1, "country": cc, "iban": clean}


VAT_PATTERNS = {
    "AT": r"^ATU\d{8}$",
    "BE": r"^BE0\d{9}$",
    "BG": r"^BG\d{9,10}$",
    "CY": r"^CY\d{8}[A-Z]$",
    "CZ": r"^CZ\d{8,10}$",
    "DE": r"^DE\d{9}$",
    "DK": r"^DK\d{8}$",
    "EE": r"^EE\d{9}$",
    "EL": r"^EL\d{9}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "FI": r"^FI\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "GB": r"^GB(\d{9}|\d{12}|GD\d{3}|HA\d{3})$",
    "HR": r"^HR\d{11}$",
    "HU": r"^HU\d{8}$",
    "IE": r"^IE\d{7}[A-W]$",
    "IT": r"^IT\d{11}$",
    "LT": r"^LT\d{9,12}$",
    "LU": r"^LU\d{8}$",
    "LV": r"^LV\d{11}$",
    "MT": r"^MT\d{8}$",
    "NL": r"^NL\d{9}B\d{2}$",
    "PL": r"^PL\d{10}$",
    "PT": r"^PT\d{9}$",
    "RO": r"^RO\d{2,10}$",
    "SE": r"^SE\d{12}$",
    "SI": r"^SI\d{8}$",
    "SK": r"^SK\d{10}$",
    "UA": r"^UA\d{8,12}$",
}


@app.get("/v1/validate/vat")
def validate_vat(vat: str = Query(...), country: str = Query(None)):
    v = re.sub(r"[\s.\-]", "", vat or "").upper()
    detected = v[:2] if v[:2].isalpha() else None
    cc = (country or detected or "").upper()
    pattern = VAT_PATTERNS.get(cc)
    if not pattern:
        return {"valid": False, "reason": "unknown_country", "country": cc or None, "vat": v}
    return {"valid": bool(re.fullmatch(pattern, v)), "country": cc, "vat": v}


# ---------------- generators ----------------
@app.get("/v1/uuid/generate")
def uuid_generate(count: int = Query(1, ge=1, le=100)):
    return {"uuids": [str(uuid_lib.uuid4()) for _ in range(count)]}


@app.get("/v1/uuid/v7")
def uuid_v7(count: int = Query(1, ge=1, le=100)):
    ts = int(time.time() * 1000)
    out = []
    for _ in range(count):
        rand_a = secrets.randbits(12)
        rand_b = secrets.randbits(62)
        # layout: 48 бит ts | версия 7 (4 бита) | rand_a (12) | вариант 10 (2) | rand_b (62)
        value = (ts << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
        out.append(str(uuid_lib.UUID(int=value)))
    return {"uuids": out}


@app.get("/v1/password/generate")
def password_generate(length: int = Query(16, ge=8, le=128)):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%^&*"
    return {"password": "".join(secrets.choice(alphabet) for _ in range(length))}


# ---------------- extractors ----------------
URL_RE = re.compile(r"https?://[^\s<>\"']+")
MAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class TextIn(BaseModel):
    text: str


@app.post("/v1/text/extract-emails")
def extract_emails(body: TextIn):
    return {"emails": list(dict.fromkeys(MAIL_RE.findall(body.text)))}


@app.post("/v1/text/extract-urls")
def extract_urls(body: TextIn):
    return {"urls": list(dict.fromkeys(URL_RE.findall(body.text)))}


# ---------------- codecs ----------------
class CodecIn(BaseModel):
    data: str


@app.post("/v1/codec/base64")
def base64_codec(body: CodecIn, mode: str = Query("encode", pattern="^(encode|decode)$")):
    try:
        if mode == "encode":
            return {"result": base64.b64encode(body.data.encode()).decode()}
        return {"result": base64.b64decode(body.data).decode()}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@app.get("/v1/hash")
def hash_data(data: str = Query(...), algo: str = Query("sha256", pattern="^(md5|sha1|sha256|sha512)$")):
    return {"algo": algo, "hash": hashlib.new(algo, data.encode()).hexdigest()}


# ---------------- dev tools: JWT, CIDR ----------------
def _b64url_decode(s: str) -> str:
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    return base64.b64decode(s).decode("utf-8", errors="replace")


@app.get("/v1/jwt/decode")
def jwt_decode(token: str = Query(...)):
    parts = (token or "").split(".")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return {"valid": False, "error": "not_a_jwt"}
    try:
        header = json.loads(_b64url_decode(parts[0]))
        payload = json.loads(_b64url_decode(parts[1]))
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "error": str(exc)}
    result = {
        "valid": True,
        "header": header,
        "payload": payload,
        "signature_present": len(parts) == 3 and bool(parts[2]),
    }
    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        result["expires_at"] = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
    return result


@app.get("/v1/cidr")
def cidr_calc(cidr: str = Query(...)):
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        return {"valid": False, "error": str(exc)}
    n = net.num_addresses
    if net.version == 4 and n > 2:
        usable = n - 2
        first = str(net.network_address + 1)
        last = str(net.broadcast_address - 1)
    else:
        usable = n if net.version == 4 else None
        first = str(net.network_address)
        last = str(net.network_address + (n - 1))
    return {
        "valid": True,
        "network": str(net.network_address),
        "netmask": str(net.netmask),
        "prefix": net.prefixlen,
        "version": net.version,
        "total_addresses": n,
        "usable_hosts": usable,
        "first_usable": first,
        "last_usable": last,
        "is_private": net.is_private,
    }


# ---------------- csv ↔ json ----------------
@app.post("/v1/csv/to-json")
def csv_to_json(body: CodecIn, delimiter: str = Query(",", max_length=1), has_header: bool = Query(True)):
    try:
        rows = list(csv.reader(io.StringIO(body.data), delimiter=delimiter))
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    if not rows:
        return {"rows": [], "count": 0}
    if has_header:
        header = [h.strip() or f"col{i}" for i, h in enumerate(rows[0])]
        out = []
        for r in rows[1:]:
            if any(cell.strip() for cell in r):
                out.append(dict(zip(header, r)))
    else:
        out = rows
    return {"rows": out, "count": len(out)}


@app.post("/v1/csv/from-json")
def json_to_csv(body: CodecIn, delimiter: str = Query(",", max_length=1), include_header: bool = Query(True)):
    try:
        data = json.loads(body.data)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"invalid_json: {exc}"}
    if not isinstance(data, list) or not data:
        return {"error": "expected_nonempty_array"}
    if not all(isinstance(r, dict) for r in data):
        return {"error": "expected_array_of_objects"}
    keys = []
    for r in data:
        for k in r:
            if k not in keys:
                keys.append(k)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delimiter, lineterminator="\n")
    if include_header:
        w.writerow(keys)
    for r in data:
        w.writerow([r.get(k, "") for k in keys])
    return {"csv": buf.getvalue(), "rows": len(data)}


# ---------------- text tools ----------------
TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g",
}


def _slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).lower()
    s = "".join(TRANSLIT.get(ch, ch) for ch in s)
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


@app.post("/v1/text/tools")
def text_tools(
    body: TextIn,
    mode: str = Query("slugify", pattern="^(slugify|uppercase|lowercase|titlecase|snakecase|kebabcase|camelcase|reverse)$"),
):
    t = body.text
    if mode == "uppercase":
        out = t.upper()
    elif mode == "lowercase":
        out = t.lower()
    elif mode == "titlecase":
        out = t.title()
    elif mode == "snakecase":
        out = _slugify(t).replace("-", "_")
    elif mode == "kebabcase":
        out = _slugify(t)
    elif mode == "camelcase":
        parts = _slugify(t).split("-")
        out = parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else ""
    elif mode == "reverse":
        out = t[::-1]
    else:  # slugify
        out = _slugify(t)
    return {"mode": mode, "result": out}


LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt "
    "ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco "
    "laboris nisi aliquip ex ea commodo consequat duis aute irure in reprehenderit voluptate "
    "velit esse cillum eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident "
    "sunt culpa qui officia deserunt mollit anim id est laborum"
).split()


@app.get("/v1/text/lorem")
def lorem(words: int = Query(25, ge=1, le=1000), paragraphs: int = Query(1, ge=1, le=20)):
    out_p = []
    for _ in range(paragraphs):
        ws = [random.choice(LOREM_WORDS) for _ in range(words)]
        ws[0] = ws[0].capitalize()
        out_p.append(" ".join(ws) + ".")
    return {"text": "\n\n".join(out_p), "words": words, "paragraphs": paragraphs}
