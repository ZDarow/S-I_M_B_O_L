/**
 * @file Модуль доступности (WCAG 2.1 AA).
 * Управление фокусом, ARIA-атрибутами, клавиатурная навигация,
 * skip-links, поддержка prefers-reduced-motion.
 *
 * @example
 *   import { A11y } from './accessibility.js';
 *
 *   // Skip-link
 *   A11y.createSkipLink('main', 'К содержимому');
 *
 *   // Фокус
 *   A11y.focus.trap(element);
 *   A11y.focus.saveContext();
 *   // … динамическое обновление DOM …
 *   A11y.focus.restoreContext();
 *
 *   // Клавиатура
 *   A11y.keyboard.enter(el, handler);
 *   A11y.keyboard.arrowKeys(el, (dir) => console.log(dir));
 */

export const A11y = {
  /**
   * Создать и добавить skip-link в начало body.
   * @param {string} targetId  ID целевого элемента
   * @param {string} [label='Перейти к содержимому']  Текст ссылки
   * @returns {HTMLAnchorElement}
   */
  createSkipLink(targetId, label = 'Перейти к содержимому') {
    // Удаляем старый skip-link, если есть
    const old = document.querySelector('.a11y-skip-link');
    if (old) {
      old.remove();
    }

    const link = document.createElement('a');
    link.href = `#${targetId}`;
    link.className = 'a11y-skip-link';
    link.textContent = label;
    // ARIA
    link.setAttribute('role', 'navigation');
    link.setAttribute('aria-label', label);

    // Фокус на целевой элемент
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.getElementById(targetId);
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: false });
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Убираем tabindex после потери фокуса, чтобы не ломать Tab-порядок
        target.addEventListener(
          'focusout',
          () => {
            target.removeAttribute('tabindex');
          },
          { once: true },
        );
      }
    });

    document.body.insertBefore(link, document.body.firstChild);
    return link;
  },

  /**
   * Управление фокусом.
   */
  focus: {
    /** Стек сохранённых контекстов фокуса */
    _stack: [],

    /**
     * Сохранить текущий активный элемент.
     * Вызвать перед динамическим изменением DOM.
     */
    saveContext() {
      this._stack.push(document.activeElement);
    },

    /**
     * Восстановить последний сохранённый фокус.
     */
    restoreContext() {
      const el = this._stack.pop();
      if (el && document.contains(el) && typeof el.focus === 'function') {
        el.focus({ preventScroll: true });
      }
    },

    /**
     * Сбросить стек контекстов.
     */
    clearContext() {
      this._stack = [];
    },

    /**
     * Запереть фокус внутри элемента (модальные окна).
     * @param {HTMLElement} container
     * @returns {function(): void}  Функция для снятия ловушки
     */
    trap(container) {
      const focusableSelector =
        'a[href], button:not([disabled]), textarea:not([disabled]), ' +
        'input:not([disabled]), select:not([disabled]), ' +
        '[tabindex]:not([tabindex="-1"]):not([disabled])';

      /** @returns {HTMLElement[]} */
      const getFocusable = () => Array.from(container.querySelectorAll(focusableSelector));

      const handleKeydown = (e) => {
        if (e.key !== 'Tab') {
          return;
        }

        const focusable = getFocusable();
        if (focusable.length === 0) {
          e.preventDefault();
          return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      };

      container.addEventListener('keydown', handleKeydown);

      // Фокус на первый элемент
      const focusable = getFocusable();
      if (focusable.length > 0) {
        focusable[0].focus();
      }

      return () => {
        container.removeEventListener('keydown', handleKeydown);
      };
    },

    /**
     * Сделать элемент видимым и сфокусированным.
     * @param {HTMLElement} el
     */
    focusVisible(el) {
      el.setAttribute('tabindex', '-1');
      el.focus({ preventScroll: true });
      el.addEventListener(
        'focusout',
        () => {
          el.removeAttribute('tabindex');
        },
        { once: true },
      );
    },
  },

  /**
   * Клавиатурные хендлеры.
   */
  keyboard: {
    /**
     * Обработка Enter и Space как «активации».
     * @param {HTMLElement} el
     * @param {function(KeyboardEvent): void} handler
     * @returns {function(): void}  Отписка
     */
    activate(el, handler) {
      const onKey = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handler(e);
        }
      };
      el.addEventListener('keydown', onKey);
      return () => el.removeEventListener('keydown', onKey);
    },

    /**
     * Обработка Enter.
     * @param {HTMLElement} el
     * @param {function(KeyboardEvent): void} handler
     * @returns {function(): void}
     */
    enter(el, handler) {
      const onKey = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handler(e);
        }
      };
      el.addEventListener('keydown', onKey);
      return () => el.removeEventListener('keydown', onKey);
    },

    /**
     * Обработка стрелок.
     * @param {HTMLElement} el
     * @param {function(string, KeyboardEvent): void} handler  dir = 'up'|'down'|'left'|'right'
     * @returns {function(): void}
     */
    arrowKeys(el, handler) {
      const map = {
        ArrowUp: 'up',
        ArrowDown: 'down',
        ArrowLeft: 'left',
        ArrowRight: 'right',
      };
      const onKey = (e) => {
        const dir = map[e.key];
        if (dir) {
          e.preventDefault();
          handler(dir, e);
        }
      };
      el.addEventListener('keydown', onKey);
      return () => el.removeEventListener('keydown', onKey);
    },

    /**
     * Обработка Escape.
     * @param {HTMLElement} el
     * @param {function(KeyboardEvent): void} handler
     * @returns {function(): void}
     */
    escape(el, handler) {
      const onKey = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          handler(e);
        }
      };
      el.addEventListener('keydown', onKey);
      return () => el.removeEventListener('keydown', onKey);
    },

    /**
     * Создать Roving Tabindex для списка элементов (как radio group).
     * @param {HTMLElement} container
     * @param {string} itemSelector  CSS-селектор для элементов
     * @returns {function(): void}  Отписка
     */
    rovingTabindex(container, itemSelector) {
      /** @returns {HTMLElement[]} */
      const getItems = () => Array.from(container.querySelectorAll(itemSelector));

      const handleKeydown = (e) => {
        const items = getItems();
        const currentIdx = items.indexOf(/** @type {HTMLElement} */ (document.activeElement));
        if (currentIdx === -1) {
          return;
        }

        let nextIdx = currentIdx;
        switch (e.key) {
          case 'ArrowDown':
          case 'ArrowRight':
            e.preventDefault();
            nextIdx = (currentIdx + 1) % items.length;
            break;
          case 'ArrowUp':
          case 'ArrowLeft':
            e.preventDefault();
            nextIdx = (currentIdx - 1 + items.length) % items.length;
            break;
          case 'Home':
            e.preventDefault();
            nextIdx = 0;
            break;
          case 'End':
            e.preventDefault();
            nextIdx = items.length - 1;
            break;
          default:
            return;
        }

        items[nextIdx].setAttribute('tabindex', '0');
        items[currentIdx].setAttribute('tabindex', '-1');
        items[nextIdx].focus();
      };

      // Инициализация: первый элемент tabindex=0, остальные -1
      const items = getItems();
      items.forEach((item, i) => {
        item.setAttribute('tabindex', i === 0 ? '0' : '-1');
        item.setAttribute('role', 'tab');
      });

      container.addEventListener('keydown', handleKeydown);
      return () => container.removeEventListener('keydown', handleKeydown);
    },
  },

  /**
   * ARIA-утилиты.
   */
  aria: {
    /**
     * Установить ARIA-атрибуты на элемент.
     * @param {HTMLElement} el
     * @param {Object<string, string|boolean>} attrs  Например {role: 'button', 'aria-expanded': false}
     */
    set(el, attrs) {
      for (const [key, val] of Object.entries(attrs)) {
        if (typeof val === 'boolean') {
          el.setAttribute(key, val ? 'true' : 'false');
        } else {
          el.setAttribute(key, String(val));
        }
      }
    },

    /**
     * Обновить aria-live регион или создать, если не существует.
     * @param {string} [id='a11y-live-region']
     * @param {string} [mode='polite']  polite | assertive
     * @returns {HTMLElement}
     */
    liveRegion(id = 'a11y-live-region', mode = 'polite') {
      let region = document.getElementById(id);
      if (!region) {
        region = document.createElement('div');
        region.id = id;
        region.setAttribute('aria-live', mode);
        region.setAttribute('aria-atomic', 'true');
        region.className = 'a11y-sr-only';
        document.body.appendChild(region);
      }
      return region;
    },

    /**
     * Объявить текст через aria-live.
     * @param {string} message
     * @param {'polite'|'assertive'} [mode='polite']
     */
    announce(message, mode = 'polite') {
      const region = this.liveRegion('a11y-live-region', mode);
      // Смена текста с задержкой для повторных объявлений
      region.textContent = '';
      requestAnimationFrame(() => {
        region.textContent = message;
      });
    },
  },

  /**
   * prefers-reduced-motion.
   */
  motion: {
    /**
     * Проверить, предпочитает ли пользователь уменьшение движения.
     * @returns {boolean}
     */
    prefersReduced() {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    /**
     * Выполнить колбэк при изменении предпочтений движения.
     * @param {function(boolean): void} fn  Получает true, если reduced
     * @returns {function(): void}  Отписка
     */
    onChange(fn) {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      const handler = (e) => fn(e.matches);
      mq.addEventListener('change', handler);
      return () => mq.removeEventListener('change', handler);
    },

    /**
     * Обертка для requestAnimationFrame с учётом reduced-motion.
     * @param {function(): void} fn
     */
    safeAnimate(fn) {
      if (this.prefersReduced()) {
        fn(); // Выполнить сразу без анимации
      } else {
        requestAnimationFrame(fn);
      }
    },
  },

  /**
   * Установить aria-current на элемент навигации.
   * @param {HTMLElement} container  Родительский контейнер
   * @param {string} selector  Селектор элементов навигации
   * @param {string|number|boolean} currentValue  Значение для aria-current
   */
  setCurrentNav(container, selector, currentValue = 'page') {
    const items = container.querySelectorAll(selector);
    items.forEach((el) => {
      const isCurrent =
        el.getAttribute('href') === window.location.pathname || el.dataset.current === 'true';
      el.setAttribute('aria-current', isCurrent ? String(currentValue) : 'false');
    });
  },

  /**
   * Инициализация: skip-link, aria-live, тёмная тема.
   * @param {Object} [opts]
   * @param {string} [opts.skipTo='mdbook-content']  ID основного контента
   * @param {string} [opts.skipLabel='Перейти к содержимому']
   */
  init({ skipTo = 'mdbook-content', skipLabel = 'Перейти к содержимому' } = {}) {
    this.createSkipLink(skipTo, skipLabel);
    this.aria.liveRegion();

    // Установка aria-current для навигации по главам
    const sidebar = document.getElementById('mdbook-sidebar');
    if (sidebar) {
      this.setCurrentNav(sidebar, 'a');
    }
  },
};
