/**
 * @file Централизованное управление состоянием приложения.
 * Паттерн Observer с атомарными транзакциями, персистентностью
 * через localStorage и валидацией данных при загрузке.
 *
 * @example
 *   const store = createStore(
 *     { count: 0, user: null },
 *     { persist: true, key: 'my-app-state' }
 *   );
 *
 *   // Подписка на изменения конкретного ключа
 *   const unsub = store.subscribe('count', (newVal, oldVal) => {
 *     console.log(`count: ${oldVal} → ${newVal}`);
 *   });
 *
 *   // Атомарное обновление
 *   store.update({ count: 1 });
 *
 *   // Отписка
 *   unsub();
 */

/**
 * @template T
 * @typedef {Object} StoreOptions
 * @property {boolean} [persist=false]  Включить автосохранение в localStorage
 * @property {string}  [key='app-state'] Ключ localStorage для персистентности
 * @property {function(T): T} [validate] Функция валидации/миграции при загрузке
 */

/**
 * @template T
 * @typedef {Object} Store
 * @property {function(): T} getState      Получить текущее состояние (копия)
 * @property {function(string): *} getKey  Получить значение по ключу
 * @property {function(Partial<T>, string): void} update  Атомарное обновление
 * @property {function(string, function(*, *): void): function(): void} subscribe
 *   Подписка на изменения ключа. Возвращает функцию отписки.
 * @property {function(function(*, *): void, string=): function(): void} subscribeAll
 *   Подписка на любые изменения. Опционально — фильтр по ключу.
 * @property {function(): void} reset  Сброс к начальному состоянию
 * @property {function(): void} destroy  Очистка всех подписок и данных
 */

/**
 * Создать хранилище состояния.
 *
 * @template T
 * @param {T} initialState  Начальное состояние
 * @param {StoreOptions<T>} [options={}]  Опции
 * @returns {Store<T>}
 */
export function createStore(initialState, options = {}) {
  const { persist = false, key = 'app-state', validate = null } = options;

  // Глубокое копирование начального состояния (защита от мутаций извне)
  const INITIAL = deepClone(initialState);

  /** @type {T} */
  let state = deepClone(initialState);

  /** @type {Map<string, Set<function(*, *): void>>} */
  const keySubs = new Map();

  /** @type {Set<function(string, *, *): void>} */
  const allSubs = new Set();

  /** @type {boolean} */
  let insideTransaction = false;

  // ─── Загрузка сохранённого состояния ────────────────────────────
  if (persist) {
    const saved = loadFromStorage(key, validate);
    if (saved !== null) {
      state = deepMerge(deepClone(initialState), saved);
    }
  }

  // ─── Внутренние утилиты ─────────────────────────────────────────

  /**
   * Уведомить подписчиков об изменении ключа.
   * @param {string} keyPath
   * @param {*} newVal
   * @param {*} oldVal
   */
  function notify(keyPath, newVal, oldVal) {
    // Подписчики конкретного ключа
    const subs = keySubs.get(keyPath);
    if (subs) {
      subs.forEach((fn) => {
        safeCall(fn, newVal, oldVal);
      });
    }

    // Глобальные подписчики
    allSubs.forEach((fn) => {
      safeCall(fn, keyPath, newVal, oldVal);
    });
  }

  /**
   * Сохранить состояние в localStorage, если включена персистентность.
   */
  function persistState() {
    if (!persist) {
      return;
    }
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch (err) {
      console.warn(`[StateManager] Не удалось сохранить «${key}»:`, err.message);
    }
  }

  // ─── Публичный API ──────────────────────────────────────────────

  /**
   * Вернуть копию всего состояния.
   * @returns {T}
   */
  function getState() {
    return deepClone(state);
  }

  /**
   * Вернуть значение по ключу (поддерживает точечную нотацию «a.b.c»).
   * @param {string} keyPath
   * @returns {*}
   */
  function getKey(keyPath) {
    return deepClone(getNested(state, keyPath));
  }

  /**
   * Атомарное обновление состояния. Изменения применяются пакетно,
   * уведомления отправляются один раз для каждого затронутого ключа.
   *
   * @param {Partial<T>} patch  Объект с новыми значениями
   * @param {string} [source='']  Источник обновления (для отладки)
   */
  function update(patch, _source = '') {
    if (insideTransaction) {
      throw new Error('[StateManager] Рекурсивный вызов update запрещён');
    }

    insideTransaction = true;
    const changedKeys = [];

    try {
      for (const [k, value] of Object.entries(patch)) {
        const oldVal = getNested(state, k);
        const newVal = deepClone(value);

        setNested(state, k, newVal);

        if (!shallowEqual(oldVal, newVal)) {
          changedKeys.push({ key: k, oldVal, newVal });
        }
      }
    } finally {
      insideTransaction = false;
    }

    // Сохранить в localStorage
    if (persist && changedKeys.length > 0) {
      persistState();
    }

    // Уведомить подписчиков
    for (const { key: k, oldVal, newVal } of changedKeys) {
      notify(k, newVal, oldVal);
    }
  }

  /**
   * Подписаться на изменения конкретного ключа.
   * @param {string} keyPath
   * @param {function(*, *): void} fn  Получает (newValue, oldValue)
   * @returns {function(): void}  Функция для отписки
   */
  function subscribe(keyPath, fn) {
    if (!keySubs.has(keyPath)) {
      keySubs.set(keyPath, new Set());
    }
    keySubs.get(keyPath).add(fn);

    return () => {
      const subs = keySubs.get(keyPath);
      if (subs) {
        subs.delete(fn);
        if (subs.size === 0) {
          keySubs.delete(keyPath);
        }
      }
    };
  }

  /**
   * Подписаться на любые изменения (опционально — по ключу).
   * @param {function(string, *, *): void} fn  Получает (keyPath, newValue, oldValue)
   * @param {string} [filterKey]  Если указан, вызывать только при изменениях этого ключа
   * @returns {function(): void}
   */
  function subscribeAll(fn, filterKey) {
    if (filterKey) {
      // Оборачиваем фильтром
      const wrapped = (keyPath, newVal, oldVal) => {
        if (keyPath === filterKey) {
          fn(keyPath, newVal, oldVal);
        }
      };
      allSubs.add(wrapped);
      return () => {
        allSubs.delete(wrapped);
      };
    }

    allSubs.add(fn);
    return () => {
      allSubs.delete(fn);
    };
  }

  /**
   * Сбросить состояние до начального.
   */
  function reset() {
    const oldState = state;
    state = deepClone(INITIAL);

    const changedKeys = [];

    // Собираем изменившиеся ключи
    for (const k of Object.keys(state)) {
      if (!shallowEqual(oldState[k], state[k])) {
        changedKeys.push({ key: k, oldVal: oldState[k], newVal: state[k] });
      }
    }

    if (persist) {
      persistState();
    }

    for (const { key: k, oldVal, newVal } of changedKeys) {
      notify(k, newVal, oldVal);
    }
  }

  /**
   * Полностью очистить хранилище: подписки, данные, localStorage.
   */
  function destroy() {
    keySubs.clear();
    allSubs.clear();
    state = deepClone(INITIAL);
    if (persist) {
      try {
        localStorage.removeItem(key);
      } catch {
        // localStorage недоступен — игнорируем
      }
    }
  }

  return {
    getState,
    getKey,
    update,
    subscribe,
    subscribeAll,
    reset,
    destroy,
  };
}

