/**
 * Конфигурация Vitest для тестирования JS-модулей темы
 */
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['book/theme/js/__tests__/**/*.test.js'],
    environment: 'jsdom',
    globals: false,
  },
});
