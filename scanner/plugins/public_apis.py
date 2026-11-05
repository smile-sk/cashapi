#!/usr/bin/env python3
"""Разведчик public-apis (GitHub) - 1700+ бесплатных API по категориям.

Парсит README: категории и число API в каждой. Топ категорий = где
проверенный спрос и куча готовых примеров для вдохновения.
"""
import re

async def probe(session, cfg):
    async with session.get(cfg["url"], timeout=cfg.get("timeout", 60)) as r:
        text = await r.text()

    cats = {}
    cat = None
    for ln in text.splitlines():
        m = re.match(r"^### (.+)$", ln)
        if m:
            cat = m.group(1).strip()
            cats.setdefault(cat, 0)
            continue
        if ln.startswith("| [") and cat:
            cats[cat] += 1

    top = sorted(cats.items(), key=lambda kv: -kv[1])[:15]
    return {
        "status": r.status,
        "meta": {
            "categories": len(cats),
            "entries_total": sum(cats.values()),
            "top_categories": top,
        },
    }
