# geosite_russia

Кастомный geosite.dat для Xray / Sing-box / Happ и других клиентов.

Основная цель проекта — создать лёгкий и эффективный набор доменных правил для работы в России:
- обход блокировок
- стабильная работа сервисов
- минимальное потребление памяти
- чистая и понятная структура

## 📦 Состав

В итоговом geosite.dat доступны следующие теги:

🚀 Основной список
ru-blocked — объединённый список:
- community.antifilter.download
- Loyalsoldier surge-rules (proxy.txt)
- из proxy.txt удалены домены из category-ru

Покрывает:
- заблокированные сайты
- международные сервисы
- ресурсы, требующие проксирования
- без российских доменов

🇷🇺 Российские ресурсы
category-ru — официальный список российских доменов из v2fly

🚫 Реклама
category-ads-all — полный список рекламы (развёрнутый, без include)

📱 Сервисы
telegram
viber (расширен доменами Rakuten)
whatsapp
meta
facebook
google
supercell
roblox

🔒 Системные
private — локальные сети и приватные домены

## ⬇️ Скачать

Актуальная версия:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat

SHA256:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat.sha256

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

- скачиваются исходные списки
- нормализуются домены
- объединяются списки
- из proxy.txt исключаются домены category-ru
- разворачиваются include зависимости
- генерируется geosite.dat
- публикуется в ветку release

Обновление происходит ежедневно.

## 📊 Особенности

- оптимизировано под низкое потребление памяти (~20–30 MB)
- proxy.txt используется в очищенном виде (без RU доменов)
- отсутствуют лишние и дублирующие списки
- все зависимости разворачиваются в плоский вид
- полный контроль над составом списков

## 📚 Источники

Основные:
https://community.antifilter.download
https://github.com/Loyalsoldier/surge-rules

Upstream:
https://github.com/v2fly/domain-list-community

Производные проекты:
https://github.com/Loyalsoldier/v2ray-rules-dat

## 🙏 Благодарности

v2fly  
https://github.com/v2fly/domain-list-community  
Базовый проект geosite

Loyalsoldier  
https://github.com/Loyalsoldier/v2ray-rules-dat  
Идеи сборки и структура

surge-rules  
https://github.com/Loyalsoldier/surge-rules  
Источник proxy.txt

Antifilter  
https://community.antifilter.download  
Список заблокированных доменов

## ⚠️ Примечания

- ru-blocked — кастомный список (proxy.txt - category-ru + antifilter)
- российские домены исключаются из proxy автоматически
- viber расширен доменами Rakuten
- category-ads-all используется в полном развёрнутом виде
- итоговый файл не содержит промежуточных тегов

## 📄 Лицензия

Репозиторий агрегирует данные из сторонних источников.  
Смотри лицензии в оригинальных проектах.

## 💬 Обратная связь

Pull request'ы и идеи приветствуются.
