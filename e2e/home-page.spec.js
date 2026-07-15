/**
 * E2E-тесты: загрузка главной страницы и навигация
 */
import { test, expect } from '@playwright/test';

test.describe('Главная страница', () => {
  test('загружается с корректным заголовком', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.ok()).toBeTruthy();

    const title = await page.title();
    expect(title).toContain('Renault Symbol');
  });

  test('содержит навигационное меню mdBook', async ({ page }) => {
    await page.goto('/');

    // Проверяем, что меню навигации присутствует
    const nav = page.locator('nav.chapter, nav.sidebar, #sidebar');
    await expect(nav.first()).toBeVisible({ timeout: 5000 });
  });

  test('переход по ссылке в содержании открывает новую страницу', async ({ page }) => {
    await page.goto('/');

    // Кликаем по первой ссылке в содержании
    const firstLink = page.locator('ol.chapter li a, .sidebar li a').first();
    await firstLink.waitFor({ state: 'visible', timeout: 5000 });

    const href = await firstLink.getAttribute('href');
    await firstLink.click();
    await page.waitForLoadState('networkidle');

    // Проверяем, что URL изменился
    expect(page.url()).toContain(href);
  });
});
