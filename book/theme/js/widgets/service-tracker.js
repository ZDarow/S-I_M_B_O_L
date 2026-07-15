/**
 * @file Рефакторенный виджет планировщика ТО для Renault Symbol.
 * Логика расчёта и localStorage отделены от представления.
 *
 * @module widgets/service-tracker
 */

import { html, Show, render } from '../core/renderer.js';

// ─── Регламент ТО ─────────────────────────────────────────────────

/** @type {import('../core/renderer.js').ServiceScheduleEntry[]} */
const serviceSchedule = [
  {
    km: 0,
    years: 0,
    label: '0 км — Подготовка к эксплуатации',
    items: [
      'Проверка уровней всех жидкостей',
      'Регулировка давления в шинах',
      'Проверка световых приборов',
    ],
    critical: false,
  },
  {
    km: 15000,
    years: 1,
    label: '15 000 км / 1 год — ТО-1',
    items: [
      'Моторное масло + масляный фильтр',
      'Проверка ремня ГРМ',
      'Проверка тормозных колодок',
      'Проверка ШРУСов',
      'Проверка выхлопной системы',
    ],
    critical: true,
  },
  {
    km: 30000,
    years: 2,
    label: '30 000 км / 2 года — ТО-2',
    items: [
      'Всё из ТО-1',
      'Свечи зажигания (замена)',
      'Салонный фильтр',
      'Воздушный фильтр',
      'Смазка замков и петель',
      'Проверка рулевых наконечников',
    ],
    critical: true,
  },
  {
    km: 40000,
    years: 2,
    label: '40 000 км / 2 года',
    items: [
      'Тормозная жидкость DOT 4 (замена)',
      'Проверка амортизаторов',
      'Проверка сайлент-блоков',
    ],
    critical: true,
  },
  {
    km: 60000,
    years: 4,
    label: '60 000 км / 4 года — ТО-3',
    items: [
      'Всё из ТО-2',
      'Ремень ГРМ + натяжной ролик + помпа',
      'Антифриз (замена)',
      'Масло в МКПП',
      'Топливный фильтр (дизель)',
      'Проверка ремня генератора',
      'Проверка тормозных дисков',
    ],
    critical: true,
  },
  {
    km: 90000,
    years: 6,
    label: '90 000 км / 6 лет',
    items: ['Ремень ГРМ (дизель K9K)', 'Проверка турбины (дизель)'],
    critical: true,
  },
  {
    km: 120000,
    years: 8,
    label: '120 000 км — ТО-4',
    items: [
      'Ремень ГРМ повторно + помпа',
      'Топливный фильтр (бензин)',
      'Передние амортизаторы',
      'Сайлент-блоки рычагов',
      'Рулевые наконечники',
      'Проверка глушителя',
    ],
    critical: true,
  },
  {
    km: 150000,
    years: 10,
    label: '150 000+ км',
    items: ['Сцепление (комплект)', 'Задние амортизаторы', 'Ступичные подшипники'],
    critical: false,
  },
];

const STORAGE_KEY = 'renault_symbol_service_history';
const STATE_KEY = 'renault_service_state';

// ─── Хранилище данных ────────────────────────────────────────────

/**
 * @template T
 * @param {string} key
 * @param {T} fallback
 * @returns {T}
 */
function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

/**
 * @param {string} key
 * @param {*} value
 */
function saveJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage недоступен
  }
}

/**
 * @returns {{ mileage: number, lastService: number }}
 */
function loadState() {
  return loadJSON(STATE_KEY, { mileage: 0, lastService: 0 });
}

/**
 * @param {{ mileage: number, lastService: number }} s
 */
function persistState(s) {
  saveJSON(STATE_KEY, s);
}

/**
 * @returns {import('../core/renderer.js').ServiceHistoryEntry[]}
 */
function loadHistory() {
  return loadJSON(STORAGE_KEY, []);
}

/**
 * @param {import('../core/renderer.js').ServiceHistoryEntry[]} h
 */
function saveHistory(h) {
  saveJSON(STORAGE_KEY, h);
}

// ─── Расчётная логика ────────────────────────────────────────────

