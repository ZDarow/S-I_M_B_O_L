/**
 * Интерактивный поиск и фильтрация DTC-кодов для Renault Symbol
 * Данные загружаются из data/dtc-codes.json
 * Полностью автономный виджет, не требует внешних зависимостей
 */
(function () {
  'use strict';

  // ─── Экранирование HTML (защита от XSS) ───────────────────────
  const esc = (s) => {
    const d = document.createElement('div');
    d.textContent = String(s ?? '');
    return d.innerHTML;
  };

  // ─── База данных DTC-кодов (загружается асинхронно) ──────────
  let DTC_DB = [];

  // ─── Системные метки ──────────────────────────────────────────
  const SYSTEM_LABELS = {
    engine: 'Двигатель',
    abs: 'ABS',
    srs: 'SRS (Airbag)',
    trans: 'Трансмиссия',
  };

  const SYSTEM_ICONS = {
    engine: '⚙️',
    abs: '🛞',
    srs: '🛡️',
    trans: '🔧',
  };

  // ─── Загрузка данных ──────────────────────────────────────────
  /** URL для загрузки JSON с DTC-кодами (относительный) */
  const DATA_URL =
    (typeof path_to_root !== 'undefined' ? path_to_root : '') + 'data/dtc-codes.json';

  /** Загрузить базу DTC-кодов из JSON */
  async function loadDtcData() {
    try {
      const response = await fetch(DATA_URL);
      if (!response.ok) {throw new Error('HTTP ' + response.status);}
      DTC_DB = await response.json();
      return true;
    } catch (err) {
      console.warn('DTC: Не удалось загрузить ' + DATA_URL, err);
      // Fallback: встроенный минимум
      DTC_DB = [
        {
          code: 'P0170',
          system: 'engine',
          cat: 'Топливо/воздух',
          desc: 'Коррекция смеси — выход за пределы',
          cause: 'Подсос воздуха, неисправность лямбда-зонда',
          fix: 'Диагностика топливной системы',
        },
        {
          code: 'P0300',
          system: 'engine',
          cat: 'Зажигание',
          desc: 'Случайные / множественные пропуски зажигания',
          cause: 'Свечи, катушка, компрессия',
          fix: 'Комплексная диагностика',
        },
        {
          code: 'C0001',
          system: 'abs',
          cat: 'ABS',
          desc: 'Датчик скорости левый передний',
          cause: 'Загрязнение датчика, обрыв проводки',
          fix: 'Чистка датчика, проверка зазора',
        },
      ];
      return false;
    }
  }

  // ─── Построение DOM ────────────────────────────────────────────
  function buildWidget(container) {
    // Контейнер
    const wrapper = document.createElement('div');
    wrapper.className = 'dtc-widget';
    wrapper.innerHTML = `
      <style>
        .dtc-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 1.5em 0; }
        .dtc-widget * { box-sizing: border-box; }
        .dtc-widget .dtc-header { background: var(--widget-header-bg, #e65100); color: var(--widget-header-text, #fff); padding: 1em 1.2em; border-radius: 8px 8px 0 0; }
        .dtc-widget .dtc-header h3 { margin: 0 0 0.3em; font-size: 1.2em; color: var(--widget-header-text, #fff); }
        .dtc-widget .dtc-header p { margin: 0; opacity: 0.9; font-size: 0.9em; }
        .dtc-widget .dtc-search-wrap { display: flex; gap: 0.5em; padding: 0.8em; background: var(--widget-search-bg, #f5f5f5); }
        .dtc-widget .dtc-input { flex: 1; padding: 0.7em 1em; border: 2px solid var(--widget-input-border, #ddd); border-radius: 6px; font-size: 1em; transition: border-color 0.2s; background: var(--widget-input-bg, #fff); color: var(--widget-input-text, #1a1a2e); }
        .dtc-widget .dtc-input:focus { border-color: var(--accent, #ff6b00); outline: 2px solid var(--accent, #ff6b00); outline-offset: 2px; }
        .dtc-widget .dtc-input.small { font-size: 0.85em; }
        .dtc-widget .dtc-clear { padding: 0.7em 1em; background: #aaa; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; }
        .dtc-widget .dtc-clear:hover { background: #888; }
        .dtc-widget .dtc-tabs { display: flex; flex-wrap: wrap; gap: 0.3em; padding: 0.5em 0.8em; background: #eee; border-bottom: 1px solid #ddd; }
        .dtc-widget .dtc-tab { padding: 0.4em 0.8em; border: 1px solid #ccc; border-radius: 4px; background: var(--widget-tab-bg, #fff); color: var(--widget-tab-text, #333); cursor: pointer; font-size: 0.85em; transition: all 0.2s; }
        .dtc-widget .dtc-tab:hover { background: var(--widget-tab-hover, #ffe0b2); }
        .dtc-widget .dtc-tab.active { background: var(--widget-tab-active-bg, #e65100); color: var(--widget-tab-active-text, #fff); border-color: var(--widget-tab-active-bg, #e65100); }
        .dtc-widget .dtc-count { margin-left: 0.3em; opacity: 0.7; font-size: 0.8em; }
        .dtc-widget .dtc-results { max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-top: 0; border-radius: 0 0 8px 8px; }
        .dtc-widget .dtc-item { padding: 0.8em 1em; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.15s; }
        .dtc-widget .dtc-item:last-child { border-bottom: 0; }
        .dtc-widget .dtc-item:hover { background: var(--widget-item-hover, #fff3e0); }
        .dtc-widget .dtc-item.hidden { display: none; }
        .dtc-widget .dtc-item-code { font-weight: 700; color: #d32f2f; font-size: 1.1em; }
        .dtc-widget .dtc-item-code .sys-badge { display: inline-block; font-size: 0.65em; padding: 0.15em 0.5em; border-radius: 3px; color: #fff; margin-left: 0.5em; vertical-align: middle; }
        .dtc-widget .dtc-item-code .sys-badge.engine { background: #d32f2f; }
        .dtc-widget .dtc-item-code .sys-badge.abs { background: #1565c0; }
        .dtc-widget .dtc-item-code .sys-badge.srs { background: #6a1b9a; }
        .dtc-widget .dtc-item-code .sys-badge.trans { background: #2e7d32; }
        .dtc-widget .dtc-item-cat { font-size: 0.8em; color: var(--widget-empty-color, #666); margin-top: 0.2em; }
        .dtc-widget .dtc-item-desc { margin-top: 0.3em; color: var(--fg-primary, #333); }
        .dtc-widget .dtc-item-detail { margin-top: 0.5em; padding: 0.5em 0.7em; background: var(--widget-detail-bg, #fafafa); border-left: 3px solid var(--accent, #ff6b00); border-radius: 0 4px 4px 0; display: none; font-size: 0.9em; }
        .dtc-widget .dtc-item-detail.open { display: block; }
        .dtc-widget .dtc-item-detail dt { font-weight: 600; color: var(--warning, #e65100); margin-top: 0.4em; }
        .dtc-widget .dtc-item-detail dt:first-child { margin-top: 0; }
        .dtc-widget .dtc-item-detail dd { margin: 0.2em 0 0 0.5em; }
        .dtc-widget .dtc-empty { padding: 2em; text-align: center; color: var(--widget-empty-color, #666); font-style: italic; }
        .dtc-widget .dtc-loading { padding: 2em; text-align: center; color: var(--widget-loading-color, #666); }
        @media (prefers-color-scheme: dark) {
          .dtc-widget .dtc-search-wrap { background: var(--widget-search-bg, #333); }
          .dtc-widget .dtc-input { background: var(--widget-input-bg, #444); color: var(--widget-input-text, #eee); border-color: var(--widget-input-border, #555); }
          .dtc-widget .dtc-tabs { background: #2a2a2a; border-bottom-color: #444; }
          .dtc-widget .dtc-tab { background: var(--widget-tab-bg, #444); color: var(--widget-tab-text, #ddd); border-color: #555; }
          .dtc-widget .dtc-tab:hover { background: var(--widget-tab-hover, #664); }
          .dtc-widget .dtc-results { border-color: #444; }
          .dtc-widget .dtc-item { border-bottom-color: #333; }
          .dtc-widget .dtc-item:hover { background: var(--widget-item-hover, #3a3020); }
          .dtc-widget .dtc-item-desc { color: #ccc; }
          .dtc-widget .dtc-item-detail { background: var(--widget-detail-bg, #2a2a2a); }
          .dtc-widget .dtc-empty { color: var(--widget-empty-color, #aaa); }
          .dtc-widget .dtc-loading { color: var(--widget-loading-color, #aaa); }
        }
      </style>
      <div class="dtc-header">
        <h3>🔍 Поиск DTC-кодов</h3>
        <p>Введите код неисправности (P0170) или ключевое слово (лямбда, ABS, пропуски)</p>
      </div>
      <div class="dtc-search-wrap">
        <input class="dtc-input" type="text" id="dtc-query" placeholder="Поиск по коду или описанию..." autocomplete="off">
        <button class="dtc-clear" id="dtc-clear-btn">✕</button>
      </div>
      <div class="dtc-tabs" id="dtc-tabs"></div>
      <div class="dtc-results" id="dtc-results" aria-live="polite" aria-atomic="true"></div>
    `;
    container.appendChild(wrapper);

    const queryInput = wrapper.querySelector('#dtc-query');
    const clearBtn = wrapper.querySelector('#dtc-clear-btn');
    const tabsEl = wrapper.querySelector('#dtc-tabs');
    const resultsEl = wrapper.querySelector('#dtc-results');

    let activeSystem = 'all';
    let searchQuery = '';

    // ─── Фильтрация ────────────────────────────────────────────────
    function getFiltered() {
      let items = DTC_DB;
      if (activeSystem !== 'all') {
        items = items.filter((d) => d.system === activeSystem);
      }
      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        items = items.filter(
          (d) =>
            d.code.toLowerCase().includes(q) ||
            d.desc.toLowerCase().includes(q) ||
            d.cause.toLowerCase().includes(q) ||
            d.fix.toLowerCase().includes(q) ||
            d.cat.toLowerCase().includes(q),
        );
      }
      return items;
    }

    // ─── Подсчёт по системам ────────────────────────────────────────
    function countBySystem() {
      const counts = { all: DTC_DB.length };
      for (const key in SYSTEM_LABELS) {
        counts[key] = DTC_DB.filter((d) => d.system === key).length;
      }
      return counts;
    }

    // ─── Рендер вкладок ─────────────────────────────────────────────
    function renderTabs() {
      const counts = countBySystem();
      const renderTab = (sys, label) => {
        const icon = SYSTEM_ICONS[sys] || '';
        return `<button class="dtc-tab${activeSystem === sys ? ' active' : ''}" data-system="${esc(sys)}">${icon} ${esc(label)} <span class="dtc-count">${counts[sys] ?? 0}</span></button>`;
      };
      const html = [renderTab('all', 'Все')];
      for (const [key, label] of Object.entries(SYSTEM_LABELS)) {
        html.push(renderTab(key, label));
      }
      tabsEl.innerHTML = html.join('');

      tabsEl.querySelectorAll('.dtc-tab').forEach((btn) => {
        btn.addEventListener('click', function () {
          activeSystem = this.dataset.system;
          renderTabs();
          renderResults();
        });
      });
    }

    // ─── Рендер результатов ─────────────────────────────────────────
    function renderResults() {
      const items = getFiltered();
      if (items.length === 0) {
        resultsEl.innerHTML =
          '<div class="dtc-empty">По вашему запросу ничего не найдено. Попробуйте другой код или ключевое слово.</div>';
        return;
      }

      let html = '';
      for (const d of items) {
        const sysLabel = SYSTEM_LABELS[d.system] || d.system;
        html += '<div class="dtc-item" data-code="' + esc(d.code) + '">';
        html +=
          '  <div class="dtc-item-code">' +
          esc(d.code) +
          ' <span class="sys-badge ' +
          esc(d.system) +
          '">' +
          esc(sysLabel) +
          '</span></div>';
        html += '  <div class="dtc-item-cat">' + esc(d.cat) + '</div>';
        html += '  <div class="dtc-item-desc">' + esc(d.desc) + '</div>';
        html += '  <div class="dtc-item-detail">';
        html += '    <dl>';
        html += '      <dt>🔍 Причина</dt><dd>' + esc(d.cause) + '</dd>';
        html += '      <dt>✅ Решение</dt><dd>' + esc(d.fix) + '</dd>';
        html += '    </dl>';
        html += '  </div>';
        html += '</div>';
      }
      resultsEl.innerHTML = html;

      // Клик по элементу — разворачиваем детали
      resultsEl.querySelectorAll('.dtc-item').forEach((el) => {
        el.addEventListener('click', function (e) {
          const detail = this.querySelector('.dtc-item-detail');
          if (detail) {
            const wasOpen = detail.classList.contains('open');
            resultsEl
              .querySelectorAll('.dtc-item-detail.open')
              .forEach((d) => d.classList.remove('open'));
            if (!wasOpen) {
              detail.classList.add('open');
            }
          }
        });
      });
    }

    // ─── Обработчики поиска ─────────────────────────────────────────
    // Дебаунс-таймер для поиска (200ms)
    let debounceTimer = null;
    queryInput.addEventListener('input', function () {
      searchQuery = this.value;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(renderResults, 200);
    });

    clearBtn.addEventListener('click', function () {
      queryInput.value = '';
      searchQuery = '';
      renderResults();
      queryInput.focus();
    });

    // ─── Инициализация ──────────────────────────────────────────────
    resultsEl.innerHTML = '<div class="dtc-loading">Загрузка базы DTC-кодов…</div>';
    renderTabs();
    loadDtcData().then(() => {
      renderTabs();
      renderResults();
    });
  }

  // ─── Условный запуск ─────────────────────────────────────────
  // Виджет рендерится ТОЛЬКО если на странице есть контейнер #dtc-widget
  // (вручную размещённый в Markdown). Авто-вставка отсутствует.
  function init() {
    const container = document.getElementById('dtc-widget');
    if (!container) return;
    buildWidget(container);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
