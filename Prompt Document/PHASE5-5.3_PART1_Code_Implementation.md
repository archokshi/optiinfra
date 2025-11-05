# PHASE5-5.3 PART1: Portal Tests - Code Implementation Plan

**Phase**: PHASE5-5.3  
**Component**: Portal & Production  
**Objective**: Create Playwright E2E tests for the portal  
**Estimated Time**: 30+25m = 55 minutes total  
**Priority**: HIGH  
**Dependencies**: PHASE5-5.2 (Dashboard Components)

---

## Overview

This phase creates comprehensive end-to-end tests using Playwright to validate all portal functionality, including navigation, dashboard components, charts, and user interactions.

---

## Portal Tests Purpose

### **Primary Goals**
1. **E2E Testing** - Test complete user workflows
2. **Component Testing** - Validate individual components
3. **Visual Testing** - Ensure UI renders correctly
4. **Interaction Testing** - Test user interactions
5. **API Integration** - Test API calls and responses

### **Test Coverage**
- Landing page navigation
- Dashboard layout and components
- Agent status cards
- Charts rendering
- Recommendations approve/reject
- Sidebar navigation
- Responsive design

---

## Implementation Plan

### Step 1: Install Playwright (5 minutes)

```bash
cd portal
npm install -D @playwright/test
npx playwright install
```

**What this installs:**
- Playwright test runner
- Browser binaries (Chromium, Firefox, WebKit)
- Test utilities

---

### Step 2: Configure Playwright (playwright.config.ts) (5 minutes)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

### Step 3: Create Test Structure (3 minutes)

```bash
mkdir -p tests/e2e
mkdir -p tests/fixtures
```

**Directory Structure:**
```
tests/
├── e2e/
│   ├── landing.spec.ts
│   ├── dashboard.spec.ts
│   ├── navigation.spec.ts
│   ├── agents.spec.ts
│   └── recommendations.spec.ts
└── fixtures/
    └── mock-data.ts
```

---

### Step 4: Create Mock Data Fixtures (tests/fixtures/mock-data.ts) (5 minutes)

```typescript
import type { Agent, Recommendation } from '@/lib/types';

export const mockAgents: Agent[] = [
  {
    agent_id: 'cost-001',
    agent_name: 'Cost Agent',
    agent_type: 'cost',
    version: '1.0.0',
    status: 'active',
    last_heartbeat: new Date().toISOString(),
    capabilities: ['cost_tracking'],
    host: 'localhost',
    port: 8001,
  },
  {
    agent_id: 'perf-001',
    agent_name: 'Performance Agent',
    agent_type: 'performance',
    version: '1.0.0',
    status: 'active',
    last_heartbeat: new Date().toISOString(),
    capabilities: ['performance_monitoring'],
    host: 'localhost',
    port: 8002,
  },
];

export const mockRecommendations: Recommendation[] = [
  {
    id: 'rec-001',
    agent_type: 'cost',
    type: 'spot_migration',
    title: 'Migrate to Spot Instances',
    description: 'Test recommendation',
    estimated_savings: 450,
    risk_level: 'low',
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];
```

---