/**
 * Рассчитать статус ТО.
 * @param {import('../core/renderer.js').ServiceScheduleEntry} entry
 * @param {number} currentMileage
 * @param {number} lastServiceKm
 * @param {Set<number>} doneKmSet
 * @returns {{ status: string, statusText: string, nextKm: number, dueDistance: number }}
 */
function calcServiceStatus(entry, currentMileage, lastServiceKm, doneKmSet) {
  const nextKm = lastServiceKm > 0 ? lastServiceKm + entry.km : entry.km;
  const dueDistance = Math.max(0, nextKm - currentMileage);
  const isDone = doneKmSet.has(entry.km);

  let status;
  let statusText;

  if (isDone) {
    status = 'done';
    statusText = '✅ Выполнено';
  } else if (nextKm <= currentMileage) {
    status = 'overdue';
    statusText = '❗ Просрочено';
  } else if (dueDistance <= 5000) {
    status = 'due-soon';
    statusText = '⚠️ Скоро';
  } else {
    status = 'pending';
    statusText = 'Ок';
  }

  return { status, statusText, nextKm, dueDistance };
}

// ─── Функции рендеринга ──────────────────────────────────────────

/**
 * Рендер карточки одного ТО.
 * @param {import('../core/renderer.js').ServiceScheduleEntry & {
 *   status: string, statusText: string, dueDistance: number,
 *   isDone: boolean, historyDate?: string, open: boolean
 * }} props
 * @param {(km: number) => void} onToggle
 * @param {(km: number) => void} onMark
 * @param {(km: number) => void} onUnmark
 * @returns {DocumentFragment}
 */
function renderServiceCard(props, onToggle, onMark, onUnmark) {
  const { km, label, items, status, statusText, dueDistance, isDone, historyDate, open } = props;
  const dueInfo = isDone ? '' : ` (через ${dueDistance.toLocaleString()} км)`;

  return html`
    <div class="sw-card ${status}" role="region" aria-label=${label}>
      <div
        class="sw-card-header ${status}"
        onclick=${() => onToggle(km)}
        onkeydown=${(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle(km);
          }
        }}
        role="button"
        tabindex="0"
        aria-expanded=${String(open)}
      >
        <span class="sw-card-km">${km.toLocaleString()} км</span>
        <span class="sw-card-label">${label}${dueInfo}</span>
        <span class="sw-card-status ${status}">${statusText}</span>
      </div>
      <div class="sw-card-body ${open ? 'open' : ''}" role="region">
        <ul>
          ${items.map((i) => html`<li>${i}</li>`)}
        </ul>
        <div style="margin-top:0.5em">
          ${Show(
            isDone,
            () =>
              html`<button class="sw-unmark-btn" onclick=${() => onUnmark(km)}>
                Отменить выполнение
              </button>`,
            () =>
              html`<button class="sw-mark-btn" onclick=${() => onMark(km)}>
                ✅ Отметить выполненным
              </button>`,
          )}
          ${historyDate ? html`<span class="sw-history" style="margin-left:1em">Выполнено: ${historyDate}</span>` : ''}
        </div>
      </div>
    </div>
  `;
}

/**
 * Рендер панели статистики.
 * @param {number} mileage
 * @param {number} overdue
 * @param {number} pending
 * @param {number} totalDone
 * @returns {DocumentFragment}
 */
function renderStats(mileage, overdue, pending, totalDone) {
  return html`
    <div class="sw-stat">
      <div class="sw-stat-item" style="background:#e3f2fd">
        <h5>Пробег</h5>
        <div class="sw-stat-num">${mileage.toLocaleString()}</div>
      </div>
      <div class="sw-stat-item" style="background:#ffebee">
        <h5>Просрочено</h5>
        <div class="sw-stat-num" style="color:${overdue > 0 ? '#d32f2f' : '#4caf50'}">
          ${overdue}
        </div>
      </div>
      <div class="sw-stat-item" style="background:#fff3e0">
        <h5>Предстоит</h5>
        <div class="sw-stat-num" style="color:#ff6b00">${pending}</div>
      </div>
      <div class="sw-stat-item" style="background:#e8f5e9">
        <h5>Выполнено</h5>
        <div class="sw-stat-num" style="color:#4caf50">${totalDone}</div>
      </div>
    </div>
  `;
}

