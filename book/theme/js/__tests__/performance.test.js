/**
 * @file Unit-тесты для модуля производительности
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { debounce, throttle, batchRAF, memoize } from '../core/performance.js';

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('вызывает функцию после задержки', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced();
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('сбрасывает таймер при повторном вызове', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 200);

    debounced();
    vi.advanceTimersByTime(100);
    debounced(); // сброс
    vi.advanceTimersByTime(100);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('leading option вызывает fn немедленно', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100, { leading: true });

    debounced();
    expect(fn).toHaveBeenCalledTimes(1);

    // trailing-вызов тоже происходит (стандартное поведение leading+trailing)
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('несколько вызовов при leading не дублируют немедленный вызов', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100, { leading: true });

    debounced();
    debounced();
    debounced();
    expect(fn).toHaveBeenCalledTimes(1); // только первый leading

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(2); // trailing с последними аргументами
  });

  it('.cancel отменяет вызов', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced();
    debounced.cancel();
    vi.advanceTimersByTime(100);

    expect(fn).not.toHaveBeenCalled();
  });

  it('.flush немедленно выполняет отложенный вызов', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced();
    debounced.flush();

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('сохраняет контекст и аргументы', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 50);

    const ctx = { value: 42 };
    debounced.call(ctx, 'a', 'b');
    vi.advanceTimersByTime(50);

    expect(fn).toHaveBeenCalledWith('a', 'b');
  });
});

describe('throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('вызывает fn не чаще заданного интервала', () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);

    throttled();
    expect(fn).toHaveBeenCalledTimes(1);

    throttled();
    throttled();
    expect(fn).toHaveBeenCalledTimes(1); // не вызывается повторно

    vi.advanceTimersByTime(100);
    // trailing call
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('trailing=false отключает вызов в конце', () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100, { trailing: false });

    throttled();
    vi.advanceTimersByTime(50);
    throttled(); // игнорируется
    vi.advanceTimersByTime(100);

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('.cancel отменяет trailing вызов', () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);

    throttled();
    throttled(); // планирует trailing
    throttled.cancel();
    vi.advanceTimersByTime(100);

    expect(fn).toHaveBeenCalledTimes(1);
  });
});

describe('batchRAF', () => {
  it('группирует вызовы в один RAF', () => {
    vi.useFakeTimers();
    const batch = batchRAF();
    const fn1 = vi.fn();
    const fn2 = vi.fn();

    batch.schedule(fn1);
    batch.schedule(fn2);

    expect(fn1).not.toHaveBeenCalled();
    expect(fn2).not.toHaveBeenCalled();

    vi.advanceTimersByTime(20); // RAF callback
    expect(fn1).toHaveBeenCalledTimes(1);
    expect(fn2).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('flush немедленно выполняет все задачи', () => {
    const batch = batchRAF();
    const fn = vi.fn();

    batch.schedule(fn);
    batch.flush();

    expect(fn).toHaveBeenCalledTimes(1);
  });
});

describe('memoize', () => {
  it('кеширует результат функции', () => {
    const fn = vi.fn((x) => x * 2);
    const memoized = memoize(fn);

    expect(memoized(5)).toBe(10);
    expect(memoized(5)).toBe(10);
    expect(fn).toHaveBeenCalledTimes(1); // второй вызов из кеша
  });

  it('различает разные аргументы', () => {
    const fn = vi.fn((x) => x * 2);
    const memoized = memoize(fn);

    memoized(1);
    memoized(2);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('.clear очищает кеш', () => {
    const fn = vi.fn((x) => x * 2);
    const memoized = memoize(fn);

    memoized(5);
    memoized.clear();
    memoized(5);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('ограничивает размер кеша', () => {
    const fn = vi.fn((x) => x);
    const memoized = memoize(fn, 2);

    memoized('a');
    memoized('b');
    memoized('c'); // 'a' вытесняется
    memoized('a'); // снова вычисляется
    expect(fn).toHaveBeenCalledTimes(4);
  });
});
