# geosite_russia

Кастомный `geosite.dat` для Xray / v2fly / Sing-box / Happ и других клиентов.

Репозиторий автоматически собирает оптимизированный набор правил для работы в России с акцентом на:
- стабильную работу мессенджеров
- обход блокировок
- корректную блокировку рекламы
- минимальное потребление памяти

## 📦 Состав

В итоговом `geosite.dat` доступны следующие теги:

### 🇷🇺 Основной список
- `custom-ru` — объединённый список:
  - antifilter
  - refilter

### 🚫 Реклама
- `category-ads-all` — официальный список из domain-list-community (полностью развёрнут, без include)

### 🌐 Россия (внутренние ресурсы)
- `ru-available-only-inside` — домены, доступные только внутри РФ (runetfreedom)

### 🔒 Системные
- `private` — локальные и приватные сети (v2fly)

### 📱 Сервисы
- `telegram`
- `viber`
- `whatsapp`
- `meta`
- `facebook`
- `google`
- `supercell`
- `roblox`

## ⬇️ Скачать

Актуальная версия:

`https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat`

Контрольная сумма:

`https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat.sha256`

## ⚙️ Использование

Примеры тегов:

- `geosite:custom-ru`
- `geosite:category-ads-all`
- `geosite:ru-available-only-inside`
- `geosite:private`
- `geosite:telegram`
- `geosite:viber`
- `geosite:whatsapp`
- `geosite:meta`
- `geosite:facebook`
- `geosite:google`
- `geosite:supercell`
- `geosite:roblox`

## 🎯 Рекомендации по использованию

### Proxy
- `geosite:custom-ru`
- `geosite:telegram`
- `geosite:viber`
- `geosite:whatsapp`
- `geosite:meta`
- `geosite:google`

### Direct
- `geosite:private`
- `geosite:ru-available-only-inside`

### Block
- `geosite:category-ads-all`

## 🔄 Автоматизация

Репозиторий автоматически:
- скачивает исходные списки
- очищает и нормализует `custom-ru`
- удаляет дубликаты
- подтягивает upstream-теги
- разворачивает все include-зависимости
- генерирует чистый `geosite.dat` без лишних тегов
- публикует результат в ветку `release`

Обновление выполняется ежедневно через GitHub Actions.

## 📚 Источники

### 🇷🇺 Основной список
- [community.antifilter.download](https://community.antifilter.download/list/domains.txt)
- [Re-filter-lists](https://github.com/1andrevich/Re-filter-lists)

### 📦 Upstream (geosite база)
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)

### 🌐 Россия (доступ только внутри)
- [runetfreedom/russia-domains-list](https://github.com/runetfreedom/russia-domains-list)

### 📊 Производные проекты
- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)

## 🙏 Благодарности

Огромное спасибо авторам следующих проектов:

### 🔹 v2fly
https://github.com/v2fly/domain-list-community  
Базовый проект geosite, на котором строится вся система правил.

### 🔹 runetfreedom
https://github.com/runetfreedom/russia-domains-list  
За списки доменов, доступных только внутри России.

### 🔹 Loyalsoldier
https://github.com/Loyalsoldier/v2ray-rules-dat  
За идеи и реализацию автоматической сборки.

### 🔹 Re-filter
https://github.com/1andrevich/Re-filter-lists  
За актуальные списки доменов.

### 🔹 Antifilter
https://community.antifilter.download  
За поддержку списков блокировок.

## ⚠️ Примечания

- `category-ads-all` используется в полностью развёрнутом виде, без include
- итоговый `geosite.dat` не содержит лишних промежуточных тегов
- списки оптимизированы для минимального потребления памяти
- рекомендуется использовать совместно с корректной DNS-настройкой

## 📄 Лицензия

Репозиторий агрегирует данные из сторонних источников.  
Лицензии и условия использования смотри в исходных проектах.
