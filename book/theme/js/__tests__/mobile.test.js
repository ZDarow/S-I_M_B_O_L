/**
 * @file Unit-тесты для модуля mobile
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  checkTouchTarget,
  ensureTouchTarget,
  detectSwipe,
  createSpinner,
  toggleSpinner,
  enhanceTables,
  downloadJSON,
} from '../core/mobile.js';

describe('checkTouchTarget', () => {
  it('возвращает valid=true для элемента >= 44x44', () => {
    const el = document.createElement('button');
    Object.defineProperty(el, 'getBoundingClientRect', {
      value: () => ({ width: 44, height: 44, top: 0, left: 0, right: 44, bottom: 44 }),
    });
    const result = checkTouchTarget(el);
    expect(result.valid).toBe(true);
  });

  it('возвращает valid=false для элемента < 44x44', () => {
    const el = document.createElement('button');
    Object.defineProperty(el, 'getBoundingClientRect', {
      value: () => ({ width: 20, height: 20, top: 0, left: 0, right: 20, bottom: 20 }),
    });
    const result = checkTouchTarget(el);
    expect(result.valid).toBe(false);
  });
});

describe('ensureTouchTarget', () => {
  it('добавляет padding до 44x44', () => {
    const el = document.createElement('button');
    Object.defineProperty(el, 'getBoundingClientRect', {
      value: () => ({ width: 20, height: 20, top: 0, left: 0, right: 20, bottom: 20 }),
    });
    const changed = ensureTouchTarget(el);
    expect(changed).toBe(true);
    expect(el.style.paddingLeft).toBeTruthy();
    expect(el.style.paddingTop).toBeTruthy();
  });

  it('не меняет элемент, если он уже >= 44x44', () => {
    const el = document.createElement('button');
    Object.defineProperty(el, 'getBoundingClientRect', {
      value: () => ({ width: 100, height: 100, top: 0, left: 0, right: 100, bottom: 100 }),
    });
    const changed = ensureTouchTarget(el);
    expect(changed).toBe(false);
  });
});

describe('detectSwipe', () => {
  it('определяет свайп вправо', () => {
    const el = document.createElement('div');
    const handler = vi.fn();
    detectSwipe(el, handler);

    el.dispatchEvent(
      new TouchEvent('touchstart', {
        touches: [{ clientX: 0, clientY: 0 }],
      }),
    );

    el.dispatchEvent(
      new TouchEvent('touchend', {
        changedTouches: [{ clientX: 100, clientY: 0 }],
      }),
    );

    expect(handler).toHaveBeenCalledWith('right', expect.any(Number));
  });

  it('определяет свайп вверх', () => {
    const el = document.createElement('div');
    const handler = vi.fn();
    detectSwipe(el, handler);

    el.dispatchEvent(
      new TouchEvent('touchstart', {
        touches: [{ clientX: 0, clientY: 100 }],
      }),
    );

    el.dispatchEvent(
      new TouchEvent('touchend', {
        changedTouches: [{ clientX: 0, clientY: 0 }],
      }),
    );

    expect(handler).toHaveBeenCalledWith('up', expect.any(Number));
  });
});

describe('spinner', () => {
  it('createSpinner возвращает элемент с role=status', () => {
    const spinner = createSpinner('Загрузка...');
    expect(spinner.className).toBe('spinner-indicator');
    expect(spinner.getAttribute('role')).toBe('status');
    expect(spinner.querySelector('.spinner-text')?.textContent).toBe('Загрузка...');
  });

  it('toggleSpinner добавляет/удаляет индикатор', () => {
    const container = document.createElement('div');
    toggleSpinner(container, true, 'Тест');
    expect(container.querySelector('.spinner-indicator')).toBeTruthy();

    toggleSpinner(container, false);
    expect(container.querySelector('.spinner-indicator')).toBeNull();
  });
});

describe('enhanceTables', () => {
  it('оборачивает таблицу в скроллящийся контейнер', () => {
    const container = document.createElement('div');
    container.className = 'content';
    container.innerHTML =
      '<table><thead><tr><th>Заголовок</th></tr></thead><tbody><tr><td>Данные</td></tr></tbody></table>';
    document.body.appendChild(container);

    enhanceTables(container);

    const wrapper = container.querySelector('.table-wrapper-enhanced');
    expect(wrapper).toBeTruthy();
    expect(wrapper.style.overflowX).toBe('auto');

    // Таблица внутри wrapper
    expect(wrapper.querySelector('table')).toBeTruthy();

    document.body.removeChild(container);
  });
});

describe('downloadJSON', () => {
  it('создаёт ссылку для скачивания', () => {
    // Мокаем createObjectURL и appendChild
    const originalCreateObjectURL = URL.createObjectURL;
    const originalRevokeObjectURL = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn(() => 'blob:test');
    URL.revokeObjectURL = vi.fn();

    const appendChildSpy = vi.spyOn(document.body, 'appendChild');
    const removeChildSpy = vi.spyOn(document.body, 'removeChild');

    downloadJSON({ key: 'value' }, 'test.json');

    // Должна быть создана ссылка
    expect(appendChildSpy).toHaveBeenCalled();
    expect(URL.createObjectURL).toHaveBeenCalled();

    // Восстанавливаем
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });
});
