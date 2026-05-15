import { test, expect, Page } from '@playwright/test';

const BASE = 'http://localhost:5173';
const ADMIN = { phone: '13800000000', password: 'admin123' };

async function loginAs(page: Page, phone: string, password: string) {
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('#login-account', { state: 'visible', timeout: 10000 });
  // 先清空再输入，确保触发 Vue 的 v-model
  await page.fill('#login-account', '');
  await page.type('#login-account', phone);
  await page.fill('#login-password', '');
  await page.type('#login-password', password);
  await page.waitForTimeout(500);
  // 使用键盘回车提交表单
  await page.keyboard.press('Enter');
  // 等待跳转到首页
  await page.waitForURL(`${BASE}/`, { timeout: 15000 });
  await page.waitForTimeout(500);
}

test.describe('需求大厅', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('需求列表页面正常加载', async ({ page }) => {
    await page.goto(`${BASE}/demands`);
    await page.waitForTimeout(1500);
    // 应该有需求列表容器
    const container = page.locator('[class*="demand"], [class*="list"], main').first();
    await expect(container).toBeVisible({ timeout: 5000 });
  });

  test('需求列表有数据', async ({ page }) => {
    await page.goto(`${BASE}/demands`);
    await page.waitForTimeout(2000);
    // 至少有一个需求卡片
    const cards = page.locator('[class*="demand-card"], [class*="card"], .demand-item');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('搜索功能存在', async ({ page }) => {
    await page.goto(`${BASE}/demands`);
    await page.waitForTimeout(1000);
    // 搜索框应存在
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="关键"], input[type="search"]').first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });
});

test.describe('我的需求', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('我的需求页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/my-demands`);
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });
});

test.describe('订单管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('订单列表页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/orders`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
    const container = page.locator('main, [class*="order"], [class*="list"]').first();
    await expect(container).toBeVisible({ timeout: 5000 });
  });
});

test.describe('通知页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('通知页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/notifications`);
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });
});
