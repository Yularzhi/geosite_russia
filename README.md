# geosite_russia

Кастомный `geosite.dat` для Xray / v2fly / Sing-box / Happ и других клиентов.

Репозиторий автоматически собирает оптимизированный набор правил для работы в России с акцентом на:
- обход блокировок
- корректную блокировку рекламы
- стабильную работу популярных сервисов
- минимальное потребление памяти

## 📦 Состав

В итоговом `geosite.dat` доступны следующие теги:

### 🇷🇺 Основной список
- `ru-blocked` — объединённый список:
  - `community.antifilter.download`
  - `gfw.txt` от Loyalsoldier

### 🇷🇺 Российские ресурсы
- `category-ru` — официальный upstream список российских доменов из `v2fly/domain-list-community`

### 🚫 Реклама
- `category-ads-all` — официальный список рекламы из `domain-list-community`, развёрнутый в плоский вид

### 🔒 Системные
- `private` — локальные и приватные сети / домены

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

- `geosite:ru-blocked`
- `geosite:category-ru`
- `geosite:category-ads-all`
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
- `geosite:ru-blocked`
- `geosite:telegram`
- `geosite:viber`
- `geosite:whatsapp`
- `geosite:meta`
- `geosite:google`

### Direct
- `geosite:private`
- `geosite:category-ru`

### Block
- `geosite:category-ads-all`

## 🔄 Автоматизация

Репозиторий автоматически:
- скачивает исходные списки
- очищает и нормализует `ru-blocked`
- подтягивает upstream-теги
- разворачивает зависимости
- генерирует `geosite.dat`
- публикует результат в ветку `release`

Обновление выполняется ежедневно через GitHub Actions.

## 📚 Источники

### 🇷🇺 Основной список
- [community.antifilter.download](https://community.antifilter.download/list/domains.txt)
- [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)

### 📦 Upstream geosite
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)

### 📊 Производные проекты
- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)

## 🙏 Благодарности

Огромное спасибо авторам следующих проектов:

### 🔹 v2fly
https://github.com/v2fly/domain-list-community  
Базовый проект geosite, на котором строится вся система правил.

### 🔹 Loyalsoldier
https://github.com/Loyalsoldier/v2ray-rules-dat  
За идеи сборки и удобную экосистему правил.

### 🔹 Loyalsoldier surge-rules
https://github.com/Loyalsoldier/surge-rules  
За текстовый `gfw.txt`, который используется в сборке `ru-blocked`.

### 🔹 Antifilter
https://community.antifilter.download  
За поддержку списков доменов, используемых для обхода блокировок.

## ⚠️ Примечания

- `ru-blocked` — это кастомный тег, собранный из `antifilter` и `gfw`
- `category-ru` и сервисные теги берутся из upstream `v2fly/domain-list-community`
- `category-ads-all` используется в развёрнутом виде
- итоговый `geosite.dat` не содержит лишних промежуточных тегов
- список оптимизирован под снижение потребления памяти

## 📄 Лицензия

Репозиторий агрегирует данные из сторонних источников.  
Лицензии и условия использования смотри в исходных проектах.

## 💬 Обратная связь

Если хочешь улучшить списки или добавить новые категории — создавай issue или pull request.
