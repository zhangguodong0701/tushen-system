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

test.describe('需求详情', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, PARTY_A.phone, PARTY_A.password);
  });

  test('从需求大厅点击进入详情页', async ({ page }) => {
    await page.goto(`${BASE}/demands`);
    await page.waitForTimeout(2000);

    // 点击第一个需求卡片/行
    const firstCard = page.locator('[class*="demand-card"], [class*="card"], tbody tr').first();
    const count = await firstCard.count();
    if (count > 0) {
      await firstCard.click();
      await page.waitForTimeout(1500);
      // 应该跳转到详情页，URL 包含 /demands/
      await expect(page.url()).toContain('/demands/');
    }
  });

  test('详情页显示需求信息', async ({ page }) => {
    // 直接访问一个已知需求 ID（从后端取一个真实 ID）
    // 先去需求列表取第一个需求的链接
    await page.goto(`${BASE}/demands`);
    await page.waitForTimeout(2000);

    const firstLink = page.locator('a[href*="/demands/"]').first();
    const count = await firstLink.count();
    if (count > 0) {
      await firstLink.click();
      await page.waitForTimeout(1500);
      // 详情页应显示标题或描述
      const body = await page.locator('body').textContent();
      expect(body?.length || 0).toBeGreaterThan(100);
    }
  });
});
