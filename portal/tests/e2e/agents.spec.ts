import { test, expect } from '@playwright/test';

test.describe('Agent Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display trend indicators', async ({ page }) => {
    await expect(page.locator('text=-8.2%')).toBeVisible();
    await expect(page.locator('text=-12%')).toBeVisible();
    await expect(page.locator('text=+5%')).toBeVisible();
    await expect(page.locator('text=+2%')).toBeVisible();
  });

  test('should show last heartbeat time', async ({ page }) => {
    const heartbeats = page.locator('text=Last heartbeat:');
    await expect(heartbeats).toHaveCount(4);
  });

  test('should display agent icons', async ({ page }) => {
    await expect(page.locator('text=💰')).toBeVisible();
    await expect(page.locator('text=⚡')).toBeVisible();
    await expect(page.locator('text=🖥️')).toBeVisible();
    await expect(page.locator('text=✅')).toBeVisible();
  });
});
