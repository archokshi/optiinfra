import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should have all navigation items', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Overview' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Cost Agent' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Performance Agent' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Resource Agent' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Application Agent' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

  test('should highlight active navigation item', async ({ page }) => {
    const overviewLink = page.getByRole('link', { name: 'Overview' });
    await expect(overviewLink).toHaveClass(/bg-primary-50/);
  });

  test('should navigate to different pages', async ({ page }) => {
    await page.getByRole('link', { name: 'Cost Agent' }).click();
    await expect(page).toHaveURL('/dashboard/cost');
    
    await page.getByRole('link', { name: 'Performance Agent' }).click();
    await expect(page).toHaveURL('/dashboard/performance');
    
    await page.getByRole('link', { name: 'Overview' }).click();
    await expect(page).toHaveURL('/dashboard');
  });

  test('should display version in sidebar', async ({ page }) => {
    await expect(page.locator('text=Version 1.0.0')).toBeVisible();
  });
});
