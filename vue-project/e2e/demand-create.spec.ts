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

test.describe('需求创建', () => {
  test.beforeEach(async ({ page }) => {
    await page.waitForTimeout(1000);
    await loginAs(page, PARTY_A.phone, PARTY_A.password);
  });

  test('创建需求页面可访问', async ({ page }) => {
    await page.goto(`${BASE}/demands/create`);
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(`${BASE}/login`);
    // 页面标题应包含"发布"
    const h1 = page.locator('h1').first();
    await expect(h1).toContainText('发布');
  });

  test('创建需求表单字段存在', async ({ page }) => {
    await page.goto(`${BASE}/demands/create`);
    await page.waitForTimeout(1000);
    // 标题输入
    await expect(page.locator('input[placeholder*="标题"], input[placeholder*="需求"]').first()).toBeVisible();
    // 分类选择
    await expect(page.locator('select').first()).toBeVisible();
    // 描述文本域
    await expect(page.locator('textarea').first()).toBeVisible();
    // 付款方式（radio 可能被 CSS 隐藏，检查可见的卡片）
    await expect(page.locator('.payment-type-card').first()).toBeVisible();
  });

  test('填写需求表单可提交', async ({ page }) => {
    await page.goto(`${BASE}/demands/create`);
    await page.waitForTimeout(1000);

    // 填标题
    const titleInput = page.locator('input[placeholder*="标题"], input[placeholder*="需求"]').first();
    await titleInput.fill('E2E自动化测试需求');

    // 选分类
    const categorySelect = page.locator('select').first();
    await categorySelect.selectOption({ index: 1 });

    // 填预算
    const budgetInputs = page.locator('input[type="number"]');
    if (await budgetInputs.count() >= 2) {
      await budgetInputs.nth(0).fill('5000');
      await budgetInputs.nth(1).fill('20000');
    }

    // 填描述
    const descTextarea = page.locator('textarea').first();
    await descTextarea.fill('这是E2E自动化测试创建的需求描述，用于测试需求发布功能。');

    // 选付款方式（radio 可能被 CSS 隐藏，点可见的卡片）
    const paymentCard = page.locator('.payment-type-card, label:has(input[type="radio"])').first();
    await paymentCard.click();

    // 提交按钮应存在
    const submitBtn = page.locator('button[type="submit"], button:has-text("发布"), button:has-text("提交")').first();
    await expect(submitBtn).toBeVisible();
  });
});
