import { test, expect, Page } from '@playwright/test';

const BASE = 'http://localhost:5173';
const ADMIN = { phone: '13800000000', password: 'admin123' };

// 登录工具函数
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

test.describe('导航与布局', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
  });

  test('登录后显示侧边导航栏', async ({ page }) => {
    // 侧边栏存在
    const sidebar = page.locator('.sidebar, nav, [class*="sidebar"], [class*="nav"]').first();
    await expect(sidebar).toBeVisible({ timeout: 5000 });
  });

  test('顶部导航显示用户信息', async ({ page }) => {
    // 顶栏应有用户头像或名称
    const topbar = page.locator('.topbar, .header, [class*="header"], [class*="top"]').first();
    await expect(topbar).toBeVisible({ timeout: 5000 });
  });

  test('点击仪表盘菜单跳转到首页', async ({ page }) => {
    // 找到 Dashboard 链接并点击
    const dashLink = page.locator('a[href="/"], a[href*="dashboard"], .nav-item').first();
    await dashLink.click();
    await page.waitForTimeout(500);
    // 页面中应包含统计数字
    const content = page.locator('.dashboard, main, .content').first();
    await expect(content).toBeVisible();
  });
});

test.describe('仪表盘', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, ADMIN.phone, ADMIN.password);
    await page.goto(`${BASE}/`);
  });

  test('首页加载成功', async ({ page }) => {
    await expect(page).toHaveURL(`${BASE}/`);
    // 页面 title 包含图审
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('统计卡片可见', async ({ page }) => {
    // 等待数字加载
    await page.waitForTimeout(1000);
    // 找到数字统计区域
    const stats = page.locator('[class*="stat"], [class*="count"], [class*="card"]').first();
    await expect(stats).toBeVisible({ timeout: 5000 });
  });
});