### Step 5: Create Landing Page Tests (tests/e2e/landing.spec.ts) (5 minutes)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test('should display OptiInfra branding', async ({ page }) => {
    await page.goto('/');
    
    // Check title
    await expect(page.locator('h1')).toContainText('OptiInfra');
    
    // Check description
    await expect(page.locator('p')).toContainText('AI-Powered LLM Infrastructure Optimization');
  });

  test('should have navigation buttons', async ({ page }) => {
    await page.goto('/');
    
    // Check dashboard button
    const dashboardButton = page.getByRole('link', { name: 'Go to Dashboard' });
    await expect(dashboardButton).toBeVisible();
    
    // Check API health button
    const healthButton = page.getByRole('link', { name: 'API Health' });
    await expect(healthButton).toBeVisible();
  });

  test('should display key metrics', async ({ page }) => {
    await page.goto('/');
    
    // Check for 50%, 3x, 4 metrics
    await expect(page.locator('text=50%')).toBeVisible();
    await expect(page.locator('text=3x')).toBeVisible();
    await expect(page.locator('text=4')).toBeVisible();
    
    // Check labels
    await expect(page.locator('text=Cost Reduction')).toBeVisible();
    await expect(page.locator('text=Performance Boost')).toBeVisible();
    await expect(page.locator('text=AI Agents')).toBeVisible();
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('link', { name: 'Go to Dashboard' }).click();
    
    // Should be on dashboard page
    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

### Step 6: Create Dashboard Tests (tests/e2e/dashboard.spec.ts) (7 minutes)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display dashboard layout', async ({ page }) => {
    // Check sidebar
    await expect(page.locator('text=OptiInfra')).toBeVisible();
    
    // Check header
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Monitor your LLM infrastructure')).toBeVisible();
    
    // Check main content
    await expect(page.locator('h1:has-text("Overview")')).toBeVisible();
  });

  test('should display all agent cards', async ({ page }) => {
    // Check for 4 agent cards
    await expect(page.locator('text=Cost Agent')).toBeVisible();
    await expect(page.locator('text=Performance Agent')).toBeVisible();
    await expect(page.locator('text=Resource Agent')).toBeVisible();
    await expect(page.locator('text=Application Agent')).toBeVisible();
  });

  test('should display agent metrics', async ({ page }) => {
    // Check Cost Agent metric
    await expect(page.locator('text=$12,450')).toBeVisible();
    await expect(page.locator('text=Monthly Cost')).toBeVisible();
    
    // Check Performance Agent metric
    await expect(page.locator('text=85ms')).toBeVisible();
    await expect(page.locator('text=P95 Latency')).toBeVisible();
    
    // Check Resource Agent metric
    await expect(page.locator('text=78%')).toBeVisible();
    await expect(page.locator('text=GPU Utilization')).toBeVisible();
    
    // Check Application Agent metric
    await expect(page.locator('text=94%')).toBeVisible();
    await expect(page.locator('text=Quality Score')).toBeVisible();
  });

  test('should display status badges', async ({ page }) => {
    // All agents should show "active" status
    const badges = page.locator('text=active');
    await expect(badges).toHaveCount(4);
  });

  test('should display charts', async ({ page }) => {
    // Check chart titles
    await expect(page.locator('text=Cost Trends')).toBeVisible();
    await expect(page.locator('text=Performance Metrics')).toBeVisible();
    
    // Charts should be rendered (check for SVG elements)
    const charts = page.locator('svg.recharts-surface');
    await expect(charts).toHaveCount(2);
  });

  test('should display recommendations', async ({ page }) => {
    // Check recommendations section
    await expect(page.locator('h2:has-text("Pending Recommendations")')).toBeVisible();
    
    // Check recommendation cards
    await expect(page.locator('text=Migrate to Spot Instances')).toBeVisible();
    await expect(page.locator('text=Optimize KV Cache')).toBeVisible();
  });

  test('should show recommendation details', async ({ page }) => {
    // Check first recommendation
    await expect(page.locator('text=$450.00')).toBeVisible();
    await expect(page.locator('text=Estimated Savings')).toBeVisible();
    await expect(page.locator('text=Low Risk')).toBeVisible();
    
    // Check second recommendation
    await expect(page.locator('text=15.0%')).toBeVisible();
    await expect(page.locator('text=Estimated Improvement')).toBeVisible();
    await expect(page.locator('text=Medium Risk')).toBeVisible();
  });
});
```

---

### Step 7: Create Navigation Tests (tests/e2e/navigation.spec.ts) (5 minutes)

```typescript
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
    // Overview should be active
    const overviewLink = page.getByRole('link', { name: 'Overview' });
    await expect(overviewLink).toHaveClass(/bg-primary-50/);
  });

  test('should navigate to different pages', async ({ page }) => {
    // Click Cost Agent
    await page.getByRole('link', { name: 'Cost Agent' }).click();
    await expect(page).toHaveURL('/dashboard/cost');
    
    // Click Performance Agent
    await page.getByRole('link', { name: 'Performance Agent' }).click();
    await expect(page).toHaveURL('/dashboard/performance');
    
    // Click back to Overview
    await page.getByRole('link', { name: 'Overview' }).click();
    await expect(page).toHaveURL('/dashboard');
  });

  test('should display version in sidebar', async ({ page }) => {
    await expect(page.locator('text=Version 1.0.0')).toBeVisible();
  });
});
```

---

### Step 8: Create Agent Tests (tests/e2e/agents.spec.ts) (5 minutes)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Agent Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display trend indicators', async ({ page }) => {
    // Check for trend values
    await expect(page.locator('text=-8.2%')).toBeVisible();
    await expect(page.locator('text=-12%')).toBeVisible();
    await expect(page.locator('text=+5%')).toBeVisible();
    await expect(page.locator('text=+2%')).toBeVisible();
  });

  test('should show last heartbeat time', async ({ page }) => {
    // All cards should show "Last heartbeat"
    const heartbeats = page.locator('text=Last heartbeat:');
    await expect(heartbeats).toHaveCount(4);
  });

  test('should display agent icons', async ({ page }) => {
    // Check for emoji icons
    await expect(page.locator('text=💰')).toBeVisible(); // Cost
    await expect(page.locator('text=⚡')).toBeVisible(); // Performance
    await expect(page.locator('text=🖥️')).toBeVisible(); // Resource
    await expect(page.locator('text=✅')).toBeVisible(); // Application
  });
});
```

