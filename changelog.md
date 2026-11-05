# Журнал изменений CashAPI

## 2026-08-19 (ночь) - Витрина RapidAPI доведена до ума ✅
- Draft 0.2.0 активирован через **Import OpenAPI** (файл `api_pharmacy/openapi.json`, 20 путей, префикс `/v1/` сохранён - без него прокси отдаёт 404).
- Base URL `https://apiteka.pp.ua` + Health Check `/healthz` прописаны в студии (урок: поле Health Check принимает только путь, не полный URL).
- Метрика Test **50% → 100%**: тест healthz пересоздан (раз в 6 часов) - фейл был из-за неверного health check на старте.
- README витрины переписан: слоган + **реальные JSON-примеры** к каждому эндпоинту (сняты с продакшена), пути `/v1/`.
- Добавлены **3 спотлайта**: Validate Email, Generate UUID v7, CIDR Calculator (ведут на playground-страницы с примерами).
- Ключ Zyla сохранён в `.env` (`ZYLA_API_KEY`, `ZYLA_PROJECT_ID`) - второй аэродром готов к публикации.
- Следующее: публикация на Zyla (чек-лист Джемми), партия 3 (GeoIP 9.5 → Currency 9.0 → QR 8.5 → Phone 7.5 → Password 5.0 + UA Parser, Temp Email Detector).

## 2026-08-19 (поздно) - Вторая партия таблеток v0.2.0 ✅
- Набор из скан-отчёта подтверждён Стасом, написаны и задеплоены **9 новых эндпоинтов**:
  `/v1/validate/iban` (mod-97 + длины по ISO 13616), `/v1/validate/vat` (30 стран, EU+UA),
  `/v1/jwt/decode` (header/payload/exp), `/v1/cidr` (IPv4/IPv6, usable/first/last),
  `/v1/csv/to-json` и `/v1/csv/from-json`, `/v1/text/tools` (slugify с кириллицей/case),
  `/v1/text/lorem`, `/v1/uuid/v7` (time-ordered, RFC 4122).
- Витрина: **11 → 20 путей** (healthz + 19 утилит), версия 0.2.0.
- Тесты: py_compile + прогон алгоритмов (IBAN/VAT/JWT/CIDR/CSV/slugify/UUIDv7) локально,
  смоук на сервере (все зелёные), публичный `https://apiteka.pp.ua/openapi.json` = 0.2.0.
- Деплой: SFTP (paramiko) + docker build/run на cash-api, `--restart unless-stopped`.
- Снапшот до правок: `.snapshots/main_v0.1.0_20260819_164431.py`.
- Следующее: проверить витрину RapidAPI (спека подтянулась?), Zyla, партия 3 (currency/QR/password strength).

## 2026-08-19 (вечер) - Сканер ожил: первый разведполёт ✅
- Написаны и проверены живьём три плагина: `apis_guru` (2529 API, счётчик по темам),
  `public_apis` (1702 API, 52 категории), `rapidapi_categories` (48 категорий маркетплейса из sitemap).
- Конфиг `scanner/config.json` - 3 реальных таргета вместо примерочного github.
- **Отчёт** `scanner/scan_report_2026-08-19.md`: карта спроса и кандидаты во вторую
  партию таблеток: IBAN, VAT, JWT, CIDR, CSV↔JSON, Text Tools, UUID v7 (+QR, password strength опционально).
- Вывод: 11 эндпоинтов мало - ядро второй партии из 6 новых таблеток выведет витрину на ~17.
- RapidAPI-поиск скрейпить нельзя (SPA) - используем sitemap категорий + ручной браузерный контроль.

## 2026-08-19 - Публикация витрины на RapidAPI ✅
- Домен `apiteka.pp.ua` зарегистрирован (NIC.UA, бесплатный pp.ua), NS переведены на Cloudflare.
- Cloudflare Tunnel (`apiteka`) поднят на cash-api; `https://apiteka.pp.ua/healthz` отвечает снаружи, домашний IP в тени.
- Проект **CashAPI Micro Utilities** создан и опубликован на RapidAPI (krisanovstas, id `39ab6fc0…`).
- Импортирована спецификация `/openapi.json`: 10 утилит + healthz, рабочие пути `/v1/…`.
- **Base URL** `https://apiteka.pp.ua` и Health Check прописаны в студии (без этого прокси RapidAPI отдавал 400 - поймали до первых продаж).
- Тарифы: **BASIC $0.00** (500 req/мес, пробник), **PRO $9.99** (100k req/мес, Recommended). ULTRA/MEGA неактивны.
- Документация: README заполнен в студии и виден на витрине (предупреждение «Documentation is not set» ушло).
- Лого залито (`creadev_logo.png`).
- Тест через прокси RapidAPI (`…p.rapidapi.com/healthz`) → **200** `{"status":"ok"}` - цепочка «подписка → прокси → наш сервер» живая.

## 2026-08-18 - Каркас и старт
- ТЗ Джемми на аптеку (`agents/gemmy/request_to_cody_api_pharmacy_2026-08-18.md`), пул 20 утилит, шорт-лист площадок.
- Каркас сканера (`scanner/`: aiohttp + пул воркеров + SQLite + плагины).
- ВМ Ubuntu 24.04 на NAS (hostname `cash-api`, x.x.x.x), пользователь `cody`, SSH-ключ ed25519, Docker 29.1.3 + Compose 2.40.3, ufw (только SSH).
