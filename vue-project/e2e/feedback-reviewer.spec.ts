import { test, expect, Page } from '@playwright/test';

const BASE = 'http://localhost:5173';
const PARTY_A = { phone: '13800000000', password: 'admin123' };
const REVIEWER = { phone: '13900000000', password: 'reviewer123' };

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

test.describe('意见反馈', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, PARTY_A.phone, PARTY_A.password);
  });

  test('反馈页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/feedback`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('反馈表单元素存在', async ({ page }) => {
    await page.goto(`${BASE}/feedback`);
    await page.waitForTimeout(1000);
    // 应有文本域和提交按钮
    const textarea = page.locator('textarea').first();
    const btn = page.locator('button').first();
    await expect(textarea).toBeVisible({ timeout: 5000 });
    await expect(btn).toBeVisible({ timeout: 5000 });
  });
});

test.describe('审核员页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    // 用审核员账号登录
    await loginAs(page, REVIEWER.phone, REVIEWER.password);
  });

  test('审核员页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/reviewer`);
    await page.waitForTimeout(1500);
    await expect(page).not.toHaveURL(`${BASE}/login`);
  });

  test('审核员页面有内容', async ({ page }) => {
    await page.goto(`${BASE}/reviewer`);
    await page.waitForTimeout(2000);
    const body = await page.locator('body').textContent();
    expect((body || '').length).toBeGreaterThan(50);
  });
});
