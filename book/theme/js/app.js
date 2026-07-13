/**
 * @file Главный модуль приложения.
 * Инициализирует все подсистемы: состояние, доступность,
 * производительность, мобильные улучшения.
 *
 * Загружается как ES-модуль через <script type="module">
 * в index.hbs.
 */

import { A11y } from './core/accessibility.js';
import { initPerformance } from './core/performance.js';
import { initMobile } from './core/mobile.js';
import { createStore } from './core/state-manager.js';
import { initDtcSearch } from './widgets/dtc-search.js';
import { initServiceTracker } from './widgets/service-tracker.js';

// ─── Глобальное хранилище приложения ────────────────────────────

/**
 * Основное хранилище состояния приложения.
 * Доступно через window.__APP_STORE для отладки.
 *
 * @type {import('./core/state-manager.js').Store}
 */
export const appStore = createStore(
  {
    theme: 'light',
    sidebar: 'visible',
    preferences: {
      reducedMotion: false,
      contrast: 'normal',
    },
    widgets: {
      dtcSearchActive: false,
      serviceTrackerActive: false,
    },
  },
  {
    persist: true,
    key: 'reno-symbol-app-state',
    validate: (data) => {
      // Миграция: если нет раздела widgets, добавляем
      if (!data.widgets) {
        data.widgets = { dtcSearchActive: false, serviceTrackerActive: false };
      }
      return data;
    },
  },
);

if (typeof window !== 'undefined') {
  window.__APP_STORE = appStore;
}

// ─── Инициализация ──────────────────────────────────────────────

/**
 * Запуск всех подсистем.
 */
export function initApp() {
  // Доступность
  A11y.init({
    skipTo: 'mdbook-content',
    skipLabel: 'Перейти к содержимому',
  });

  // Производительность
  initPerformance();

  // Мобильные улучшения
  const cleanupMobile = initMobile();

  // Сохранение предпочтений по движению
  A11y.motion.onChange((reduced) => {
    appStore.update({ 'preferences.reducedMotion': reduced });
  });

  // Виджеты (рефакторенные, если legacy-скрипты не перехватили контейнеры)
  const cleanupDtc = initDtcSearch();
  const cleanupTracker = initServiceTracker();

  // Возвращаем функцию очистки
  return () => {
    cleanupMobile();
    cleanupDtc();
    cleanupTracker();
  };
}

// Автозапуск
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

export default {
  appStore,
  initApp,
};
