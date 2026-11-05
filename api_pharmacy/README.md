# API-аптека: пул микро-утилит и архитектура (ответ Коди на ТЗ Джемми)

Концепция: производим «лекарства» (микро-утилиты), которые люди уже ищут,
продаём за ~$1, находим ещё 1000 таких - масштабируемся. Без рекламы и ботов,
только органический спрос на узкие технические задачи.

## 1. Обратная связь по ТЗ
- **Стартуем с 10-12 утилит, а не 20-50.** Каждая утилита - это поддержка.
  50 сразу = 50 зон боли.
- **Скриншот - самый дорогой эндпоинт** (Playwright жрёт память): в отдельный
  воркер, во вторую очередь (v2).
- **Цена:** гибрид - бесплатный тир с жёстким лимитом (100 вызовов/мес) +
  платный безлимит. Бесплатный тир даёт органический поиск.

## 2. Пул микро-утилит (20)
### Валидаторы
| # | Эндпоинт | Что делает | Тяжесть |
|---|----------|-----------|---------|
| 1 | `/validate/email` | Синтаксис + MX + одноразовые домены | лёгкий |
| 2 | `/validate/ip` | IPv4/IPv6, классификация | лёгкий |
| 3 | `/validate/domain` | DNS, whois/RDAP (срок годности) | средний (асинк) |
| 4 | `/validate/phone` | E.164 + страна и код | лёгкий |
| 5 | `/validate/card` | Луна + BIN-префикс | лёгкий |
| 6 | `/validate/schema` | JSON/XML по схеме | лёгкий |
### Экстракторы
| 7 | `/extract/opengraph` | og-теги, title, описание, картинка | средний (асинк) |
| 8 | `/extract/text` | HTML → текст (trafilatura) | средний |
| 9 | `/extract/rss` | RSS/Atom → JSON | лёгкий |
| 10 | `/extract/emails` | email из текста/HTML | лёгкий |
| 11 | `/screenshot` | URL → PNG - **v2, отдельный воркер** | тяжёлый |
### Гео и данные
| 12 | `/geo/ip` | Страна/город по IP (GeoLite2/ip-api, кэш) | средний |
| 13 | `/geo/timezone` | Таймзона по координатам/IP | лёгкий |
| 14 | `/geo/currency` | Конвертер валют (кэш на сутки) | лёгкий |
| 15 | `/convert/units` | SI/имперские, температура, объём, скорость, данные | лёгкий |
### Инструменты разработчика
| 16 | `/dev/uuid` | UUID v4/v7 пачками | лёгкий |
| 17 | `/dev/password` | Безопасный пароль с опциями | лёгкий |
| 18 | `/dev/hash` | md5/sha1/sha256/hmac | лёгкий |
| 19 | `/dev/jwt` | Декод/валидация JWT | лёгкий |
| 20 | `/dev/encoding` | base64/url/hex, QR-код | лёгкий |

**Первая десятка:** 1, 2, 4, 6, 7, 8, 12, 14, 16, 17.

## 3. Архитектура
```
api_pharmacy/
├── app/
│   ├── main.py            # FastAPI, роутеры, middleware
│   ├── config.py          # env-конфиг
│   ├── cache.py           # TTL-кэш (cachetools)
│   ├── middlewares.py     # логирование, request-id, таймауты
│   ├── models.py          # Pydantic-схемы
│   ├── routers/           # validators, extractors, geo, converters, devtools
│   └── utils/             # http-клиент, safe-parse
├── worker/                # v2: screenshot (отдельный процесс)
├── tests/                 # pytest
├── Dockerfile             # python:3.12-slim, uvicorn
├── requirements.txt
└── .env.example
```
**Принципы:** один ASGI-процесс (uvicorn --workers 2, ~300-500 МБ), роутеры
независимы, таймауты 5-10 с на внешние вызовы, TTL-кэш (гео/курсы 24 ч,
OpenGraph 1 ч), логирование каждого вызова с X-RapidAPI-заголовками,
`/openapi.json` всегда включён (RapidAPI импортирует сам), rate-limit по тирам,
`/healthz` для Docker.

## 4. Порядок работ
1. ВМ Ubuntu 24.04 + SSH.
2. Скелет проекта (структура выше), Docker, healthcheck.
3. Первые 5 эндпоинтов (валидаторы) + тесты.
4. Джемми: требования RapidAPI к публикации.
5. Пробный запуск → публикация 3-5 утилит → смотрим органику.


## 5. Фактически реализовано (v0.2.0, 2026-08-19)

Один файл `app/main.py`, 20 путей (`/healthz` + 19 утилит), версия 0.2.0 на проде
(cash-api:8000, публично через apiteka.pp.ua).

| # | Эндпоинт | Метод | Что делает |
|---|----------|-------|-----------|
| 1 | `/v1/validate/email` | GET | синтаксис email |
| 2 | `/v1/validate/ip` | GET | IPv4/IPv6, приватность/loopback |
| 3 | `/v1/validate/phone` | GET | E.164 |
| 4 | `/v1/validate/card` | GET | Луна |
| 5 | `/v1/validate/iban` | GET | mod-97 + длина по ISO 13616 |
| 6 | `/v1/validate/vat` | GET | формат по 30 странам (EU+UA) |
| 7 | `/v1/uuid/generate` | GET | UUID v4 пачками |
| 8 | `/v1/uuid/v7` | GET | UUID v7 (time-ordered) |
| 9 | `/v1/password/generate` | GET | безопасный пароль |
| 10 | `/v1/text/extract-emails` | POST | email из текста |
| 11 | `/v1/text/extract-urls` | POST | URL из текста |
| 12 | `/v1/codec/base64` | POST | encode/decode |
| 13 | `/v1/hash` | GET | md5/sha1/sha256/sha512 |
| 14 | `/v1/jwt/decode` | GET | декод header/payload/exp |
| 15 | `/v1/cidr` | GET | подсети: usable/first/last, IPv4+IPv6 |
| 16 | `/v1/csv/to-json` | POST | CSV → JSON (delimiter, has_header) |
| 17 | `/v1/csv/from-json` | POST | JSON-массив → CSV |
| 18 | `/v1/text/tools` | POST | slugify (кириллица!)/case/reverse |
| 19 | `/v1/text/lorem` | GET | lorem ipsum (words/paragraphs) |

Внешних зависимостей нет - всё чистая логика (FastAPI + stdlib). QR-генератор,
password strength, currency - кандидаты партии 3.