/**
 * Рендер всего виджета планировщика ТО.
 * @param {Object} state
 * @returns {DocumentFragment}
 */
function renderWidget(state) {
  const { mileage, lastService, history, doneKmSet, openKm } = state;
  const totalDone = history.length;

  // Рассчитываем статистику
  let overdueCount = 0;
  let pendingCount = 0;
  for (const s of serviceSchedule) {
    if (doneKmSet.has(s.km)) {
      continue;
    }
    const nextKm = Math.max(s.km, lastService + s.km);
    if (nextKm <= mileage) {
      overdueCount++;
    } else if (nextKm <= mileage + 15000) {
      pendingCount++;
    }
  }

  return html`
    <div class="service-widget" role="region" aria-label="Планировщик обслуживания">
      <div class="sw-header">
        <h3>📅 Планировщик обслуживания</h3>
        <p>Введите пробег — и увидите предстоящее ТО.</p>
      </div>
      <div class="sw-body">
        <div class="sw-row">
          <div class="sw-field">
            <label for="sw-mileage">🔢 Текущий пробег (км)</label>
            <input
              type="number"
              id="sw-mileage"
              class="sw-input"
              value=${mileage}
              min="0"
              step="1000"
              aria-label="Текущий пробег"
            />
          </div>
          <div class="sw-field">
            <label for="sw-last-service">📆 Последнее ТО (км)</label>
            <input
              type="number"
              id="sw-last-service"
              class="sw-input"
              value=${lastService}
              min="0"
              step="1000"
              aria-label="Последнее ТО в километрах"
            />
          </div>
          <div style="display:flex;align-items:flex-end;gap:0.5em">
            <button class="sw-submit" id="sw-calc-btn">Рассчитать</button>
            <button class="sw-reset" id="sw-reset-btn" aria-label="Сбросить">↺</button>
          </div>
        </div>

        ${renderStats(mileage, overdueCount, pendingCount, totalDone)}

        <div class="sw-upcoming">
          <h4>График обслуживания</h4>
          ${serviceSchedule.map((s) => {
            const { status, statusText, dueDistance } = calcServiceStatus(
              s,
              mileage,
              lastService,
              doneKmSet,
            );
            const isDone = doneKmSet.has(s.km);
            const historyEntry = isDone ? history.find((h) => h.km === s.km) : null;
            return renderServiceCard(
              {
                ...s,
                status,
                statusText,
                dueDistance,
                isDone,
                historyDate: historyEntry?.date,
                open: openKm === s.km,
              },
              state._onToggle,
              state._onMark,
              state._onUnmark,
            );
          })}
          ${Show(
            totalDone > 0,
            () =>
              html`<p>
                <span
                  class="sw-clear-history"
                  id="sw-clear-all"
                  role="button"
                  tabindex="0"
                  onkeydown=${(e) => {
                  if (e.key === 'Enter') {
                    state._onClearHistory();
                  }
                }}
                >
                  Очистить историю обслуживания
                </span>
              </p>`,
          )}
        </div>
      </div>
    </div>
  `;
}

// ─── Создание виджета ─────────────────────────────────────────────

/**
 * Создать экземпляр планировщика ТО.
 * @returns {{ mount: (container: HTMLElement) => void, unmount: () => void }}
 */
