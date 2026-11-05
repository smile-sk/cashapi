#!/usr/bin/env python3
"""Разведчик apis.guru - каталог OpenAPI-спецификаций (2500+ API).

Считает, сколько API на площадке завязано на каждую «таблетку» (тему-утилиту).
Много совпадений по теме = доказанный спрос; мало = возможная ниша.
"""
import re

KEYWORDS = {
    "email": r"email|mail",
    "phone/sms": r"phone|sms|call|voice",
    "vat/tax": r"\bvat\b|\btax\b",
    "iban/bank": r"iban|bank|bic|swift",
    "currency": r"currency|exchange rate|forex|\bfx\b",
    "ip/geo": r"\bip\b|geoip|geolocat",
    "domain/dns": r"domain|dns|whois",
    "qr/barcode": r"\bqr\b|barcode|ean",
    "uuid": r"uuid|guid",
    "hash/crypto": r"hash|md5|sha|encrypt|decrypt",
    "base64": r"base64",
    "text tools": r"slug|lorem|diff|case converter|format",
    "csv/json": r"csv|json",
    "image/ocr": r"image|ocr|thumbnail|screenshot",
    "translate": r"translate|language",
    "weather": r"weather|forecast",
    "finance/stocks": r"stock|quote|finance|market",
}

async def probe(session, cfg):
    async with session.get(cfg["url"], timeout=cfg.get("timeout", 60)) as r:
        data = await r.json()

    titles = []
    for key, entry in data.items():
        pref = entry.get("preferred")
        if pref and pref in entry.get("versions", {}):
            info = entry["versions"][pref].get("info", {})
            titles.append((info.get("title") or key).lower())

    hits = {}
    for name, pat in KEYWORDS.items():
        hits[name] = sum(1 for t in titles if re.search(pat, t))

    return {
        "status": r.status,
        "meta": {"apis_total": len(titles), "keyword_hits": hits},
    }
