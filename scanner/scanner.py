#!/usr/bin/env python3
"""Async scanner framework - Phase 1 (cody).

Асинхронный каркас сканера-разведчика: aiohttp + плагины + SQLite + пул воркеров.
Каждая площадка/источник - отдельный плагин в plugins/. Результаты пишутся в SQLite.

Запуск:
    pip install aiohttp
    python scanner.py
"""
import asyncio
import importlib
import json
import pathlib
import sqlite3
import time

BASE = pathlib.Path(__file__).parent
CONFIG = BASE / "config.json"
DB = BASE / "scan.db"


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class Store:
    def __init__(self, db=DB):
        self._lock = asyncio.Lock()
        self.con = sqlite3.connect(db)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS scans(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT, plugin TEXT, target TEXT,
                status INTEGER, latency_ms REAL, note TEXT)"""
        )
        self.con.commit()

    async def save(self, row):
        async with self._lock:
            self.con.execute(
                "INSERT INTO scans(ts,plugin,target,status,latency_ms,note) VALUES(?,?,?,?,?,?)",
                row,
            )
            self.con.commit()


def load_plugins():
    out = {}
    for p in (BASE / "plugins").glob("*.py"):
        if p.name.startswith("_"):
            continue
        m = importlib.import_module(f"plugins.{p.stem}")
        out[p.stem] = m
    return out


async def run_plugin(name, mod, cfg, session, store):
    t0 = time.perf_counter()
    try:
        res = await mod.probe(session, cfg)
        lat = (time.perf_counter() - t0) * 1000
        note = json.dumps(res.get("meta", {}), ensure_ascii=False)[:400]
        await store.save((now_iso(), name, cfg.get("url", ""), res.get("status", 0), lat, note))
    except Exception as e:
        lat = (time.perf_counter() - t0) * 1000
        await store.save((now_iso(), name, cfg.get("url", ""), -1, lat, f"ERR {e}")[:400])


async def worker(q, session, store, plugins):
    while True:
        name, cfg = await q.get()
        try:
            await run_plugin(name, plugins[name], cfg, session, store)
        finally:
            q.task_done()


async def main():
    import aiohttp

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    plugins = load_plugins()
    store = Store(cfg.get("db", str(DB)))

    async with aiohttp.ClientSession() as session:
        q = asyncio.Queue()
        for t in cfg["targets"]:
            if t["plugin"] in plugins:
                q.put_nowait((t["plugin"], t))
        workers = [
            asyncio.create_task(worker(q, session, store, plugins))
            for _ in range(cfg.get("workers", 8))
        ]
        await q.join()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    print(f"[{now_iso()}] scan done: {len(cfg['targets'])} targets -> {store.con.total_changes} rows")


if __name__ == "__main__":
    asyncio.run(main())
