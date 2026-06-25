# Ресурсы для развития проекта Renault Symbol Manual

## 1. Текстовые материалы

| № | Ресурс | Тип | Лицензия | Интеграция |
|---|--------|-----|----------|------------|
| 1 | [youfixcars.com Renault Symbol](https://youfixcars.com/auto-service-repair-manual/Renault/Symbol) | Сервис-мануал PDF | Платный (ориентир структуры) | Использовать как референс для недостающих разделов: тормозная система, рулевое, кондиционер |
| 2 | [free-auto-repair-manuals.com – Symbol](https://free-auto-repair-manuals.com/renault-symbol-repair-manual/) | Бесплатные PDF | Freeware (личное пользование) | Сверить схемы электрооборудования (`8-5.md`) и моменты затяжки (`momenty.md`) |
| 3 | [carmanualsonline.info – Renault](https://www.carmanualsonline.info/b/renault/3) | 285 PDF мануалов | Бесплатно онлайн | Пополнить разделы `expluataciya/` (интервалы ТО, жидкости) из официальных руководств |
| 4 | [workshopmanuals.org – Symbol](https://workshopmanuals.org/product/renault-symbol-manual/) | Dealer-level manual | Платный ($14.99) | Диагностические коды ошибок, электропроцедуры — дополнить `8-5.md` |
| 5 | [onlymanuals.com – Symbol](https://www.onlymanuals.com/renault/symbol) | 2 PDF (сервис + владелец) | Условно-бесплатно | Описание приборной панели, предупреждающие лампы → `faq.md` |

## 2. Визуальные ресурсы (открытые лицензии)

### SVG-иконки (автомобильная тематика)

| № | Ресурс | Кол-во | Лицензия | Идея |
|---|--------|--------|----------|------|
| 1 | [Iconduck – SSJB Map Icons](https://iconduck.com/icons/160989/car-repair) | 298 иконок | **CC0** | Иконки для каждого раздела: `🔧 двигатель` → `⚙ трансмиссия` → `🔌 электрика`. Встроить через кастомный theme/index.hbs |
| 2 | [OpenIconLibrary.com](https://openiconlibrary.com) | 2000+ | CC0 / MIT | Универсальные иконки документации: поиск, принт, скачать, тултипы |
| 3 | [Iconoir.com](https://iconoir.com) | 1300+ | **MIT** | Иконки навигации: стрелки, гамбургер, закрыть, оглавление |
| 4 | [Flaticon – Car Repair](https://www.flaticon.com/free-icons/car-repair) | 14000+ | Free с attribution | Фотореалистичные иконки двигателя, АКБ, масла, тормозов |
| 5 | [cc0-icons/cc0-icons (GitHub)](https://github.com/cc0-icons/cc0-icons) | ~50 | **CC0** | Установка/обслуживание, инструменты |
| 6 | [Humaaans / Open Peeps](https://allsvgicons.com/cc0-illustrations/) | CC0 | **CC0** | Иллюстрации людей для раздела "Безопасность" (домкрат, поддомкрачивание) |

### Шрифты (кириллица)

| № | Ресурс | Лицензия | Идея |
|---|--------|----------|------|
| 1 | [Google Fonts – Inter](https://fonts.google.com/specimen/Inter) | **OFL** | Основной шрифт документации (кириллица, отличная читаемость) |
| 2 | [Google Fonts – JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | **OFL** | Моноширинный для кода, схем, таблиц с данными |
| 3 | [Google Fonts – Onest](https://fonts.google.com/specimen/Onest) | **OFL** | Современный кириллический гротеск, альтернатива Inter |

## 3. Мок-данные / Датасеты

| № | Ресурс | Тип | Лицензия | Идея |
|---|--------|-----|----------|------|
| 1 | [vehicle-json (GitHub)](https://github.com/topics/vehicle-database) | JSON | Разная | Тестовые данные автомобилей для валидации: марка/модель/год/двигатель |
| 2 | [CARLA dataset (Microsoft)](https://github.com/microsoft/carla) | Simulation | **MIT** | 3D-модели автомобилей, датчики — для иллюстраций положения датчиков |
| 3 | [OBD-II JSON PIDs](https://github.com/topics/obd) | JSON | MIT/Unlicense | PID-коды OBD-II для раздела диагностики (`elektrika/8-5.md`) |
| 4 | [cars.json (rozochkin)](https://gist.github.com/rozochkin) | JSON | Public Domain | Тестовый JSON каталога марок/моделей для демо-данных портативной версии |
| 5 | [OpenAPI Car API](https://github.com/topics/car-api) | OpenAPI/Swagger | MIT | API-спецификация для мок-сервера — если делать поиск по запчастям |

### Генерация своих мок-данных

```python
# scripts/mock_torque_data.py — заглушка для momenty.md
mock_torque = {
    "ГБЦ": {"Symbol I 1.4": "25 Н·м + 180°", "Symbol II 1.4": "20 Н·м + 200°"},
    "Свечи зажигания": {"K7J 1.4": "25 Н·м", "K4J 1.6": "28 Н·м"},
    "Колёсные болты": {"Все": "90 Н·м (M12×1.5)"},
}
```

## 4. Тренды оформления техдокументации

| № | Тренд | Описание | Интеграция в проект |
|---|-------|----------|---------------------|
| 1 | **mdBook кастомный theme** | Переопределить `theme/index.hbs`, `theme/css/general.css`, `theme/css/chrome.css` | Стиль под руководство по ремонту: цветовая схема (оранжевый/серый Renault), увеличенный шрифт, автомобильные иконки в сайдбаре |
| 2 | **Мобильная адаптация** | mdBook по умолчанию адаптивен, но таблицы часто ломаются | Обернуть таблицы в `<div class="table-wrapper">`, настроить `overflow-x: auto` в кастомном CSS |
| 3 | **Mermaid-схемы** | Блок-схемы, графы, Gantt | Заменить ASCII-схемы в `elektrika/` на интерактивные Mermaid (уже настроен `mermaid-preprocess.py`) |
| 4 | **Collapsible секции** | `<details><summary>` для вложенной информации | Применить в `momenty.md` (развернуть таблицу по клику) и `faq.md` (ответ под вопросом) |
| 5 | **Интерактивные торки / затяжка** | visual torque wrenches | Анимированная иллюстрация динамометрического ключа в `momenty.md` (SVG + CSS анимация) |
| 6 | **Search + авто-дополнение** | mdBook встроенный Elasticlunr.js | Настроить `search.js` для токенизации русских слов (через `--zh` тонер не нужен, нужна кастомная сегментация) |
| 7 | **Светлая/тёмная тема** | CSS Variables + `prefers-color-scheme` | Кастомный `theme.css` с `--bg`, `--fg`, `--accent` под ночной режим для чтения в гараже |
| 8 | **Print-friendly CSS** | `@media print` | Скрыть навбар, подвал, увеличить шрифт при печати. `scripts/pdf-a4.py` — уже есть |
| 9 | **Бейджи статуса раздела** | Markdown badges | `![Готово](https://img.shields.io/badge/status-готово-green)` для `README.md` и оглавления |

## Приоритет внедрения

### Высокий (сделать в первую очередь)
1. Кастомный theme mdBook (брендирование Renault, иконки разделов)
2. Collapsible FAQ (`faq.md` с `<details>`)
3. Тёмная тема (CSS Variables)
4. Mobile-first таблицы (`div.table-wrapper`)

### Средний
5. Mermaid-схемы для `elektrika/8-5.md`
6. Print-friendly CSS
7. Бейджи статуса разделов

### Низкий (опционально)
8. Мок-данные для моментов затяжки (автотесты)
9. OBD-II PID-коды в разделе диагностики
10. API car-data для поиска

## Быстрый старт: кастомная тема

```bash
# Извлечь дефолтную тему mdBook
mdbook init --theme book
cp -r book/theme .kilo/theme-default

# Создать кастомную
mkdir -p book/theme/css
cat > book/theme/css/renault.css << 'CSS'
:root {
  --bg: #1a1a2e;
  --fg: #e0e0e0;
  --accent: #ff6b00;
  --sidebar-bg: #16213e;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --fg: #333333;
    --accent: #cc5500;
    --sidebar-bg: #f8f9fa;
  }
}
CSS
```