export function createServiceTracker() {
  /** @type {HTMLElement|null} */
  let container = null;

  // Состояние
  const state = {
    mileage: 0,
    lastService: 0,
    /** @type {import('../core/renderer.js').ServiceHistoryEntry[]} */
    history: [],
    /** @type {Set<number>} */
    doneKmSet: new Set(),
    /** @type {number|null} */
    openKm: null,

    /** @param {number} km */
    _onToggle(km) {
      state.openKm = state.openKm === km ? null : km;
      update();
    },

    /** @param {number} km */
    _onMark(km) {
      if (!state.doneKmSet.has(km)) {
        state.history.push({ km, date: new Date().toLocaleDateString('ru-RU') });
        state.doneKmSet.add(km);
        saveHistory(state.history);
        update();
      }
    },

    /** @param {number} km */
    _onUnmark(km) {
      const idx = state.history.findIndex((h) => h.km === km);
      if (idx !== -1) {
        state.history.splice(idx, 1);
        state.doneKmSet.delete(km);
        saveHistory(state.history);
        update();
      }
    },

    _onClearHistory() {
      if (window.confirm('Очистить всю историю обслуживания?')) {
        state.history = [];
        state.doneKmSet.clear();
        saveHistory(state.history);
        update();
      }
    },
  };

  /** Загрузить данные из localStorage. */
  function loadFromStorage() {
    const saved = loadState();
    const history = loadHistory();
    state.mileage = saved.mileage;
    state.lastService = saved.lastService;
    state.history = history;
    state.doneKmSet = new Set(history.map((h) => h.km));
  }

  /** Перерендерить. */
  function update() {
    if (!container) {
      return;
    }
    const frag = renderWidget(state);
    render(container, frag);
    // Привязываем обработчики полей после рендера
    bindFieldEvents();
  }

  /** Привязать события к полям ввода. */
  function bindFieldEvents() {
    if (!container) {
      return;
    }

    const mileageInput = /** @type {HTMLInputElement|null} */ (
      container.querySelector('#sw-mileage')
    );
    const lastServiceInput = /** @type {HTMLInputElement|null} */ (
      container.querySelector('#sw-last-service')
    );
    const calcBtn = container.querySelector('#sw-calc-btn');
    const resetBtn = container.querySelector('#sw-reset-btn');

    if (mileageInput) {
      mileageInput.value = String(state.mileage);
      const handler = () => {
        state.mileage = parseInt(mileageInput.value) || 0;
        persistState({ mileage: state.mileage, lastService: state.lastService });
        update();
      };
      mileageInput.oninput = handler;
      mileageInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          handler();
        }
      };
    }

    if (lastServiceInput) {
      lastServiceInput.value = String(state.lastService);
      const handler = () => {
        state.lastService = parseInt(lastServiceInput.value) || 0;
        persistState({ mileage: state.mileage, lastService: state.lastService });
        update();
      };
      lastServiceInput.oninput = handler;
      lastServiceInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          handler();
        }
      };
    }

    if (calcBtn) {
      calcBtn.onclick = () => update();
    }
    if (resetBtn) {
      resetBtn.onclick = () => {
        state.mileage = 0;
        state.lastService = 0;
        persistState({ mileage: 0, lastService: 0 });
        update();
      };
    }

    // Очистка истории
    const clearAll = container.querySelector('#sw-clear-all');
    if (clearAll) {
      clearAll.onclick = () => state._onClearHistory();
    }
  }

  return {
    /**
     * Смонтировать виджет в контейнер.
     * @param {HTMLElement} el
     */
    mount(el) {
      container = el;
      loadFromStorage();
      update();
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
 * Инициализировать виджет планировщика ТО на странице.
 * @returns {Function} Функция очистки
 */
export function initServiceTracker() {
  let container = document.getElementById('service-tracker');
  if (container && container.querySelector('.service-widget')) {
    // Уже есть виджет (сработал legacy-скрипт) — не дублируем
    return () => {};
  }

  if (!container) {
    const content = document.querySelector('.content, article, main');
    if (content) {
      container = document.createElement('div');
      container.id = 'service-tracker';
      const target = content.querySelector('#полная-таблица-то, table');
      if (target) {
        target.parentNode.insertBefore(container, target);
      } else {
        const h2 = content.querySelector('h2');
        if (h2) {
          h2.parentNode.insertBefore(container, h2);
        } else {
          content.insertBefore(container, content.firstChild);
        }
      }
    } else {
      container = document.createElement('div');
      container.id = 'service-tracker';
      document.body.insertBefore(container, document.body.firstChild);
    }
  }

  const widget = createServiceTracker();
  widget.mount(container);

  return () => {
    widget.unmount();
  };
}

export default { initServiceTracker, createServiceTracker };
