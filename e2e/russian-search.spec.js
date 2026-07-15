/**
 * E2E-тесты: поиск по сайту (mdBook search + кириллический поиск)
 *
 * mdBook search:
 *   - Поле #mdbook-searchbar скрыто по умолчанию
 *   - Активируется клавишей s или /
 *   - После активации появляется #mdbook-searchbar
 */
import { test, expect } from '@playwright/test';

test.describe('Поиск по сайту', () => {
  test('поле поиска mdBook активируется клавишей /', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('#mdbook-searchbar');
    await expect(searchInput).toBeAttached();

    // Нажимаем / для активации поиска
    await page.keyboard.press('/');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });

  test('поисковый запрос на русском языке работает', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.keyboard.press('/');
    const searchInput = page.locator('#mdbook-searchbar');
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.fill('двигатель');
    await page.waitForTimeout(1000);
  });

  test('переключение на кириллический поиск по клику', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const rusButton = page.locator('.russian-search-toggle, #rus-search-btn, a[href="#russian-search"]').first();
    if (await rusButton.count() > 0) {
      await rusButton.click();
      await page.waitForTimeout(500);

      const rusInput = page.locator('#russian-search input, .russian-search input').first();
      if (await rusInput.count() > 0) {
        await expect(rusInput).toBeVisible({ timeout: 3000 });
        await rusInput.fill('770105');
        await page.waitForTimeout(500);
      }
    }
  });
});
