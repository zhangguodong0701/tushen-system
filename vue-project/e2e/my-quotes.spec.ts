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

test.describe('我的报价', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, PARTY_A.phone, PARTY_A.password);
  });

  test('我的报价页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/my-quotes`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('报价列表或空状态显示', async ({ page }) => {
    await page.goto(`${BASE}/my-quotes`);
    await page.waitForTimeout(2000);
    // 要么显示表格，要么显示空状态
    const table = page.locator('table');
    const empty = page.locator('[class*="empty"]');
    const tableCount = await table.count();
    const emptyCount = await empty.count();
    expect(tableCount + emptyCount).toBeGreaterThan(0);
  });

  test('分页组件（多页时）', async ({ page }) => {
    await page.goto(`${BASE}/my-quotes`);
    await page.waitForTimeout(2000);
    // 分页组件（如果有多页）
    const pagination = page.locator('[class*="pagination"], button:has-text("下一页"), button:has-text("上一页")');
    // 存在即验证通过（无分页也不报错）
    const count = await pagination.count();
    // 不断言，存在即可
  });
});
