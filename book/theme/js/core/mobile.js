/**
 * @file Мобильная адаптивность и UX.
 *
 * Touch-friendly зоны, адаптивные таблицы, жесты (swipe),
 * экспорт/импорт JSON, визуальная обратная связь.
 */

import { debounce } from './performance.js';

// ─── Touch-friendly (44x44px minimum) ───────────────────────────

/**
 * Проверить, является ли элемент достаточно большим для touch-взаимодействия.
 * WCAG 2.5.8 — целевой размер не менее 44x44 CSS-пикселей.
 *
 * @param {HTMLElement} el
 * @returns {{ valid: boolean, width: number, height: number }}
 */
export function checkTouchTarget(el) {
  const rect = el.getBoundingClientRect();
  const w = rect.width;
  const h = rect.height;
  return {
    valid: w >= 44 && h >= 44,
    width: w,
    height: h,
  };
}

/**
 * Добавить отступы элементу, если его размер меньше 44x44.
 * @param {HTMLElement} el
 * @returns {boolean}  true если размер был увеличен
 */
export function ensureTouchTarget(el) {
  const { valid, width, height } = checkTouchTarget(el);
  if (valid) {
    return false;
  }

  const style = el.style;
  const padX = Math.max(0, Math.ceil((44 - width) / 2));
  const padY = Math.max(0, Math.ceil((44 - height) / 2));

  if (padX > 0) {
    style.paddingLeft = padX + 'px';
    style.paddingRight = padX + 'px';
  }
  if (padY > 0) {
    style.paddingTop = padY + 'px';
    style.paddingBottom = padY + 'px';
  }
  return true;
}

/**
 * Просканировать DOM и увеличить touch-цели для интерактивных элементов.
 * @param {HTMLElement} [root=document.body]
 */
export function fixTouchTargets(root = document.body) {
  const selectors = [
    'button',
    'a',
    'input[type="button"]',
    'input[type="submit"]',
    '[role="button"]',
    '.dtc-tab',
    '.dtc-item',
    '.sw-card-header',
    '.sw-mark-btn',
    '.sw-unmark-btn',
    '.sw-submit',
    '.sw-reset',
  ];

  for (const sel of selectors) {
    const elements = root.querySelectorAll(sel);
    for (const el of elements) {
      ensureTouchTarget(el);
    }
  }
}

// ─── Swipe Detection ─────────────────────────────────────────────

/**
 * Определение жеста свайпа.
 *
 * @param {HTMLElement} el
 * @param {function(string, number): void} onSwipe  (direction, distance) => void
 *   direction: 'left' | 'right' | 'up' | 'down'
 * @returns {function(): void}  Отписка
 */
export function detectSwipe(el, onSwipe) {
  let startX = 0;
  let startY = 0;
  let tracking = false;

  const MIN_DISTANCE = 50;

  const onTouchStart = (e) => {
    if (e.touches.length !== 1) {
      return;
    }
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    tracking = true;
  };

  const onTouchEnd = (e) => {
    if (!tracking) {
      return;
    }
    tracking = false;

    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;

    const dx = endX - startX;
    const dy = endY - startY;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    if (Math.max(absDx, absDy) < MIN_DISTANCE) {
      return;
    }

    if (absDx > absDy) {
      onSwipe(dx > 0 ? 'right' : 'left', absDx);
    } else {
      onSwipe(dy > 0 ? 'down' : 'up', absDy);
    }
  };

  el.addEventListener('touchstart', onTouchStart, { passive: true });
  el.addEventListener('touchend', onTouchEnd, { passive: true });

  return () => {
    el.removeEventListener('touchstart', onTouchStart);
    el.removeEventListener('touchend', onTouchEnd);
  };
}

// ─── Адаптивные таблицы ─────────────────────────────────────────

/**
 * Преобразовать таблицы для мобильных: добавить горизонтальный скролл,
 * data-атрибуты для заголовков, фиксированные заголовки.
 *
 * @param {HTMLElement} [root=document.body]
 */
