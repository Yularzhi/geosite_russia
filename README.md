# geosite_russia

Кастомный `geosite.dat` для Xray / v2fly / совместимых клиентов (Happ, Sing-box и др.).

Репозиторий автоматически собирает облегчённый набор правил, оптимизированный для работы в России, с акцентом на:
- стабильную работу мессенджеров
- обход блокировок
- блокировку рекламы
- минимальное потребление памяти

---

## 📦 Состав

В итоговом `geosite.dat` доступны следующие теги:

- `custom-ru` — объединённый список (antifilter + refilter)
- `category-ads` — реклама (на основе upstream)
- `telegram`
- `viber`
- `whatsapp`
- `meta`
- `facebook`
- `google`
- `supercell`
- `roblox`

---

## ⬇️ Скачать

Актуальная версия:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat

Контрольная сумма:
https://raw.githubusercontent.com/yularzhi/geosite_russia/release/geosite.dat.sha256

---

## ⚙️ Использование

Подключите `geosite.dat` в клиенте (например Happ или Xray):

Примеры тегов:
geosite:custom-ru
geosite:category-ads
geosite:telegram
geosite:viber
geosite:whatsapp
geosite:meta
geosite:facebook
geosite:google
geosite:supercell
geosite:roblox

---

## 🎯 Цель проекта

Этот репозиторий создан как альтернатива тяжёлым спискам вроде:
geosite:ru-blocked

Проблема таких списков:
- высокий расход памяти (особенно на iOS)
- избыточность
- нестабильная работа некоторых сервисов (например Viber)

Решение:
- использовать облегчённый `custom-ru`
- разделить категории (ads, сервисы)
- сохранить контроль над маршрутизацией

---

## 🔄 Автоматизация

Репозиторий автоматически:

- скачивает исходные списки
- очищает и нормализует домены
- удаляет дубликаты
- объединяет данные
- генерирует `geosite.dat`
- публикует его в ветку `release`

Обновление происходит ежедневно через GitHub Actions.

---

## 📚 Источники

### Основной список (custom-ru)

Собран из:

- https://community.antifilter.download/list/domains.txt  
- https://github.com/1andrevich/Re-filter-lists  

---

### Категории сервисов и реклама

Используются данные проекта:

- https://github.com/v2fly/domain-list-community  

На его основе также построен:

- https://github.com/Loyalsoldier/v2ray-rules-dat  

---

## 🙏 Благодарности

Огромное спасибо следующим проектам и их авторам:

- **v2fly/domain-list-community**  
  https://github.com/v2fly/domain-list-community  
  (база для geosite)

- **Loyalsoldier/v2ray-rules-dat**  
  https://github.com/Loyalsoldier/v2ray-rules-dat  
  (реализация и идеи сборки)

- **Re-filter-lists**  
  https://github.com/1andrevich/Re-filter-lists  
  (списки доменов и фильтрация)

- **community.antifilter.download**  
  https://community.antifilter.download  
  (актуальные списки блокировок)

---

## ⚠️ Примечания

- `custom-ru` намеренно облегчён — это сделано для снижения нагрузки на устройства
- списки не претендуют на 100% полноту, но дают лучший баланс:
  - стабильность
  - скорость
  - память
- рекомендуется использовать совместно с корректной DNS-настройкой

---

## 📄 Лицензия

Обрати внимание: данный репозиторий агрегирует данные из сторонних источников.

Лицензии и условия использования смотри в исходных проектах.
