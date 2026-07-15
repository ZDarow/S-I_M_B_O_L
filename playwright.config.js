/**
 * Конфигурация Playwright для E2E-тестирования
 *
 * Тесты запускаются против сервера разработки (mdbook serve)
 * или против уже собранного сайта (http-сервер из book/book/html/).
 *
 * CI: сборка mdBook → python3 -m http.server → npx playwright test
 */
import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'list',
  timeout: 30_000,

  use: {
    baseURL: BASE_URL,
    trace: process.env.CI ? 'on-first-retry' : 'off',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  /* Запуск локального сервера для тестов */
  webServer: process.env.CI
    ? undefined
    : {
        command: 'python3 -m http.server 3000 --directory book/book/html',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        cwd: '.',
      },
});
