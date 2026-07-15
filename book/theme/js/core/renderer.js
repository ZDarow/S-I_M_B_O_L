/**
 * @file Система шаблонов и рендеринга для отделения логики от представления.
 *
 * Все функции-рендереры возвращают DOM-элементы (или DocumentFragment),
 * не работают с состоянием и не содержат бизнес-логики.
 *
 * @example
 *   import { html, render, For, Show, Fragment } from './renderer.js';
 *
 *   // Простой рендер
 *   const btn = html`<button class="btn">Нажми меня</button>`;
 *
 *   // Условный рендеринг
 *   const el = Show(items.length > 0,
 *     () => html`<ul>${items.map(i => html`<li>${i}</li>`)}</ul>`,
 *     () => html`<p>Нет элементов</p>`
 *   );
 *
 *   // Цикл
 *   const list = For(items, (item, idx) =>
 *     html`<li data-index="${idx}">${item.name}</li>`
 *   );
 */

// ─── Symbol для идентификации компонентов ────────────────────────
const COMPONENT = Symbol('component');

// ─── Экранирование HTML (защита от XSS) ─────────────────────────
/**
 * Экранировать строку для безопасной вставки в HTML.
 * @param {*} value
 * @returns {string}
 */
export function escapeHtml(value) {
  if (value === null || value === undefined) {
    return '';
  }
  const str = String(value);
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ─── Tagged template literal → DOM ───────────────────────────────

/**
 * Tagged template literal для создания DOM-элементов.
 * Поддерживает вложенные элементы, строки, числа, массивы, null.
 *
 * @param {TemplateStringsArray} strings
 * @param {...*} values
 * @returns {DocumentFragment}
 *
 * @example
 *   const frag = html`<div class="${cls}">${content}</div>`;
 */
export function html(strings, ...values) {
  // Префикс для маркеров (достаточно уникален, чтобы не пересекаться с контентом)
  const MARKER = '\x7fHTML\x7f';

  // Собираем итоговую строку HTML, заменяя DOM-значения на маркеры
  let result = '';
  let markerCounter = 0;
  /** @type {Array<{ marker: string, value: Node|DocumentFragment, isComponent: boolean }>} */
  const markerMap = [];

  // Рекурсивно разворачиваем значения, собирая DOM-узлы
  function processValue(v) {
    if (v === null || v === undefined) {
      return;
    }
    if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
      return escapeHtml(v);
    }
    if (Array.isArray(v)) {
      return v.map(processValue).join('');
    }
    // DOM-узел или компонент
    if (v && typeof v === 'object') {
      if (v[COMPONENT]) {
        markerMap.push({ marker: MARKER + markerCounter, value: v, isComponent: true });
        return MARKER + markerCounter++;
      }
      if (v.nodeType) {
        markerMap.push({ marker: MARKER + markerCounter, value: v, isComponent: false });
        return MARKER + markerCounter++;
      }
    }
    return escapeHtml(v);
  }

  for (let i = 0; i < strings.length; i++) {
    result += strings[i];
    if (i < values.length) {
      result += processValue(values[i]) || '';
    }
  }

  // Парсим HTML
  const template = document.createElement('template');
  template.innerHTML = result.trim();
  const frag = template.content;

  // Заменяем маркеры на DOM-узлы
  if (markerMap.length > 0) {
    // Сортируем маркеры по убыванию длины, чтобы более длинные проверять раньше
    const sortedMarkers = [...markerMap].sort((a, b) => b.marker.length - a.marker.length);

    // Собираем все текстовые узлы
    const walker = document.createTreeWalker(frag, NodeFilter.SHOW_TEXT, null);

    const textNodes = [];
    while (walker.nextNode()) {
      textNodes.push(walker.currentNode);
    }

    for (const textNode of textNodes) {
      const content = textNode.nodeValue || '';

      // Проверяем, содержит ли узел хотя бы один маркер
      const hasMarker = sortedMarkers.some((e) => content.includes(e.marker));
      if (!hasMarker) {
        continue;
      }

      const parent = textNode.parentNode;
      if (!parent) {
        continue;
      }

      const fragment = document.createDocumentFragment();

      // Разбиваем содержимое по всем маркерам по порядку
      let remaining = content;

      while (remaining.length > 0) {
        let earliestPos = remaining.length;
        let earliestEntry = null;

        for (const entry of sortedMarkers) {
          const pos = remaining.indexOf(entry.marker);
          if (pos !== -1 && pos < earliestPos) {
            earliestPos = pos;
            earliestEntry = entry;
          }
        }

        if (earliestEntry === null) {
          // Оставшийся текст без маркеров
          if (remaining) {
            fragment.appendChild(document.createTextNode(remaining));
          }
          break;
        }

        // Текст перед маркером
        if (earliestPos > 0) {
          fragment.appendChild(document.createTextNode(remaining.slice(0, earliestPos)));
        }

        // Вставляем DOM-узел вместо маркера
        const node = earliestEntry.isComponent ? earliestEntry.value.render() : earliestEntry.value;
        fragment.appendChild(node);

        // Продолжаем с остатком после маркера
        remaining = remaining.slice(earliestPos + earliestEntry.marker.length);
      }

      parent.replaceChild(fragment, textNode);
    }
  }

  return frag;
}

