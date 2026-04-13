const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // 登录
  console.log('Opening login page...');
  await page.goto('http://60.205.220.62');
  await page.waitForTimeout(1000);
  
  console.log('Filling login form...');
  await page.fill('input[type="text"]', '13800000000');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
  
  // 访问管理员后台
  console.log('Going to admin page...');
  await page.goto('http://60.205.220.62/admin');
  await page.waitForTimeout(3000);
  
  // 获取页面HTML
  const html = await page.content();
  console.log('Page title:', await page.title());
  
  // 截图
  await page.screenshot({ path: 'admin_page.png', fullPage: true });
  console.log('Screenshot saved to admin_page.png');
  
  await browser.close();
  console.log('Done');
})();
