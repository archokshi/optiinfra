import { test, expect } from '@playwright/test';

test.describe('API Health', () => {
  test('should return healthy status', async ({ page }) => {
    const response = await page.goto('/api/health');
    
    expect(response?.status()).toBe(200);
    
    const data = await response?.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service', 'optiinfra-portal');
    expect(data).toHaveProperty('version', '1.0.0');
  });
});
