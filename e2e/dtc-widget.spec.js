/**
 * E2E-тесты: DTC-виджет поиска кодов неисправностей
 *
 * DOM-структура:
 *   .dtc-widget.collapsed        (корневой контейнер, initial collapsed)
 *     .dtc-header[role=button]   (заголовок, клик → toggle)
 *       .dtc-toggle-icon          (▶/▼)
 *     .dtc-body                   (скрыт через display:none при .collapsed)
 *       input#dtc-query           (поле поиска)
 *       .dtc-results              (результаты поиска)
 */
import { test, expect } from '@playwright/test';

test.describe('DTC-виджет поиска', () => {
  test('виджет присутствует на странице', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // DTC-виджет инжектируется JS, даём время на инициализацию
    const widget = page.locator('.dtc-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });
  });

  test('содержимое виджета сворачивается и разворачивается по клику на заголовок', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Ждём появления виджета
    const widget = page.locator('.dtc-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });

    // Проверяем начальное состояние — свёрнут
    await expect(widget).toHaveClass(/collapsed/);

    // Кликаем по заголовку для разворачивания
    const header = widget.locator('.dtc-header');
    await header.click();
    await page.waitForTimeout(300);

    // Проверяем, что collapsed удалён
    await expect(widget).not.toHaveClass(/collapsed/);

    // Повторный клик — сворачиваем обратно
    await header.click();
    await page.waitForTimeout(300);
    await expect(widget).toHaveClass(/collapsed/);
  });

  test('поле поиска становится доступным после разворачивания', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const widget = page.locator('.dtc-widget').first();
    await expect(widget).toBeVisible({ timeout: 10000 });

    // Разворачиваем виджет
    const header = widget.locator('.dtc-header');
    await header.click();
    await page.waitForTimeout(300);

    // Поле поиска должно быть видимо
    const searchInput = widget.locator('input#dtc-query');
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    // Вводим тестовый DTC-код
    await searchInput.fill('P0101');
    await page.waitForTimeout(500);

    // DTC-поиск может вернуть пустой результат для тестового кода,
    // но сам факт ввода проверяем
    const inputValue = await searchInput.inputValue();
    expect(inputValue).toBe('P0101');
  });
});
