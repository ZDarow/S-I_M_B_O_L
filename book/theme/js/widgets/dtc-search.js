/**
 * @file Рефакторенный виджет поиска DTC-кодов.
 * Логика загрузки/фильтрации отделена от представления через html-шаблоны.
 * Состояние хранится в замыкании, рендер — через renderer.html.
 *
 * @module widgets/dtc-search
 */

import { html, Show, render } from '../core/renderer.js';

// ─── Системные метки ──────────────────────────────────────────────

/** @type {Record<string, string>} */
const SYSTEM_LABELS = {
  engine: 'Двигатель',
  abs: 'ABS',
  srs: 'SRS (Airbag)',
  trans: 'Трансмиссия',
};

/** @type {Record<string, string>} */
const SYSTEM_ICONS = {
  engine: '⚙️',
  abs: '🛞',
  srs: '🛡️',
  trans: '🔧',
};

/** @type {Record<string, string>} */
const SYSTEM_COLORS = {
  engine: '#d32f2f',
  abs: '#1565c0',
  srs: '#6a1b9a',
  trans: '#2e7d32',
};

/** @type {import('../core/renderer.js').DTCCode[]} */
const FALLBACK_DB = [
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

// ─── Загрузчик данных ─────────────────────────────────────────────

/**
 * @returns {{ load: (url: string) => Promise<boolean>, db: import('../core/renderer.js').DTCCode[], loaded: boolean }}
 */
function createDataLoader() {
  /** @type {import('../core/renderer.js').DTCCode[]} */
  let db = [];
  let loaded = false;

  return {
    get db() {
      return db;
    },
    get loaded() {
      return loaded;
    },

    /** Загрузить базу из JSON. */
    async load(dataUrl) {
      if (loaded) {
        return true;
      }
      try {
        const resp = await fetch(dataUrl);
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }
        db = await resp.json();
        loaded = true;
        return true;
      } catch (err) {
        console.warn('[DTC] Не удалось загрузить', dataUrl, err);
        db = FALLBACK_DB;
        loaded = true;
        return false;
      }
    },
  };
}

// ─── Фильтр ────────────────────────────────────────────────────────

/**
 * Отфильтровать массив DTC-кодов.
 * @param {import('../core/renderer.js').DTCCode[]} items
 * @param {string} query
 * @param {string} system
 * @returns {import('../core/renderer.js').DTCCode[]}
 */
function filterCodes(items, query, system) {
  let result = items;
  if (system !== 'all') {
    result = result.filter((d) => d.system === system);
  }
  const q = query.trim().toLowerCase();
  if (q) {
    result = result.filter(
      (d) =>
        d.code.toLowerCase().includes(q) ||
        d.desc.toLowerCase().includes(q) ||
        d.cause.toLowerCase().includes(q) ||
        d.fix.toLowerCase().includes(q) ||
        d.cat.toLowerCase().includes(q),
    );
  }
  return result;
}

/**
 * Подсчёт записей по системам.
 * @param {import('../core/renderer.js').DTCCode[]} db
 * @returns {Record<string, number>}
 */
function countBySystem(db) {
  /** @type {Record<string, number>} */
  const counts = { all: db.length };
  for (const key of Object.keys(SYSTEM_LABELS)) {
    counts[key] = db.filter((d) => d.system === key).length;
  }
  return counts;
}

// ─── Функции рендеринга (чистые, без состояния) ───────────────────

/**
 * Рендер вкладки системы.
 * @param {string} sys
 * @param {string} label
 * @param {string} active
 * @param {number} count
 * @param {(sys: string) => void} onSelect
 * @returns {DocumentFragment}
 */
function renderTab(sys, label, active, count, onSelect) {
  const icon = SYSTEM_ICONS[sys] || '';
  return html`
    <button
      class="dtc-tab ${active === sys ? 'active' : ''}"
      role="tab"
      aria-selected=${String(active === sys)}
      data-system=${sys}
      onclick=${() => onSelect(sys)}
    >
      ${icon} ${label}
      <span class="dtc-count">${count}</span>
    </button>
  `;
}

/**
 * Рендер карточки одного DTC-кода.
 * @param {import('../core/renderer.js').DTCCode & { open: boolean }} props
 * @param {(code: string) => void} onToggle
 * @returns {DocumentFragment}
 */
function renderDtcItem(props, onToggle) {
  const { code, system, cat, desc, cause, fix, open } = props;
  const sysLabel = SYSTEM_LABELS[system] || system;
  const sysColor = SYSTEM_COLORS[system] || '#888';

  return html`
    <div
      class="dtc-item"
      data-code=${code}
      role="button"
      tabindex="0"
      aria-expanded=${String(open)}
      onclick=${() => onToggle(code)}
      onkeydown=${(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle(code);
        }
      }}
    >
      <div class="dtc-item-code">
        ${code}
        <span class="sys-badge" style="background:${sysColor}">${sysLabel}</span>
      </div>
      <div class="dtc-item-cat">${cat}</div>
      <div class="dtc-item-desc">${desc}</div>
      <div class="dtc-item-detail ${open ? 'open' : ''}" role="region">
        <dl>
          <dt>🔍 Причина</dt>
          <dd>${cause}</dd>
          <dt>✅ Решение</dt>
          <dd>${fix}</dd>
        </dl>
      </div>
    </div>
  `;
}

