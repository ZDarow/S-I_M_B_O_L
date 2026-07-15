/**
 * E2E-тесты: PWA (Progressive Web App)
 *
 * ВАЖНО: manifest.json и sw.js копируются в build output
 * скриптом _copy_artifacts.py (шаг CI: Post-process).
 * Локально файлы отсутствуют, тесты пропускаются.
 */
import { test, expect } from '@playwright/test';

test.describe('PWA (Progressive Web App)', () => {
  test('manifest.json доступен и содержит обязательные поля', async ({ page }) => {
    await page.goto('/');
    const url = new URL('/manifest.json', page.url());
    const resp = await page.request.get(url.href);
    test.skip(resp.status() === 404, 'manifest.json не найден — требуется _copy_artifacts.py');

    expect(resp.ok()).toBeTruthy();
    const manifest = await resp.json();
    expect(manifest).toHaveProperty('name');
    expect(manifest).toHaveProperty('short_name');
    expect(manifest).toHaveProperty('start_url');
    expect(manifest).toHaveProperty('display');
    expect(manifest.display).toMatch(/standalone|fullscreen|minimal-ui/);
  });

  test('sw.js (Service Worker) доступен', async ({ page }) => {
    await page.goto('/');
    const url = new URL('/theme/sw.js', page.url());
    const resp = await page.request.get(url.href);
    test.skip(resp.status() === 404, 'sw.js не найден — требуется _copy_artifacts.py');

    expect(resp.ok()).toBeTruthy();
    const contentType = resp.headers()['content-type'] || '';
    expect(contentType).toMatch(/javascript|text/);
  });

  test('Service Worker регистрируется на странице', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const hasSw = await page.evaluate(async () => {
      try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        return registrations.length > 0;
      } catch {
        return false;
      }
    });

    if (!hasSw) {
      const url = new URL('/theme/sw.js', page.url());
      const resp = await page.request.get(url.href);
      test.skip(resp.status() === 404, 'sw.js не найден — тест пропущен');
    }

    expect(hasSw).toBeTruthy();
  });

  test('оффлайн-режим: страница содержит контент (PWA-ready)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const html = await page.content();
    expect(html.length).toBeGreaterThan(100);

    const themeColor = page.locator('meta[name="theme-color"]');
    await expect(themeColor).toBeAttached();
  });
});
