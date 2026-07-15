/**
 * @file Unit-тесты для State Manager
 *
 * Запуск:
 *   npx vitest run book/theme/js/__tests__/state-manager.test.js
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { createStore } from '../core/state-manager.js';

// ─── Вспомогательные: мок localStorage ───────────────────────────
function mockLocalStorage() {
  const store = {};
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) =>
    store[key] !== undefined ? store[key] : null,
  );
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, val) => {
    store[key] = String(val);
  });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => {
    delete store[key];
  });
}

function clearStorageMock() {
  vi.restoreAllMocks();
}

// ─── Тесты ───────────────────────────────────────────────────────

describe('createStore', () => {
  afterEach(() => {
    clearStorageMock();
  });

  describe('базовые операции', () => {
    it('создаёт хранилище с начальным состоянием', () => {
      const store = createStore({ a: 1, b: 'hello' });
      expect(store.getState()).toEqual({ a: 1, b: 'hello' });
    });

    it('getState возвращает копию, а не ссылку', () => {
      const store = createStore({ items: [1, 2, 3] });
      const state = store.getState();
      state.items.push(4);
      // Оригинал не изменился
      expect(store.getState()).toEqual({ items: [1, 2, 3] });
    });

    it('getKey возвращает значение по ключу', () => {
      const store = createStore({ count: 42, nested: { val: 'x' } });
      expect(store.getKey('count')).toBe(42);
      expect(store.getKey('nested')).toEqual({ val: 'x' });
    });

    it('getKey поддерживает точечную нотацию', () => {
      const store = createStore({ a: { b: { c: 99 } } });
      expect(store.getKey('a.b.c')).toBe(99);
    });

    it('getKey для несуществующего пути возвращает undefined', () => {
      const store = createStore({ a: 1 });
      expect(store.getKey('b')).toBeUndefined();
      expect(store.getKey('a.b.c')).toBeUndefined();
    });
  });

  describe('update — атомарные обновления', () => {
    it('обновляет состояние', () => {
      const store = createStore({ count: 0, name: 'foo' });
      store.update({ count: 1 });
      expect(store.getKey('count')).toBe(1);
      expect(store.getKey('name')).toBe('foo');
    });

    it('обновление по точечной нотации', () => {
      const store = createStore({ user: { name: 'Alice', age: 30 } });
      store.update({ 'user.name': 'Bob' });
      expect(store.getKey('user.name')).toBe('Bob');
      expect(store.getKey('user.age')).toBe(30);
    });

    it('патч не изменяет незатронутые ключи', () => {
      const store = createStore({ a: 1, b: 2, c: 3 });
      store.update({ b: 99 });
      expect(store.getState()).toEqual({ a: 1, b: 99, c: 3 });
    });

    it('генерирует исключение при рекурсивном вызове из подписчика', () => {
      const store = createStore({ x: 0 });
      store.subscribe('x', () => {
        expect(() => store.update({ y: 1 })).toThrow(
          '[StateManager] Рекурсивный вызов update запрещён',
        );
      });
      store.update({ x: 1 });
    });
  });

  describe('subscribe — подписка на изменения', () => {
    it('уведомляет подписчика при изменении ключа', () => {
      const store = createStore({ val: 0 });
      const fn = vi.fn();
      store.subscribe('val', fn);

      store.update({ val: 42 });
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith(42, 0);
    });

    it('НЕ уведомляет, если значение не изменилось', () => {
      const store = createStore({ val: 10 });
      const fn = vi.fn();
      store.subscribe('val', fn);

      store.update({ val: 10 });
      expect(fn).not.toHaveBeenCalled();
    });

    it('subscribeAll уведомляет при любом изменении', () => {
      const store = createStore({ a: 1, b: 2 });
      const fn = vi.fn();
      store.subscribeAll(fn);

      store.update({ a: 100 });
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('a', 100, 1);
    });

    it('subscribeAll с фильтром по ключу', () => {
      const store = createStore({ a: 1, b: 2 });
      const fn = vi.fn();
      store.subscribeAll(fn, 'a');

      store.update({ a: 10, b: 20 });
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('a', 10, 1);
    });

    it('отписка работает', () => {
      const store = createStore({ val: 0 });
      const fn = vi.fn();
      const unsub = store.subscribe('val', fn);
      unsub();

      store.update({ val: 1 });
      expect(fn).not.toHaveBeenCalled();
    });

    it('ошибка в подписчике не ломает других подписчиков', () => {
      const store = createStore({ val: 0 });

      const badFn = vi.fn(() => {
        throw new Error('oops');
      });
      const goodFn = vi.fn();

      store.subscribe('val', badFn);
      store.subscribe('val', goodFn);

      expect(() => store.update({ val: 1 })).not.toThrow();
      expect(goodFn).toHaveBeenCalledWith(1, 0);
    });
  });

  describe('persist — персистентность', () => {
    beforeEach(() => {
      mockLocalStorage();
    });

    it('сохраняет состояние в localStorage при update', () => {
      const store = createStore({ count: 0 }, { persist: true, key: 'test' });
      store.update({ count: 5 });

      const saved = JSON.parse(localStorage.getItem('test'));
      expect(saved).toEqual({ count: 5 });
    });

    it('восстанавливает состояние из localStorage при создании', () => {
      localStorage.setItem('test', JSON.stringify({ count: 99 }));

      const store = createStore({ count: 0 }, { persist: true, key: 'test' });
      expect(store.getKey('count')).toBe(99);
    });

    it('сбрасывает повреждённые данные при создании', () => {
      localStorage.setItem('test', 'not-json');

      const store = createStore({ count: 0 }, { persist: true, key: 'test' });
      expect(store.getKey('count')).toBe(0);
      expect(localStorage.getItem('test')).toBeNull();
    });

    it('невалидный тип (массив вместо объекта) сбрасывается', () => {
      localStorage.setItem('test', JSON.stringify([1, 2, 3]));

      const store = createStore({ count: 0 }, { persist: true, key: 'test' });
      expect(store.getKey('count')).toBe(0);
    });

    it('validate-функция может мигрировать данные', () => {
      localStorage.setItem('test', JSON.stringify({ name: 'old', version: 1 }));

      const validate = (data) => {
        if (data.version < 2) {
          return { ...data, version: 2, migrated: true };
        }
        return data;
      };

      const store = createStore(
        { name: '', version: 2, migrated: false },
        { persist: true, key: 'test', validate },
      );

      expect(store.getKey('version')).toBe(2);
      expect(store.getKey('migrated')).toBe(true);
    });

    it('validate возвращающая null сбрасывает состояние', () => {
      localStorage.setItem('test', JSON.stringify({ bad: 'data' }));

      const validate = () => null;

      const store = createStore({ good: 'default' }, { persist: true, key: 'test', validate });

      expect(store.getKey('good')).toBe('default');
      expect(localStorage.getItem('test')).toBeNull();
    });
  });

  describe('reset / destroy', () => {
    it('reset возвращает к начальному состоянию', () => {
      const store = createStore({ a: 1, b: 'x' });
      store.update({ a: 999, b: 'y' });
      store.reset();

      expect(store.getState()).toEqual({ a: 1, b: 'x' });
    });

    it('reset уведомляет подписчиков', () => {
      const store = createStore({ val: 10 });
      const fn = vi.fn();
      store.subscribe('val', fn);

      store.update({ val: 20 });
      store.reset();

      // После reset: val вернулось к 10, oldVal — 20
      expect(fn).toHaveBeenLastCalledWith(10, 20);
    });

    it('destroy очищает подписки', () => {
      const store = createStore({ val: 0 });
      const fn = vi.fn();
      store.subscribe('val', fn);

      store.destroy();
      store.update({ val: 1 });

      expect(fn).not.toHaveBeenCalled();
    });

    it('destroy удаляет данные из localStorage', () => {
      mockLocalStorage();
      const store = createStore({ val: 0 }, { persist: true, key: 'test' });
      store.update({ val: 5 });
      store.destroy();

      expect(localStorage.getItem('test')).toBeNull();
      clearStorageMock();
    });
  });
});
