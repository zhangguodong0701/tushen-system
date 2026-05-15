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

test.describe('后台管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('管理后台页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('管理后台有用户列表', async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await page.waitForTimeout(2000);
    // 找到用户表格
    const table = page.locator('table, [class*="table"], [class*="user-list"]').first();
    await expect(table).toBeVisible({ timeout: 5000 });
  });
});

test.describe('个人信息', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('个人信息页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/profile`);
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('显示用户手机号', async ({ page }) => {
    await page.goto(`${BASE}/profile`);
    await page.waitForTimeout(1500);
    // 页面应该有手机号信息
    const body = await page.locator('body').textContent();
    expect(body).toContain('138');
  });
});

test.describe('纠纷管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('纠纷列表页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/disputes`);
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });
});

test.describe('退出登录', () => {
  test('退出后跳转登录页', async ({ page }) => {
    await loginAs(page, ADMIN.phone, ADMIN.password);
    // 清空 token 模拟退出
    await page.evaluate(() => {
      localStorage.removeItem('tushen_token');
      localStorage.removeItem('tushen_user');
    });
    await page.goto(`${BASE}/`);
    await page.waitForURL(`${BASE}/login`, { timeout: 5000 });
    await expect(page).toHaveURL(`${BASE}/login`);
  });
});
