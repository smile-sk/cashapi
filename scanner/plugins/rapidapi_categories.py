#!/usr/bin/env python3
"""Разведчик RapidAPI - карта категорий (сегменты спроса).

Тянет sitemap-category.xml: все категории маркетплейса RapidAPI.
Категория = сегмент, где люди ищут и платят. Наш профиль (микро-утилиты)
живёт в Email / Finance / Tools / Data / Text Analysis / Cryptography.
"""
import re

async def probe(session, cfg):
    async with session.get(cfg["url"], timeout=cfg.get("timeout", 60)) as r:
        body = await r.text()

    locs = re.findall(r"<loc>(.*?)</loc>", body)
    cats = []
    for l in locs:
        c = l.rsplit("/search/", 1)[-1].replace("%20", " ").strip()
        if c and c.lower() != "other":
            cats.append(c)

    return {
        "status": r.status,
        "meta": {"categories_total": len(cats), "categories": cats},
    }
