import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test('should display OptiInfra branding', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('h1')).toContainText('OptiInfra');
    await expect(page.locator('p')).toContainText('AI-Powered LLM Infrastructure Optimization');
  });

  test('should have navigation buttons', async ({ page }) => {
    await page.goto('/');
    
    const dashboardButton = page.getByRole('link', { name: 'Go to Dashboard' });
    await expect(dashboardButton).toBeVisible();
    
    const healthButton = page.getByRole('link', { name: 'API Health' });
    await expect(healthButton).toBeVisible();
  });

  test('should display key metrics', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('text=50%')).toBeVisible();
    await expect(page.locator('text=3x')).toBeVisible();
    await expect(page.locator('text=4')).toBeVisible();
    
    await expect(page.locator('text=Cost Reduction')).toBeVisible();
    await expect(page.locator('text=Performance Boost')).toBeVisible();
    await expect(page.locator('text=AI Agents')).toBeVisible();
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('link', { name: 'Go to Dashboard' }).click();
    
    await expect(page).toHaveURL('/dashboard');
  });
});
