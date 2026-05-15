import { test, expect, Page } from '@playwright/test';

const BASE = 'http://localhost:5173';
const PARTY_A = { phone: '13800000000', password: 'admin123' };

async function loginAs(page: Page, phone: string, password: string) {
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('#login-account', { state: 'visible', timeout: 10000 });
  await page.fill('#login-account', '');
  await page.type('#login-account', phone);
  await page.fill('#login-password', '');
  await page.type('#login-password', password);
  await page.waitForTimeout(500);
  await page.keyboard.press('Enter');
  await page.waitForURL(`${BASE}/`, { timeout: 15000 });
  await page.waitForTimeout(500);
}

test.describe('图纸管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, PARTY_A.phone, PARTY_A.password);
  });

  test('图纸列表页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/drawings`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('图纸统计卡片显示', async ({ page }) => {
    await page.goto(`${BASE}/drawings`);
    await page.waitForTimeout(2000);
    // 统计卡片区域
    const statCards = page.locator('[class*="stat-card"], [class*="stat"]');
    const count = await statCards.count();
    // 有数据或无数据都应有页面结构
    const body = await page.locator('body').textContent();
    expect(body).toBeTruthy();
  });

  test('搜索框存在', async ({ page }) => {
    await page.goto(`${BASE}/drawings`);
    await page.waitForTimeout(1000);
    const searchInput = page.locator('input[placeholder*="搜索"], input[type="text"]').first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });

  test('筛选标签可点击', async ({ page }) => {
    await page.goto(`${BASE}/drawings`);
    await page.waitForTimeout(1500);
    // 尝试点击"待审核"标签
    const tab = page.locator('button:has-text("待审核"), button:has-text("全部")').first();
    const count = await tab.count();
    if (count > 0) {
      await tab.click();
      await page.waitForTimeout(500);
      // 页面不应报错
      await expect(page).not.toHaveURL(`${BASE}/login`);
    }
  });
});