/**
 * Рендер всего виджета DTC-поиска.
 * @param {Object} state
 * @param {import('../core/renderer.js').DTCCode[]} state.db
 * @param {boolean} state.loading
 * @param {string} state.query
 * @param {string} state.activeSystem
 * @param {string|null} state.openCode
 * @param {(query: string) => void} onQueryChange
 * @param {() => void} onClear
 * @param {(sys: string) => void} onSystemChange
 * @param {(code: string) => void} onToggleCode
 * @returns {DocumentFragment}
 */
function renderWidget(state, onQueryChange, onClear, onSystemChange, onToggleCode) {
  const { db, loading, query, activeSystem, openCode } = state;
  const filtered = loading ? [] : filterCodes(db, query, activeSystem);
  const counts = loading ? {} : countBySystem(db);

  return html`
    <div class="dtc-widget" role="region" aria-label="Поиск DTC-кодов">
      <div class="dtc-header">
        <h3>🔍 Поиск DTC-кодов</h3>
        <p>Введите код неисправности (P0170) или ключевое слово</p>
      </div>
      <div class="dtc-search-wrap">
        <input
          class="dtc-input"
          type="text"
          placeholder="Поиск по коду или описанию..."
          value=${query}
          autocomplete="off"
          oninput=${(e) => onQueryChange(/** @type {HTMLInputElement} */ (e.target).value)}
          onkeydown=${(e) => {
            if (e.key === 'Escape') {
              onClear();
            }
          }}
          aria-label="Поиск DTC-кодов"
        />
        <button class="dtc-clear" onclick=${onClear} aria-label="Очистить поиск">✕</button>
      </div>

      <div class="dtc-tabs" role="tablist" aria-label="Системы">
        ${renderTab('all', 'Все', activeSystem, counts.all || 0, onSystemChange)}
        ${Object.entries(SYSTEM_LABELS).map(([key, label]) =>
          renderTab(key, label, activeSystem, counts[key] || 0, onSystemChange),
        )}
      </div>

      <div class="dtc-results" aria-live="polite" aria-atomic="true" role="list">
        ${Show(
          loading,
          () => html`<div class="dtc-loading">Загрузка базы DTC-кодов…</div>`,
          () =>
            Show(
              filtered.length === 0,
              () => html`<div class="dtc-empty">По вашему запросу ничего не найдено.</div>`,
              () => html`
                ${filtered.map(
                (d) => html`
                  <div class="dtc-item-wrap" role="listitem">
                    ${renderDtcItem({ ...d, open: openCode === d.code }, onToggleCode)}
                  </div>
                `,
              )}
              `,
            ),
        )}
      </div>
    </div>
  `;
}

// ─── Создание виджета ─────────────────────────────────────────────

/**
 * Создать экземпляр DTC-виджета.
 * @param {string} [dataUrl]  URL к dtc-codes.json
 * @returns {{ mount: (container: HTMLElement) => void, unmount: () => void }}
 */
export function createDtcSearch(dataUrl) {
  const loader = createDataLoader();
  /** @type {string} */
  const rootPath = (typeof window !== 'undefined' && window.__mdbook_path_to_root) || '';
  const url = dataUrl || rootPath + 'data/dtc-codes.json';

  /** @type {HTMLElement|null} */
  let container = null;

  // Состояние
  const state = {
    db: /** @type {import('../core/renderer.js').DTCCode[]} */ ([]),
    loading: true,
    query: '',
    activeSystem: 'all',
    openCode: /** @type {string|null} */ (null),
  };

  /** Обновить рендер. */
  function update() {
    if (!container) {
      return;
    }
    const frag = renderWidget(
      state,
      (q) => {
        state.query = q;
        state.openCode = null;
        update();
      },
      () => {
        state.query = '';
        state.openCode = null;
        update();
      },
      (sys) => {
        state.activeSystem = sys;
        state.openCode = null;
        update();
      },
      (code) => {
        state.openCode = state.openCode === code ? null : code;
        update();
      },
    );
    render(container, frag);
  }

  return {
    /**
     * Смонтировать виджет в контейнер.
     * @param {HTMLElement} el
     */
    mount(el) {
      container = el;
      update();
      loader.load(url).then(() => {
        state.loading = false;
        state.db = loader.db;
        update();
      });
    },

    /** Демонтировать виджет. */
    unmount() {
      if (container) {
        container.innerHTML = '';
        container = null;
      }
    },
  };
}

/**
 * Инициализировать DTC-виджет для страницы.
 * Ищет контейнер #dtc-widget или создаёт его.
 * @param {string} [dataUrl]
 * @returns {Function} Функция очистки
 */
export function initDtcSearch(dataUrl) {
  // Ищем или создаём контейнер — только если legacy-виджет ещё не запустился
  let container = document.getElementById('dtc-widget');
  if (container && container.querySelector('.dtc-widget')) {
    // Уже есть виджет (возможно, сработал legacy-скрипт) — не дублируем
    return () => {};
  }

  if (!container) {
    const content = document.querySelector('.content, article, main');
    if (content) {
      container = document.createElement('div');
      container.id = 'dtc-widget';
      const firstH = content.querySelector('h1, h2');
      if (firstH && firstH.parentNode === content) {
        firstH.insertAdjacentElement('afterend', container);
      } else {
        content.insertBefore(container, content.firstChild);
      }
    } else {
      container = document.createElement('div');
      container.id = 'dtc-widget';
      document.body.insertBefore(container, document.body.firstChild);
    }
  }

  const widget = createDtcSearch(dataUrl);
  widget.mount(container);

  return () => {
    widget.unmount();
  };
}

export default { initDtcSearch, createDtcSearch };