export function enhanceTables(root = document.body) {
  const tables = root.querySelectorAll('.content table');

  for (const table of tables) {
    // Если таблица уже внутри wrapper, пропускаем
    if (table.parentElement?.classList.contains('table-wrapper-enhanced')) {
      continue;
    }

    // Оборачиваем в скроллящийся контейнер
    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper-enhanced';
    wrapper.style.overflowX = 'auto';
    wrapper.style.WebkitOverflowScrolling = 'touch';
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', 'Таблица (горизонтальный скролл)');

    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);

    // Фиксированные заголовки при скролле
    const thead = table.querySelector('thead');
    if (thead) {
      thead.style.position = 'sticky';
      thead.style.top = '0';
      thead.style.zIndex = '1';
    }
  }
}

// ─── Индикаторы загрузки ────────────────────────────────────────

/**
 * Создать индикатор загрузки (spinner).
 * @param {string} [message='Загрузка…']
 * @returns {HTMLElement}
 */
export function createSpinner(message = 'Загрузка…') {
  const el = document.createElement('div');
  el.className = 'spinner-indicator';
  el.setAttribute('role', 'status');
  el.setAttribute('aria-live', 'polite');
  el.innerHTML = `
    <div class="spinner-ring"></div>
    <span class="spinner-text">${message}</span>
  `;
  return el;
}

/**
 * Показать/скрыть индикатор загрузки.
 * @param {HTMLElement} container
 * @param {boolean} show
 * @param {string} [message]
 */
export function toggleSpinner(container, show, message) {
  let spinner = container.querySelector('.spinner-indicator');
  if (show) {
    if (!spinner) {
      spinner = createSpinner(message);
      container.insertBefore(spinner, container.firstChild);
    }
  } else {
    if (spinner) {
      spinner.remove();
    }
  }
}

// ─── Экспорт/импорт JSON ────────────────────────────────────────

/**
 * Скачать данные как JSON-файл.
 *
 * @param {*} data
 * @param {string} [filename='export.json']
 */
export function downloadJSON(data, filename = 'export.json') {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Загрузить JSON-файл через file input.
 *
 * @returns {Promise<*>}
 */
export function uploadJSON() {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,application/json';
    input.style.display = 'none';
    document.body.appendChild(input);

    input.addEventListener('change', () => {
      const file = input.files?.[0];
      if (!file) {
        document.body.removeChild(input);
        reject(new Error('Файл не выбран'));
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          document.body.removeChild(input);
          resolve(data);
        } catch (err) {
          document.body.removeChild(input);
          reject(new Error('Ошибка парсинга JSON: ' + err.message));
        }
      };
      reader.onerror = () => {
        document.body.removeChild(input);
        reject(new Error('Ошибка чтения файла'));
      };
      reader.readAsText(file);
    });

    input.click();
  });
}

// ─── Визуальная обратная связь ──────────────────────────────────

/**
 * Временная подсветка элемента (для обратной связи при действии).
 * @param {HTMLElement} el
 * @param {string} [className='feedback-flash']
 * @param {number} [duration=300]
 */
export function flashElement(el, className = 'feedback-flash', duration = 300) {
  el.classList.add(className);
  setTimeout(() => el.classList.remove(className), duration);
}

// ─── Инициализация мобильных улучшений ──────────────────────────

/**
 * Применить все мобильные улучшения к странице.
 * @param {HTMLElement} [root=document.body]
 */
export function initMobile(root = document.body) {
  fixTouchTargets(root);
  enhanceTables(root);

  // Debounced resize handler для пересчёта touch-целей
  const onResize = debounce(() => {
    fixTouchTargets(root);
  }, 250);
  window.addEventListener('resize', onResize);

  // Возвращаем функцию очистки
  return () => {
    window.removeEventListener('resize', onResize);
    onResize.cancel();
  };
}
