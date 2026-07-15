/**
 * @file Unit-тесты для модуля рендеринга
 */

import { describe, it, expect, vi } from 'vitest';
import {
  html,
  h,
  Show,
  For,
  Component,
  Fragment,
  render,
  patch,
  escapeHtml,
  text,
} from '../core/renderer.js';

describe('escapeHtml', () => {
  it('экранирует спецсимволы', () => {
    expect(escapeHtml('<script>alert("xss")</script>')).toBe(
      '&lt;script&gt;alert("xss")&lt;/script&gt;',
    );
  });

  it('возвращает пустую строку для null/undefined', () => {
    expect(escapeHtml(null)).toBe('');
    expect(escapeHtml(undefined)).toBe('');
  });
});

describe('h', () => {
  it('создаёт элемент с тегом и атрибутами', () => {
    const el = h('div', { class: 'test', id: 'foo' }, 'Привет');
    expect(el.tagName).toBe('DIV');
    expect(el.className).toBe('test');
    expect(el.id).toBe('foo');
    expect(el.textContent).toBe('Привет');
  });

  it('обрабатывает boolean атрибуты', () => {
    const el = h('button', { disabled: true, hidden: false });
    expect(el.getAttribute('disabled')).toBe('true');
    expect(el.getAttribute('hidden')).toBe('false');
  });

  it('обрабатывает события on*', () => {
    const handler = vi.fn();
    const el = h('button', { onClick: handler });
    el.click();
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('добавляет дочерние элементы', () => {
    const child = h('span', {}, 'child');
    const parent = h('div', {}, child, ' text ');
    expect(parent.children.length).toBe(1);
    expect(parent.childNodes.length).toBe(2); // span + text
  });
});

describe('html', () => {
  it('создаёт фрагмент из шаблона', () => {
    const frag = html`<div class="test">Hello</div>`;
    expect(frag).toBeInstanceOf(DocumentFragment);
    const div = frag.firstElementChild;
    expect(div?.tagName).toBe('DIV');
    expect(div?.textContent).toBe('Hello');
  });

  it('вставляет дочерние DOM-элементы', () => {
    const child = h('span', {}, 'world');
    const frag = html`<p>Hello ${child}</p>`;
    const p = frag.firstElementChild;
    expect(p?.textContent).toBe('Hello world');
  });

  it('экранирует строковые значения', () => {
    const frag = html`<p>${'<b>bold</b>'}</p>`;
    const p = frag.firstElementChild;
    expect(p?.innerHTML).toBe('&lt;b&gt;bold&lt;/b&gt;');
  });

  it('обрабатывает массивы элементов', () => {
    const items = ['a', 'b', 'c'].map((x) => h('li', {}, x));
    const frag = html`<ul>
      ${items}
    </ul>`;
    const ul = frag.firstElementChild;
    expect(ul?.children.length).toBe(3);
  });

  it('принимает null/undefined значения', () => {
    const frag = html`<p>${null}${undefined}</p>`;
    const p = frag.firstElementChild;
    expect(p?.textContent).toBe('');
  });
});

describe('Show', () => {
  it('выполняет thenFn при истинном условии', () => {
    const result = Show(true, () => h('div', {}, 'visible'));
    expect(result).toBeInstanceOf(HTMLElement);
    expect(result.textContent).toBe('visible');
  });

  it('выполняет elseFn при ложном условии', () => {
    const result = Show(
      false,
      () => h('div', {}, 'visible'),
      () => h('p', {}, 'fallback'),
    );
    expect(result.textContent).toBe('fallback');
  });

  it('возвращает comment при ложном условии без elseFn', () => {
    const result = Show(false, () => h('div', {}));
    expect(result.nodeType).toBe(Node.COMMENT_NODE);
  });
});

describe('For', () => {
  it('рендерит список элементов', () => {
    const items = ['A', 'B', 'C'];
    const frag = For(items, (item, idx) => h('li', { 'data-index': idx }, item));
    expect(frag.children.length).toBe(3);
    expect(frag.children[0].textContent).toBe('A');
    expect(frag.children[1].textContent).toBe('B');
    expect(frag.children[2].textContent).toBe('C');
  });

  it('возвращает пустой фрагмент для пустого массива', () => {
    const frag = For([], (item) => h('li', {}, item));
    expect(frag.children.length).toBe(0);
  });
});

describe('Component', () => {
  it('создаёт компонент с методом render', () => {
    const Greeting = Component(({ name }) => h('p', {}, `Hello, ${name}!`));
    const el = Greeting.render({ name: 'World' });
    expect(el.textContent).toBe('Hello, World!');
  });
});

describe('Fragment', () => {
  it('создаёт фрагмент из узлов', () => {
    const frag = Fragment(h('span', {}, 'one'), ' ', h('span', {}, 'two'));
    expect(frag.childNodes.length).toBe(3);
  });
});

describe('render / patch', () => {
  it('render добавляет содержимое в целевой элемент', () => {
    const target = document.createElement('div');
    const content = h('p', {}, 'hello');
    render(target, content);
    expect(target.children.length).toBe(1);
    expect(target.textContent).toBe('hello');
  });

  it('patch заменяет содержимое', () => {
    const target = document.createElement('div');
    target.innerHTML = '<span>old</span>';

    const newContent = h('p', {}, 'new');
    patch(target, newContent);

    expect(target.children.length).toBe(1);
    expect(target.firstElementChild?.tagName).toBe('P');
    expect(target.textContent).toBe('new');
  });
});

describe('text', () => {
  it('создаёт текстовый узел', () => {
    const node = text('Hello');
    expect(node.nodeType).toBe(Node.TEXT_NODE);
    expect(node.textContent).toBe('Hello');
  });

  it('экранирует null/undefined в пустую строку', () => {
    expect(text(null).textContent).toBe('');
    expect(text(undefined).textContent).toBe('');
  });
});