// ─── Утилиты ─────────────────────────────────────────────────────

/**
 * Безопасно вызвать функцию, игнорируя ошибки.
 * @param {Function} fn
 * @param {...*} args
 */
function safeCall(fn, ...args) {
  try {
    fn(...args);
  } catch (err) {
    console.warn('[StateManager] Ошибка в подписчике:', err.message);
  }
}

/**
 * Глубокое копирование значения.
 * @param {*} obj
 * @returns {*}
 */
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  if (Array.isArray(obj)) {
    return obj.map(deepClone);
  }
  const clone = {};
  for (const [k, v] of Object.entries(obj)) {
    clone[k] = deepClone(v);
  }
  return clone;
}

/**
 * Получить вложенное значение по точечной нотации.
 * @param {Object} obj
 * @param {string} path  «a.b.c»
 * @returns {*}
 */
function getNested(obj, path) {
  const keys = path.split('.');
  let current = obj;
  for (const k of keys) {
    if (current === null || typeof current !== 'object') {
      return undefined;
    }
    current = current[k];
  }
  return current;
}

/**
 * Установить вложенное значение по точечной нотации.
 * @param {Object} obj
 * @param {string} path
 * @param {*} value
 */
function setNested(obj, path, value) {
  const keys = path.split('.');
  let current = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (!(keys[i] in current)) {
      current[keys[i]] = {};
    }
    current = current[keys[i]];
  }
  current[keys[keys.length - 1]] = value;
}

/**
 * Поверхностное сравнение значений.
 * @param {*} a
 * @param {*} b
 * @returns {boolean}
 */
function shallowEqual(a, b) {
  if (a === b) {
    return true;
  }
  if (a === null || b === null) {
    return false;
  }
  if (typeof a !== typeof b) {
    return false;
  }

  if (typeof a === 'object') {
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    if (keysA.length !== keysB.length) {
      return false;
    }
    return keysA.every((k) => a[k] === b[k]);
  }

  return a === b;
}

/**
 * Глубокое слияние объектов (source в target).
 * @param {Object} target
 * @param {Object} source
 * @returns {Object}
 */
function deepMerge(target, source) {
  const result = deepClone(target);
  for (const [k, v] of Object.entries(source)) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      result[k] = deepMerge(result[k] || {}, v);
    } else {
      result[k] = deepClone(v);
    }
  }
  return result;
}

/**
 * Загрузить и провалидировать состояние из localStorage.
 *
 * @template T
 * @param {string} key
 * @param {function(T): T|null} [validate]
 * @returns {T|null}
 */
function loadFromStorage(key, validate) {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) {
      return null;
    }

    /** @type {T} */
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (parseErr) {
      console.warn(
        `[StateManager] Ошибка парсинга «${key}»:`,
        parseErr.message,
        '— используется начальное состояние',
      );
      localStorage.removeItem(key);
      return null;
    }

    if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
      console.warn(`[StateManager] Неверный формат данных «${key}» — ожидался объект`);
      localStorage.removeItem(key);
      return null;
    }

    // Валидация/миграция
    if (typeof validate === 'function') {
      const validated = validate(parsed);
      if (validated === null) {
        console.warn(`[StateManager] Валидация «${key}» не пройдена — сброс`);
        localStorage.removeItem(key);
        return null;
      }
      return validated;
    }

    return parsed;
  } catch (err) {
    console.warn('[StateManager] Ошибка доступа к localStorage:', err.message);
    return null;
  }
}
