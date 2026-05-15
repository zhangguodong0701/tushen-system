import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';

// 管理员账号（已存在于数据库）
const ADMIN = { phone: '13800000000', password: 'admin123' };
// 乙方账号
const SELLER = { phone: '13900000000', password: 'reviewer123' };

test.describe('认证模块 - 登录', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await expect(page.locator('.login-card')).toBeVisible();
  });

  test('页面正常渲染', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('图审云平台');
    await expect(page.locator('.tab-btn').first()).toContainText('登录');
    await expect(page.locator('#login-account')).toBeVisible();
    await expect(page.locator('#login-password')).toBeVisible();
  });

  test('管理员登录成功并跳转首页', async ({ page }) => {
    // 等待页面完全加载
    await page.waitForSelector('#login-account', { state: 'visible', timeout: 10000 });
    await page.type('#login-account', ADMIN.phone);
    await page.type('#login-password', ADMIN.password);
    await page.waitForTimeout(500);
    // 使用键盘回车提交表单
    await page.keyboard.press('Enter');

    // 等待跳转到首页
    await page.waitForURL(`${BASE}/`, { timeout: 15000 });
    await expect(page).toHaveURL(`${BASE}/`);
  });

  test('错误密码登录失败', async ({ page }) => {
    await page.fill('#login-account', ADMIN.phone);
    await page.fill('#login-password', 'wrongpassword');
    await page.click('button[type="submit"]');

    // 应该显示错误提示，不跳转
    await page.waitForTimeout(1500);
    await expect(page).toHaveURL(`${BASE}/login`);
  });

  test('空账号不能提交', async ({ page }) => {
    await page.click('button[type="submit"]');
    // 停留在登录页
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(`${BASE}/login`);
  });
});

test.describe('认证模块 - 注册', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.click('.tab-btn:nth-child(2)'); // 点"注册"tab
    await page.waitForTimeout(300);
  });

  test('注册表单正常渲染', async ({ page }) => {
    await expect(page.locator('.role-cards')).toBeVisible();
    await expect(page.locator('#reg-phone')).toBeVisible();
    await expect(page.locator('#reg-name')).toBeVisible();
  });

  test('选择甲方角色后显示类型选项', async ({ page }) => {
    await page.click('.role-card:first-child'); // 甲方
    await expect(page.locator('#reg-type')).toBeVisible();
  });

  test('手机号格式校验', async ({ page }) => {
    // 选择角色
    await page.click('.role-card:first-child');
    await page.selectOption('#reg-type', '业主');
    // 输入非法手机号
    await page.fill('#reg-phone', '12345');
    await page.fill('#reg-name', '测试用户');
    await page.locator('form input[type="password"]').first().fill('Abc12345');
    await page.locator('form input[type="password"]').last().fill('Abc12345');
    await page.click('button[type="submit"]');
    // 停在注册页
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(`${BASE}/login`);
  });
});

test.describe('认证模块 - 需要登录的页面跳转', () => {
  test('未登录访问首页重定向到登录', async ({ page }) => {
    // 清空 localStorage
    await page.goto(`${BASE}/login`);
    await page.evaluate(() => localStorage.clear());

    await page.goto(`${BASE}/`);
    // 应该跳转到登录页
    await page.waitForURL(`${BASE}/login`, { timeout: 5000 });
    await expect(page).toHaveURL(`${BASE}/login`);
  });
});
