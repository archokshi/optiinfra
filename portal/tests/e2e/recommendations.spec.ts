import { test, expect } from '@playwright/test';

test.describe('Recommendations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display approve and reject buttons', async ({ page }) => {
    const approveButtons = page.getByRole('button', { name: 'Approve' });
    const rejectButtons = page.getByRole('button', { name: 'Reject' });
    
    await expect(approveButtons).toHaveCount(2);
    await expect(rejectButtons).toHaveCount(2);
  });

  test('should handle approve button click', async ({ page }) => {
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });
    
    await page.getByRole('button', { name: 'Approve' }).first().click();
    
    await page.waitForTimeout(100);
    expect(consoleLogs.some(log => log.includes('Approve recommendation'))).toBeTruthy();
  });

  test('should handle reject button click', async ({ page }) => {
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });
    
    await page.getByRole('button', { name: 'Reject' }).first().click();
    
    await page.waitForTimeout(100);
    expect(consoleLogs.some(log => log.includes('Reject recommendation'))).toBeTruthy();
  });

  test('should display risk indicators', async ({ page }) => {
    await expect(page.locator('text=Low Risk')).toBeVisible();
    await expect(page.locator('text=Medium Risk')).toBeVisible();
  });
});
