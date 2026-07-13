/**
 * @file Оптимизация производительности рендеринга.
 *
 * Утилиты: debounce, throttle, batch-обновления через
 * requestAnimationFrame, virtual scroll, Intersection Observer,
 * мемоизация.
 */

// ─── Debounce ────────────────────────────────────────────────────

/**
 * Debounce — откладывает вызов до прекращения серии событий.
 *
 * @param {function(...*): void} fn
 * @param {number} ms  Задержка в мс
 * @param {Object} [opts]
 * @param {boolean} [opts.leading=false]  Вызвать fn сразу
 * @returns {function(...*): void & { cancel: function(): void, flush: function(): void }}
 */
export function debounce(fn, ms, opts = {}) {
  let timer = null;
  let leadingCalled = false;
  let lastCtx = null;
  /** @type {*} */
  let lastArgs = null;

  const debounced = function (...args) {
    lastCtx = this;
    lastArgs = args;

    const later = () => {
      timer = null;
      if (!opts.leading || leadingCalled) {
        fn.apply(lastCtx, lastArgs);
      }
      leadingCalled = false;
    };

    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(later, ms);

    if (opts.leading && !leadingCalled) {
      leadingCalled = true;
      fn.apply(lastCtx, lastArgs);
    }
  };

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer);
    }
    timer = null;
    leadingCalled = false;
    lastCtx = null;
    lastArgs = null;
  };

  debounced.flush = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
      fn.apply(lastCtx, lastArgs);
      lastCtx = null;
      lastArgs = null;
    }
  };

  return debounced;
}

// ─── Throttle ────────────────────────────────────────────────────

/**
 * Throttle — ограничивает частоту вызовов.
 *
 * @param {function(...*): void} fn
 * @param {number} ms  Интервал
 * @param {Object} [opts]
 * @param {boolean} [opts.trailing=true]  Вызвать fn после последнего события
 * @returns {function(...*): void & { cancel: function(): void }}
 */
export function throttle(fn, ms, opts = {}) {
  const { trailing = true } = opts;
  let lastCall = 0;
  let timer = null;
  let lastCtx = null;
  /** @type {*} */
  let lastArgs = null;

  const throttled = function (...args) {
    lastCtx = this;
    lastArgs = args;

    const now = Date.now();
    const remaining = ms - (now - lastCall);

    if (remaining <= 0) {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      lastCall = now;
      fn.apply(lastCtx, lastArgs);
    } else if (trailing && !timer) {
      timer = setTimeout(() => {
        lastCall = Date.now();
        timer = null;
        fn.apply(lastCtx, lastArgs);
      }, remaining);
    }
  };

  throttled.cancel = () => {
    if (timer) {
      clearTimeout(timer);
    }
    timer = null;
    lastCall = 0;
    lastCtx = null;
    lastArgs = null;
  };

  return throttled;
}

// ─── Batch (requestAnimationFrame) ───────────────────────────────

/**
 * Пакетное обновление — группирует несколько вызовов в один
 * requestAnimationFrame.
 *
 * @returns {{ schedule: function(function(): void): void, flush: function(): void }}
 */
export function batchRAF() {
  let queue = [];
  let rafId = null;

  function process() {
    const batch = queue;
    queue = [];
    rafId = null;
    for (const fn of batch) {
      try {
        fn();
      } catch (err) {
        console.warn('[batchRAF]', err);
      }
    }
  }

  return {
    /**
     * Запланировать выполнение функции в следующем RAF.
     * @param {function(): void} fn
     */
    schedule(fn) {
      queue.push(fn);
      if (!rafId) {
        rafId = requestAnimationFrame(process);
      }
    },

    /** Немедленно выполнить все запланированные задачи. */
    flush() {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      process();
    },
  };
}

// ─── Мемоизация ─────────────────────────────────────────────────

/**
 * Мемоизация функции с одним аргументом.
 * Использует JSON.stringify для сериализации ключа.
 *
 * @template T, R
 * @param {function(T): R} fn
 * @param {number} [maxSize=100]  Максимальный размер кеша
 * @returns {function(T): R & { clear: function(): void }}
 */
export function memoize(fn, maxSize = 100) {
  const cache = new Map();

  const memoized = (arg) => {
    const key = JSON.stringify(arg);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(arg);
    if (cache.size >= maxSize) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
    }
    cache.set(key, result);
    return result;
  };

  memoized.clear = () => cache.clear();
  return memoized;
}

// ─── Virtual Scroll ─────────────────────────────────────────────

