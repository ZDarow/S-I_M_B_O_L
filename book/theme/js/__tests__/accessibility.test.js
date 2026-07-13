/**
 * @file Unit-тесты для модуля доступности
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { A11y } from '../core/accessibility.js';

describe('A11y', () => {
  beforeEach(() => {
    document.body.innerHTML = '<main id="main-content"><p>Content</p></main>';
    // Мок для методов, недоступных в jsdom
    Element.prototype.scrollIntoView = vi.fn();
    // Мок matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('createSkipLink', () => {
    it('создаёт skip-link и вставляет в начало body', () => {
      const link = A11y.createSkipLink('main-content');
      expect(link).toBeInstanceOf(HTMLAnchorElement);
      expect(link.className).toContain('a11y-skip-link');
      expect(link.getAttribute('href')).toBe('#main-content');
      expect(link.textContent).toBe('Перейти к содержимому');
      // Должен быть первым ребенком body
      expect(document.body.firstChild).toBe(link);
    });

    it('заменяет предыдущий skip-link', () => {
      A11y.createSkipLink('main', 'Первый');
      A11y.createSkipLink('main', 'Второй');
      const links = document.querySelectorAll('.a11y-skip-link');
      expect(links.length).toBe(1);
      expect(links[0].textContent).toBe('Второй');
    });

    it('фокусирует целевой элемент по клику', () => {
      const link = A11y.createSkipLink('main-content');
      link.click();
      const target = document.getElementById('main-content');
      expect(document.activeElement).toBe(target);
    });
  });

  describe('focus', () => {
    it('save/restore контекст фокуса', () => {
      const btn = document.createElement('button');
      btn.id = 'test-btn';
      document.body.appendChild(btn);
      btn.focus();

      A11y.focus.saveContext();
      document.body.appendChild(document.createElement('div')).focus();
      A11y.focus.restoreContext();

      expect(document.activeElement).toBe(btn);
    });

    it('trap запирает фокус внутри контейнера', () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <button id="b1">First</button>
        <button id="b2">Second</button>
        <button id="b3">Third</button>
      `;
      document.body.appendChild(container);

      const release = A11y.focus.trap(container);
      // Первый элемент должен получить фокус
      expect(document.activeElement).toBe(document.getElementById('b1'));

      // Симуляция Tab — фокус на второй
      document.getElementById('b2').focus();
      expect(document.activeElement).toBe(document.getElementById('b2'));

      // Tab на последнем — возврат к первому
      document.getElementById('b3').focus();
      const event = new KeyboardEvent('keydown', { key: 'Tab' });
      container.dispatchEvent(event);
      expect(document.activeElement).toBe(document.getElementById('b1'));

      release();
    });

    it('focusVisible делает элемент фокусируемым и фокусирует его', () => {
      const div = document.createElement('div');
      div.textContent = 'test';
      document.body.appendChild(div);

      A11y.focus.focusVisible(div);
      expect(div.getAttribute('tabindex')).toBe('-1');
      expect(document.activeElement).toBe(div);
    });
  });

  describe('keyboard', () => {
    it('activate вызывает хендлер на Enter и Space', () => {
      const btn = document.createElement('button');
      document.body.appendChild(btn);

      const handler = vi.fn();
      A11y.keyboard.activate(btn, handler);

      btn.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
      expect(handler).toHaveBeenCalledTimes(1);

      btn.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }));
      expect(handler).toHaveBeenCalledTimes(2);
    });

    it('arrowKeys передаёт направление', () => {
      const div = document.createElement('div');
      document.body.appendChild(div);

      const handler = vi.fn();
      A11y.keyboard.arrowKeys(div, handler);

      div.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }));
      expect(handler).toHaveBeenCalledWith('up', expect.any(Event));

      div.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
      expect(handler).toHaveBeenCalledWith('right', expect.any(Event));
    });

    it('escape вызывает хендлер на Escape', () => {
      const div = document.createElement('div');
      document.body.appendChild(div);

      const handler = vi.fn();
      A11y.keyboard.escape(div, handler);

      div.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(handler).toHaveBeenCalledTimes(1);

      div.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
      expect(handler).toHaveBeenCalledTimes(1); // не увеличилось
    });

    it('rovingTabindex инициализирует tabindex: первый 0, остальные -1', () => {
      const container = document.createElement('div');
      container.innerHTML = `
        <div class="item">A</div>
        <div class="item">B</div>
        <div class="item">C</div>
      `;
      document.body.appendChild(container);

      A11y.keyboard.rovingTabindex(container, '.item');
      const items = container.querySelectorAll('.item');

      expect(items[0].getAttribute('tabindex')).toBe('0');
      expect(items[1].getAttribute('tabindex')).toBe('-1');
      expect(items[2].getAttribute('tabindex')).toBe('-1');
    });
  });

  describe('aria', () => {
    it('set устанавливает атрибуты, конвертируя boolean', () => {
      const el = document.createElement('button');
      A11y.aria.set(el, {
        role: 'tab',
        'aria-expanded': false,
        'aria-label': 'test',
      });

      expect(el.getAttribute('role')).toBe('tab');
      expect(el.getAttribute('aria-expanded')).toBe('false');
      expect(el.getAttribute('aria-label')).toBe('test');
    });

    it('liveRegion создаёт и переиспользует регион', () => {
      const r1 = A11y.aria.liveRegion('test-live');
      expect(r1.getAttribute('aria-live')).toBe('polite');
      expect(r1.className).toContain('a11y-sr-only');

      const r2 = A11y.aria.liveRegion('test-live');
      expect(r2).toBe(r1); // тот же элемент
    });

    it('announce устанавливает текст в live region', () => {
      vi.useFakeTimers();
      A11y.aria.announce('Тестовое сообщение');
      vi.runAllTimers();

      const region = document.getElementById('a11y-live-region');
      expect(region.textContent).toBe('Тестовое сообщение');
      vi.useRealTimers();
    });
  });

  describe('motion', () => {
    it('prefersReduced возвращает boolean', () => {
      const result = A11y.motion.prefersReduced();
      expect(typeof result).toBe('boolean');
    });

    it('safeAnimate вызывает fn напрямую при reduced motion', () => {
      // Переопределяем matchMedia для имитации reduced motion
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const fn = vi.fn();
      A11y.motion.safeAnimate(fn);
      expect(fn).toHaveBeenCalledTimes(1);
    });
  });

  describe('setCurrentNav', () => {
    it('устанавливает aria-current', () => {
      const nav = document.createElement('nav');
      nav.innerHTML = `
        <a href="/page1" data-current="true">Page 1</a>
        <a href="/page2">Page 2</a>
      `;
      document.body.appendChild(nav);

      A11y.setCurrentNav(nav, 'a');
      const links = nav.querySelectorAll('a');
      expect(links[0].getAttribute('aria-current')).toBe('page');
      expect(links[1].getAttribute('aria-current')).toBe('false');
    });
  });

  describe('init', () => {
    it('создаёт skip-link и live region', () => {
      const sidebar = document.createElement('div');
      sidebar.id = 'mdbook-sidebar';
      document.body.appendChild(sidebar);

      A11y.init({ skipTo: 'main-content' });

      expect(document.querySelector('.a11y-skip-link')).toBeTruthy();
      expect(document.getElementById('a11y-live-region')).toBeTruthy();
    });
  });
});