---

### Step 9: Create Recommendation Tests (tests/e2e/recommendations.spec.ts) (5 minutes)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Recommendations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display approve and reject buttons', async ({ page }) => {
    // Each pending recommendation should have 2 buttons
    const approveButtons = page.getByRole('button', { name: 'Approve' });
    const rejectButtons = page.getByRole('button', { name: 'Reject' });
    
    await expect(approveButtons).toHaveCount(2);
    await expect(rejectButtons).toHaveCount(2);
  });

  test('should handle approve button click', async ({ page }) => {
    // Set up console listener
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });
    
    // Click first approve button
    await page.getByRole('button', { name: 'Approve' }).first().click();
    
    // Should log to console
    await page.waitForTimeout(100);
    expect(consoleLogs.some(log => log.includes('Approve recommendation'))).toBeTruthy();
  });

  test('should handle reject button click', async ({ page }) => {
    // Set up console listener
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });
    
    // Click first reject button
    await page.getByRole('button', { name: 'Reject' }).first().click();
    
    // Should log to console
    await page.waitForTimeout(100);
    expect(consoleLogs.some(log => log.includes('Reject recommendation'))).toBeTruthy();
  });

  test('should display risk indicators', async ({ page }) => {
    // Check for risk icons and labels
    await expect(page.locator('text=Low Risk')).toBeVisible();
    await expect(page.locator('text=Medium Risk')).toBeVisible();
  });
});
```

---

### Step 10: Create Responsive Design Tests (tests/e2e/responsive.spec.ts) (5 minutes)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('should work on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/dashboard');
    
    // All 4 agent cards should be in one row
    const cards = page.locator('[class*="grid"]').first();
    await expect(cards).toBeVisible();
  });

  test('should work on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/dashboard');
    
    // Sidebar should still be visible
    await expect(page.locator('text=OptiInfra')).toBeVisible();
    
    // Content should be responsive
    await expect(page.locator('h1:has-text("Overview")')).toBeVisible();
  });

  test('should work on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Content should be stacked
    await expect(page.locator('h1:has-text("Overview")')).toBeVisible();
  });
});
```

---

### Step 11: Create API Health Test (tests/e2e/api.spec.ts) (3 minutes)

```typescript
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
```

---

### Step 12: Update package.json Scripts (2 minutes)

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "playwright test",
    "test:ui": "playwright test --ui",
    "test:headed": "playwright test --headed",
    "test:report": "playwright show-report"
  }
}
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **Playwright Configured**
   - Test runner set up
   - Multiple browsers configured
   - Dev server integration

2. ✅ **E2E Tests Created**
   - Landing page tests
   - Dashboard tests
   - Navigation tests
   - Agent card tests
   - Recommendation tests
   - Responsive design tests
   - API tests

3. ✅ **Test Coverage**
   - All major user flows
   - Component rendering
   - User interactions
   - API endpoints

4. ✅ **CI/CD Ready**
   - Configured for CI environments
   - Retry logic
   - Screenshot on failure

---

## Success Criteria

- [ ] Playwright installed and configured
- [ ] All test files created
- [ ] Tests passing locally
- [ ] Multiple browsers tested
- [ ] Responsive design tested
- [ ] API endpoints tested
- [ ] Test reports generated

---

## Next Steps

After PHASE5-5.3 is complete:

**PHASE5-5.4: Authentication**
- OAuth2/JWT implementation
- RBAC (Role-Based Access Control)
- Protected routes

---

**Portal tests ready for comprehensive E2E validation!** ✅
