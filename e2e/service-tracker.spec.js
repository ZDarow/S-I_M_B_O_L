/**
 * E2E-тесты: Service Tracker — планировщик технического обслуживания
 *
 * DOM-структура:
 *   .service-widget.collapsed        (корневой контейнер, initial collapsed)
 *     .sw-header[role=button]        (заголовок, клик => toggle)
 *       .sw-toggle-icon               (▶/▼)
 *     .sw-body                        (скрыт через display:none при .collapsed)
 *       input#sw-mileage              (поле ввода пробега)
 */
import { test, expect } from '@playwright/test';

test.describe('Service Tracker (планировщик ТО)', () => {
  test('виджет присутствует на странице', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const widget = page.locator('.service-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });
  });

  test('виджет сворачивается и разворачивается по клику на заголовок', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const widget = page.locator('.service-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });

    // Свёрнут по умолчанию
    await expect(widget).toHaveClass(/collapsed/);

    // Разворачиваем
    const header = widget.locator('.sw-header');
    await header.click();
    await expect(widget).not.toHaveClass(/collapsed/);

    // Сворачиваем обратно
    await header.click();
    await expect(widget).toHaveClass(/collapsed/);
  });

  test('форма планировщика принимает ввод пробега после разворачивания', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const widget = page.locator('.service-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });

    // Разворачиваем виджет
    const header = widget.locator('.sw-header');
    await header.click();
    await expect(widget).not.toHaveClass(/collapsed/);

    const mileageInput = widget.locator('input#sw-mileage');
    await expect(mileageInput).toBeVisible({ timeout: 5000 });
    await mileageInput.fill('50000');
    await expect(mileageInput).toHaveValue('50000');
  });
});
