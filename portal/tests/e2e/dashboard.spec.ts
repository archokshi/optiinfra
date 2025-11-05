import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display dashboard layout', async ({ page }) => {
    await expect(page.locator('text=OptiInfra')).toBeVisible();
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Monitor your LLM infrastructure')).toBeVisible();
    await expect(page.locator('h1:has-text("Overview")')).toBeVisible();
  });

  test('should display all agent cards', async ({ page }) => {
    await expect(page.locator('text=Cost Agent')).toBeVisible();
    await expect(page.locator('text=Performance Agent')).toBeVisible();
    await expect(page.locator('text=Resource Agent')).toBeVisible();
    await expect(page.locator('text=Application Agent')).toBeVisible();
  });

  test('should display agent metrics', async ({ page }) => {
    await expect(page.locator('text=$12,450')).toBeVisible();
    await expect(page.locator('text=Monthly Cost')).toBeVisible();
    
    await expect(page.locator('text=85ms')).toBeVisible();
    await expect(page.locator('text=P95 Latency')).toBeVisible();
    
    await expect(page.locator('text=78%')).toBeVisible();
    await expect(page.locator('text=GPU Utilization')).toBeVisible();
    
    await expect(page.locator('text=94%')).toBeVisible();
    await expect(page.locator('text=Quality Score')).toBeVisible();
  });

  test('should display status badges', async ({ page }) => {
    const badges = page.locator('text=active');
    await expect(badges).toHaveCount(4);
  });

  test('should display charts', async ({ page }) => {
    await expect(page.locator('text=Cost Trends')).toBeVisible();
    await expect(page.locator('text=Performance Metrics')).toBeVisible();
    
    const charts = page.locator('svg.recharts-surface');
    await expect(charts).toHaveCount(2);
  });

  test('should display recommendations', async ({ page }) => {
    await expect(page.locator('h2:has-text("Pending Recommendations")')).toBeVisible();
    await expect(page.locator('text=Migrate to Spot Instances')).toBeVisible();
    await expect(page.locator('text=Optimize KV Cache')).toBeVisible();
  });

  test('should show recommendation details', async ({ page }) => {
    await expect(page.locator('text=$450.00')).toBeVisible();
    await expect(page.locator('text=Estimated Savings')).toBeVisible();
    await expect(page.locator('text=Low Risk')).toBeVisible();
    
    await expect(page.locator('text=15.0%')).toBeVisible();
    await expect(page.locator('text=Estimated Improvement')).toBeVisible();
    await expect(page.locator('text=Medium Risk')).toBeVisible();
  });
});