// ─── Шаблонизатор: создание элемента с атрибутами ───────────────

/**
 * Создать DOM-элемент с атрибутами и дочерними элементами.
 * Низкоуровневая альтернатива `html` для случаев, когда нужен
 * точный контроль.
 *
 * @param {string} tag
 * @param {Object<string, string|boolean|number>} [attrs]
 * @param {...(Node|string|number|null|undefined)} children
 * @returns {HTMLElement}
 */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);

  for (const [key, val] of Object.entries(attrs)) {
    if (val === null || val === undefined) {
      continue;
    }
    if (key.startsWith('on')) {
      const event = key.slice(2).toLowerCase();
      el.addEventListener(event, val);
    } else if (typeof val === 'boolean') {
      el.setAttribute(key, val ? 'true' : 'false');
    } else {
      el.setAttribute(key, String(val));
    }
  }

  for (const child of children) {
    if (child === null || child === undefined) {
      continue;
    }
    if (child instanceof Node) {
      el.appendChild(child);
    } else if (Array.isArray(child)) {
      child.forEach((c) => {
        if (c instanceof Node) {
          el.appendChild(c);
        } else {
          el.appendChild(document.createTextNode(String(c)));
        }
      });
    } else {
      el.appendChild(document.createTextNode(String(child)));
    }
  }

  return el;
}

// ─── Условный рендеринг ─────────────────────────────────────────

/**
 * Условный рендеринг: возвращает результат `thenFn` если условие истинно,
 * иначе `elseFn`.
 *
 * @param {boolean} condition
 * @param {function(): (Node|DocumentFragment)} thenFn
 * @param {function(): (Node|DocumentFragment)} [elseFn]
 * @returns {Node|DocumentFragment}
 */
export function Show(condition, thenFn, elseFn) {
  if (condition) {
    return thenFn();
  }
  if (elseFn) {
    return elseFn();
  }
  return document.createComment('Show:false');
}

// ─── Цикл ────────────────────────────────────────────────────────

/**
 * Рендеринг списка элементов.
 *
 * @template T
 * @param {T[]} items
 * @param {function(T, number): (Node|DocumentFragment)} fn  Получает (item, index)
 * @returns {DocumentFragment}
 */
export function For(items, fn) {
  const frag = document.createDocumentFragment();
  if (!items || items.length === 0) {
    return frag;
  }
  for (let i = 0; i < items.length; i++) {
    const child = fn(items[i], i);
    if (child) {
      frag.appendChild(child);
    }
  }
  return frag;
}

// ─── Компонент ──────────────────────────────────────────────────

/**
 * Создать компонент с функцией-рендерером.
 * Компонент — это объект с методом render().
 *
 * @param {function(): (Node|DocumentFragment)} renderFn
 * @returns {Object}  Компонент с методом render()
 *
 * @example
 *   const Button = Component(({ label, onClick }) =>
 *     h('button', { class: 'btn', onClick }, label)
 *   );
 *   // Использование: Button.render({ label: 'OK', onClick: handler })
 */
export function Component(renderFn) {
  return {
    [COMPONENT]: true,
    render: renderFn,
  };
}

// ─── Fragment ────────────────────────────────────────────────────

/**
 * Создать DocumentFragment из массива узлов.
 * @param {...(Node|DocumentFragment|string)} nodes
 * @returns {DocumentFragment}
 */
export function Fragment(...nodes) {
  const frag = document.createDocumentFragment();
  for (const node of nodes) {
    if (node instanceof Node) {
      frag.appendChild(node);
    } else if (typeof node === 'string') {
      frag.appendChild(document.createTextNode(node));
    }
  }
  return frag;
}

// ─── Render (монтирование) ──────────────────────────────────────

/**
 * Отрендерить и смонтировать результат в целевой элемент.
 *
 * @param {HTMLElement} target
 * @param {(Node|DocumentFragment)} content
 */
export function render(target, content) {
  target.innerHTML = '';
  if (content instanceof DocumentFragment) {
    target.appendChild(content);
  } else if (content instanceof Node) {
    target.appendChild(content);
  }
}

// ─── Patch (обновление через diff) ──────────────────────────────

/**
 * Обновить содержимое элемента, сохраняя ссылку на родителя.
 * Удаляет старые дочерние элементы и добавляет новые.
 *
 * @param {HTMLElement} target
 * @param {(Node|DocumentFragment)} content
 */
export function patch(target, content) {
  // Сохраняем ссылки на children до очистки
  const oldChildren = Array.from(target.childNodes);

  // Очищаем
  while (target.firstChild) {
    target.removeChild(target.firstChild);
  }

  // Добавляем новое содержимое
  if (content instanceof DocumentFragment) {
    target.appendChild(content);
  } else if (content instanceof Node) {
    target.appendChild(content);
  }

  // Освобождаем ссылки (GC)
  oldChildren.length = 0;
}

// ─── XSS-безопасный HTML для контента (внутренний) ─────────────

/**
 * Создать текстовый узел с экранированием.
 * @param {*} value
 * @returns {Text}
 */
export function text(value) {
  return document.createTextNode(String(value ?? ''));
}