/**
 * Виртуальный скролл для длинных списков.
 * Рендерит только видимые элементы + буфер.
 *
 * @param {HTMLElement} container  Контейнер с overflow: auto/scroll
 * @param {Object} opts
 * @param {number} opts.itemHeight  Высота одного элемента в пикселях
 * @param {number} [opts.overscan=5]  Количество дополнительных элементов сверху/снизу
 * @param {function(number, HTMLElement): void} opts.renderItem  (index, element) => void
 * @param {number} opts.totalItems  Общее количество элементов
 * @returns {{ update: function({ totalItems?: number, renderItem?: function }): void, destroy: function(): void }}
 */
export function createVirtualScroll(container, opts) {
  const { itemHeight, overscan = 5, renderItem, totalItems } = opts;

  /** @type {HTMLDivElement} */
  const spacer = document.createElement('div');
  spacer.style.height = totalItems * itemHeight + 'px';
  spacer.style.pointerEvents = 'none';
  container.appendChild(spacer);

  /** @type {HTMLDivElement} */
  const viewport = document.createElement('div');
  viewport.style.position = 'absolute';
  viewport.style.top = '0';
  viewport.style.left = '0';
  viewport.style.right = '0';
  container.style.position = 'relative';
  container.appendChild(viewport);

  let currentTotal = totalItems;
  let currentRender = renderItem;

  function render() {
    const scrollTop = container.scrollTop;
    const visibleHeight = container.clientHeight;

    const startIdx = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIdx = Math.min(
      currentTotal,
      Math.ceil((scrollTop + visibleHeight) / itemHeight) + overscan,
    );

    const fragment = document.createDocumentFragment();

    for (let i = startIdx; i < endIdx; i++) {
      const itemEl = document.createElement('div');
      itemEl.style.position = 'absolute';
      itemEl.style.top = i * itemHeight + 'px';
      itemEl.style.left = '0';
      itemEl.style.right = '0';
      itemEl.style.height = itemHeight + 'px';
      currentRender(i, itemEl);
      fragment.appendChild(itemEl);
    }

    // Очищаем и вставляем пакетно
    viewport.innerHTML = '';
    viewport.appendChild(fragment);
  }

  // Throttle-обработчик скролла
  const onScroll = throttle(render, 16); // ~60fps
  container.addEventListener('scroll', onScroll);

  // Первый рендер
  requestAnimationFrame(render);

  return {
    /**
     * Обновить параметры виртуального скролла.
     */
    update(newOpts) {
      if (newOpts.totalItems !== undefined) {
        currentTotal = newOpts.totalItems;
        spacer.style.height = currentTotal * itemHeight + 'px';
      }
      if (newOpts.renderItem) {
        currentRender = newOpts.renderItem;
      }
      render();
    },

    destroy() {
      container.removeEventListener('scroll', onScroll);
      onScroll.cancel();
      spacer.remove();
      viewport.innerHTML = '';
    },
  };
}

// ─── Intersection Observer (ленивая загрузка) ───────────────────

/**
 * Наблюдатель пересечений для ленивой загрузки.
 *
 * @param {string|HTMLElement} root  Корневой элемент или селектор
 * @param {Object} [opts]
 * @param {string} [opts.selector='[data-lazy]']  Селектор для отслеживания
 * @param {number} [opts.threshold=0]  Порог видимости
 * @param {number} [opts.rootMargin='200px']  Отступ для предзагрузки
 * @returns {function(): void}  Уничтожение наблюдателя
 */
export function initLazyLoading(root, opts = {}) {
  const { selector = '[data-lazy]', threshold = 0, rootMargin = '200px' } = opts;

  const rootEl = typeof root === 'string' ? document.querySelector(root) : root;

  if (!rootEl) {
    return () => {};
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const el = entry.target;
          const src = el.dataset.src;
          if (src) {
            if (el.tagName === 'IMG') {
              el.src = src;
            } else if (el.tagName === 'IFRAME') {
              el.src = src;
            } else {
              el.style.backgroundImage = `url(${src})`;
            }
            el.removeAttribute('data-lazy');
            el.removeAttribute('data-src');
          }
          observer.unobserve(el);
        }
      }
    },
    { root: rootEl, threshold, rootMargin },
  );

  const elements = rootEl.querySelectorAll(selector);
  elements.forEach((el) => observer.observe(el));

  return () => observer.disconnect();
}

// ─── Инициализация глобальных оптимизаций ───────────────────────

/**
 * Инициализировать глобальные оптимизации производительности.
 * Вызывается при загрузке страницы.
 */
export function initPerformance() {
  // Ленивая загрузка изображений через data-src (если не loading=lazy)
  const lazyImages = document.querySelectorAll('.content img[data-src]');
  if (lazyImages.length > 0) {
    initLazyLoading(document.body, {
      selector: '.content img[data-src]',
      rootMargin: '300px',
    });
  }
}
