# geosite_russia

[![Build geosite.dat](https://github.com/yularzhi/geosite_russia/actions/workflows/build-geosite.yml/badge.svg)](https://github.com/yularzhi/geosite_russia/actions/workflows/build-geosite.yml)
[![Last Commit](https://img.shields.io/github/last-commit/yularzhi/geosite_russia)](https://github.com/yularzhi/geosite_russia/commits/main)
[![Release Branch](https://img.shields.io/badge/release-branch-blue)](https://github.com/yularzhi/geosite_russia/tree/release)
[![Raw geosite.dat](https://img.shields.io/badge/raw-geosite.dat-brightgreen)](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat)

Кастомный geosite.dat для Xray и набор `.srs` rule-set файлов для Sing-box / Happ и других клиентов.

Основная цель проекта — создать лёгкий и эффективный набор доменных правил для работы в России:
- обход блокировок
- стабильная работа сервисов
- минимальное потребление памяти
- чистая и понятная структура

## 📌 Почему этот проект?
В отличие от стандартных списков `v2fly`, этот набор доменных правил сфокусирован на:
* **Российском контексте:** Список `ru-blocked` автоматически очищен от российских доменов (`category-ru`), что минимизирует проблемы с доступом к госуслугам, банкам и локальным сервисам при включенном прокси.
* **Производительности:** Оптимизирован для работы на устройствах с низким объемом оперативной памяти (роутеры OpenWrt, мобильные устройства) — потребление около 20–30 MB.
* **Автоматизации:** Ежедневная сборка на базе свежих дамп-листов, чтобы вы всегда имели актуальные правила.
* **Адаптации:** Полная совместимость с логикой маршрутизации популярных клиентов, включая **Happ**, **Sing-box** и **Xray**.

## 📦 Состав

В итоговом geosite.dat доступны следующие теги:

🚀 Основной список
ru-blocked — объединённый список:
- community.antifilter.download (заблокированные в РФ домены)
- Loyalsoldier surge-rules proxy.txt (международные сервисы, требующие проксирования)
- sources/manual_ru_blocked.txt (ручные дополнения: speedtest, игры, CDN)

Очищен от российских доменов (category-ru + суффиксы + `.ru/.su/.рф`).

🇷🇺 Российские ресурсы
category-ru — официальный список российских доменов из v2fly

🚫 Реклама
category-ads-all — список рекламы из v2fly/domain-list-community + HaGeZi + Peter Lowe

📱 Сервисы
telegram
viber (расширен доменами Rakuten)
whatsapp
meta
facebook
google
supercell
roblox

🧩 Sing-box
rule-set файлы в формате `.srs` для каждого тега из списка выше

🔒 Системные
private — локальные сети и приватные домены

## ⚡ Быстрый старт

### Happ
В настройках клиента перейдите в раздел **Routing (Маршрутизация)**:
1. Убедитесь, что выбран источник для `geosite`.
2. Установите ссылку на ваш файл: `https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat`
3. В правилах маршрутизации используйте следующие теги:
   - `geosite:ru-blocked` -> **Proxy**
   - `geosite:category-ru` -> **Direct**
   - `geosite:category-ads-all` -> **Block**

### Sing-box / Xray (Core)
В конфигурационном файле (`config.json`):
```json
"geosite": {
  "paths": ["/путь/к/вашему/geosite.dat"]
}
```

Для Sing-box используйте `rule_set` и отдельные `.srs` файлы, например:
```json
{
  "route": {
    "rule_set": [
      {
        "tag": "category-ru",
        "type": "remote",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/category-ru.srs"
      }
    ]
  }
}
```

## ⬇️ Скачать

Актуальная версия:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat

SHA256:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat.sha256

Sing-box rule-sets:

| Tag | Raw URL |
| --- | --- |
| `ru-blocked` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/ru-blocked.srs) |
| `category-ads-all` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/category-ads-all.srs) |
| `category-ru` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/category-ru.srs) |
| `telegram` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/telegram.srs) |
| `viber` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/viber.srs) |
| `whatsapp` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/whatsapp.srs) |
| `meta` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/meta.srs) |
| `facebook` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/facebook.srs) |
| `google` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/google.srs) |
| `supercell` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/supercell.srs) |
| `roblox` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/roblox.srs) |
| `apple` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/apple.srs) |
| `private` | [srs](https://raw.githubusercontent.com/yularzhi/geosite_russia/release/sing-box/private.srs) |

## ⚙️ Использование

Proxy:
geosite:ru-blocked
geosite:telegram
geosite:viber
geosite:whatsapp
geosite:meta
geosite:facebook
geosite:google

Direct:
geosite:category-ru
geosite:private

Block:
geosite:category-ads-all

## 🔄 Автоматизация

Сборка выполняется автоматически через GitHub Actions:

- скачиваются исходные списки (antifilter, Loyalsoldier proxy, HaGeZi, Peter Lowe)
- нормализуются домены (lowercase, punycode/IDN, обрезка портов)
- разворачиваются include зависимости из v2fly DLC
- генерируется geosite.dat и набор sing-box rule-set файлов
- публикуется в ветку release

Обновление происходит ежедневно.

## 📊 Особенности

- оптимизировано под низкое потребление памяти (~20–30 MB)
- ru-blocked объединяется из antifilter + Loyalsoldier proxy + ручных доменов и очищается от RU
- category-ads-all берётся из v2fly/domain-list-community + HaGeZi + Peter Lowe
- отсутствуют лишние и дублирующие списки
- все зависимости разворачиваются в плоский вид
- полный контроль над составом списков

## 📚 Источники

Основные (см. `sources/config.yaml`):
https://community.antifilter.download/list/domains.txt
https://github.com/Loyalsoldier/surge-rules (proxy.txt)
https://github.com/hagezi/dns-blocklists (wildcard light)
https://pgl.yoyo.org/adservers/

Upstream:
https://github.com/v2fly/domain-list-community

## 🙏 Благодарности

v2fly  
https://github.com/v2fly/domain-list-community  
Базовый проект geosite

RunetFreedom  
https://github.com/runetfreedom/russia-blocked-geosite  
Ранее использовавшийся источник списков заблокированных доменов

Loyalsoldier  
https://github.com/Loyalsoldier/v2ray-rules-dat  
Идеи сборки и структура

Antifilter  
https://community.antifilter.download  
Список заблокированных доменов

## ⚠️ Примечания

- ru-blocked — объединённый список (antifilter + Loyalsoldier proxy + ручной), очищен от российских доменов
- category-ads-all — готовый список рекламы из v2fly/domain-list-community + HaGeZi + Peter Lowe
- viber расширен доменами Rakuten
- category-ads-all используется в полном развёрнутом виде
- итоговый файл не содержит промежуточных тегов

## 📄 Лицензия

Репозиторий агрегирует данные из сторонних источников.  
Смотри лицензии в оригинальных проектах.

## 💬 Обратная связь

Pull request'ы и идеи приветствуются.
