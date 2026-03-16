#!/usr/bin/env node3
/**
 * NE301 端到端浏览器测试
 * 在浏览器中打开网页，用户可以看到实际界面
 */

const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false,  // 显示浏览器窗口
    slowMo: 100  // 慢动作，方便观察
  });

  const page = await browser.newPage();

  console.log('🌐 正在打开浏览器...');
  console.log('📍 访问: http://localhost:8000');

  // 访问主页
  await page.goto('http://localhost:8000');
  await page.waitForTimeout(3000);

  console.log('✅ 页面已加载');
  console.log('📄 标题:', await page.title());

  // 截图
  await page.screenshot({ path: 'tests/e2e/screenshots/homepage.png', fullPage: true });
  console.log('📸 截图已保存: tests/e2e/screenshots/homepage.png');

  // 保持浏览器打开10分钟，让用户查看
  console.log('\n👀 浏览器将保持打开10分钟，您可以查看界面...');
  console.log('💡 关闭浏览器请按 Ctrl+C\n');

  await new Promise(resolve => {
    setTimeout(resolve, 600000); // 10分钟
  });

  await browser.close();
  console.log('✅ 浏览器已关闭');
})();
