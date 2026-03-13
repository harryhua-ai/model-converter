import { test, expect } from '@playwright/test';
import path from 'path';

// 设置全局超时时间
test.setTimeout(120000);  // 2 分钟

test.describe('NE301 模型转换器 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 设置基础 URL
    await page.goto('http://localhost:8000');

    // 监听所有控制台消息
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      console.log(`[浏览器控制台 ${type}]:`, text);

      if (msg.args().length > 0) {
        msg.args().forEach(arg => {
          arg.jsonValue().then(val => {
            console.log(`  参数详情:`, JSON.stringify(val, null, 2));
          }).catch(() => {
            console.log(`  参数详情: [无法序列化]`);
          });
        });
      }
    });

    // 监听所有网络请求和响应
    page.on('request', request => {
      console.log(`[网络请求] ${request.method()} ${request.url()}`);
    });

    page.on('response', async response => {
      const url = response.url();
      const status = response.status();
      const method = response.request().method();

      console.log(`[网络响应] ${method} ${url} - 状态码: ${status}`);

      // 特别关注 API 响应
      if (url.includes('/api/')) {
        try {
          const body = await response.text();
          console.log(`[响应体]`, body);
        } catch (e) {
          console.log(`[响应体] [无法读取响应体]`);
        }
      }

      // 记录失败的响应
      if (status >= 400) {
        console.error(`[错误响应] ${method} ${url} - ${status}`);
        try {
          const body = await response.text();
          console.error(`[错误响应体]`, body);
        } catch (e) {
          console.error(`[错误响应体] [无法读取]`);
        }
      }
    });

    // 监听页面错误
    page.on('pageerror', error => {
      console.error(`[页面错误]`, error.message);
      console.error(`[错误堆栈]`, error.stack);
    });

    // 监听请求失败
    page.on('requestfailed', request => {
      console.error(`[请求失败] ${request.url()}`);
      console.error(`[失败原因]`, request.failure());
    });
  });

  test('完整转换流程测试', async ({ page }) => {
    console.log('\n=== 开始测试：完整转换流程 ===\n');

    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
    console.log('✓ 页面加载完成');

    // 截图：初始状态
    await page.screenshot({ path: 'tests/e2e/screenshots/01-initial-state.png' });
    console.log('✓ 截图：初始状态');

    // 查找并上传模型文件
    console.log('\n--- 步骤 1: 上传模型文件 ---');
    const modelFileInput = await page.locator('input[type="file"]').first();
    await modelFileInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/best.pt');
    console.log('✓ 模型文件已选择');

    // 等待文件名显示
    await page.waitForTimeout(1500);
    await page.screenshot({ path: 'tests/e2e/screenshots/02-model-uploaded.png' });
    console.log('✓ 截图：模型文件已上传');

    // 上传 YAML 文件（通过 ID 直接定位）
    console.log('\n--- 步骤 2: 上传 YAML 文件 ---');
    try {
      // 直接通过 ID 定位隐藏的文件输入框（Playwright 可以操作隐藏输入）
      const yamlInput = page.locator('#yaml-file-input');
      const yamlExists = await yamlInput.count() > 0;

      if (yamlExists) {
        await yamlInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/household_trash.yaml');
        console.log('✓ YAML 文件已选择（通过 ID 定位）');
      } else {
        // 备用方案：通过 accept 属性定位
        const yamlInputByAccept = page.locator('input[type="file"][accept=".yaml"], input[type="file"][accept=".yml"]').first();
        await yamlInputByAccept.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/household_trash.yaml');
        console.log('✓ YAML 文件已选择（通过 accept 属性）');
      }
    } catch (e) {
      console.log('⚠ 上传 YAML 文件时出错:', e.message);
    }

    await page.waitForTimeout(1500);
    await page.screenshot({ path: 'tests/e2e/screenshots/03-yaml-uploaded.png' });
    console.log('✓ 截图：YAML 文件已上传');

    // 上传校准数据集（通过 ID 直接定位）
    console.log('\n--- 步骤 3: 上传校准数据集 ---');
    try {
      // 直接通过 ID 定位隐藏的文件输入框
      const calibInput = page.locator('#calibration-file-input');
      const calibExists = await calibInput.count() > 0;

      if (calibExists) {
        await calibInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/calibration.zip');
        console.log('✓ 校准数据集已选择（通过 ID 定位）');

        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'tests/e2e/screenshots/04-calibration-uploaded.png' });
        console.log('✓ 截图：校准数据集已上传');
      } else {
        // 备用方案：通过 accept 属性定位
        const calibInputByAccept = page.locator('input[type="file"][accept=".zip"]').first();
        const count = await calibInputByAccept.count();

        if (count > 0) {
          await calibInputByAccept.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/calibration.zip');
          console.log('✓ 校准数据集已选择（通过 accept 属性）');

          await page.waitForTimeout(1000);
          await page.screenshot({ path: 'tests/e2e/screenshots/04-calibration-uploaded.png' });
          console.log('✓ 截图：校准数据集已上传');
        } else {
          console.log('ℹ 未找到校准数据集输入框（可选功能）');
        }
      }
    } catch (e) {
      console.log('ℹ 校准数据集上传失败（这是可选的）:', e.message);
    }

    // 查找并点击"开始转换"按钮
    console.log('\n--- 步骤 4: 点击开始转换按钮 ---');

    // 尝试多种可能的按钮选择器（支持中英文）
    const buttonSelectors = [
      'button:has-text("Start")',           // 英文界面
      'button:has-text("开始转换")',        // 中文界面
      'button:has-text("开始")',           // 中文简化
      'button[type="submit"]',             // 按类型
      'button:has-text("转换")',           // 包含"转换"
      '[data-testid="start-conversion"]',  // 测试 ID
      '#start-conversion'                  // ID 选择器
    ];

    let buttonFound = false;
    for (const selector of buttonSelectors) {
      try {
        const button = page.locator(selector).first();
        if (await button.isVisible({ timeout: 2000 }).catch(() => false)) {
          console.log(`✓ 找到按钮: ${selector}`);

          // 截图：点击前
          await page.screenshot({ path: 'tests/e2e/screenshots/05-before-click.png' });

          // 点击按钮
          await button.click();
          buttonFound = true;
          console.log('✓ 已点击"Start"按钮');
          break;
        }
      } catch (e) {
        // 继续尝试下一个选择器
      }
    }

    if (!buttonFound) {
      console.error('✗ 未找到"开始转换"按钮');
      console.log('页面上的所有按钮：');
      const buttons = await page.locator('button').all();
      for (const btn of buttons) {
        const text = await btn.textContent();
        const visible = await btn.isVisible().catch(() => false);
        console.log(`  - "${text}" (visible: ${visible})`);
      }
    }

    // 等待并观察响应
    console.log('\n--- 步骤 5: 等待转换响应 ---');

    // 等待网络请求完成
    try {
      await page.waitForResponse(
        response => response.url().includes('/api/convert'),
        { timeout: 60000 }  // 增加到 60 秒
      );
      console.log('✓ 收到转换 API 响应');
    } catch (e) {
      console.log('⚠ 60秒内未收到转换 API 响应');
    }

    // 等待一段时间以观察控制台输出
    await page.waitForTimeout(8000);

    // 截图：最终状态
    await page.screenshot({ path: 'tests/e2e/screenshots/06-final-state.png' });
    console.log('✓ 截图：最终状态');

    // 检查页面上的错误消息
    console.log('\n--- 步骤 6: 检查页面错误消息 ---');

    // 查找可能的错误消息元素
    const errorSelectors = [
      '[data-testid="error"]',
      '.error',
      '.error-message',
      '[role="alert"]',
      'text=/错误/i'
    ];

    for (const selector of errorSelectors) {
      try {
        const errorElement = page.locator(selector).first();
        if (await errorElement.isVisible({ timeout: 1000 }).catch(() => false)) {
          const errorText = await errorElement.textContent();
          console.log(`发现错误消息 (${selector}):`, errorText);
        }
      } catch (e) {
        // 继续尝试
      }
    }

    // 获取整个页面的文本内容
    const pageText = await page.textContent('body');
    if (pageText.includes('错误') || pageText.includes('[object Object]')) {
      console.log('\n⚠ 页面包含错误消息或 [object Object]');
    }

    console.log('\n=== 测试完成 ===\n');
  });

  test('直接查看网络请求', async ({ page }) => {
    console.log('\n=== 测试：直接查看网络请求 ===\n');

    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // 设置响应拦截器
    const apiResponses: any[] = [];

    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        const data = {
          url: response.url(),
          method: response.request().method(),
          status: response.status(),
          headers: await response.allHeaders(),
          body: ''
        };

        try {
          data.body = await response.text();
        } catch (e) {
          data.body = '[无法读取响应体]';
        }

        apiResponses.push(data);
        console.log('\n[API 响应记录]');
        console.log(JSON.stringify(data, null, 2));
      }
    });

    // 上传文件（通过 ID 和 accept 属性精确定位）
    console.log('\n--- 上传测试文件 ---');

    let uploadedCount = 0;

    // 1. 上传模型文件
    try {
      const modelInput = page.locator('input[type="file"][accept*=".pt"], input[type="file"][accept*=".pth"]').first();
      if (await modelInput.count() > 0) {
        await modelInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/best.pt');
        console.log(`✓ 文件 1/3 已上传: best.pt`);
        uploadedCount++;
      }
    } catch (e) {
      console.log(`⚠ 上传模型文件失败:`, e.message);
    }

    // 2. 上传 YAML 文件
    try {
      const yamlInput = page.locator('#yaml-file-input');
      if (await yamlInput.count() > 0) {
        await yamlInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/household_trash.yaml');
        console.log(`✓ 文件 2/3 已上传: household_trash.yaml`);
        uploadedCount++;
      }
    } catch (e) {
      console.log(`⚠ 上传 YAML 文件失败:`, e.message);
    }

    // 3. 上传校准数据集
    try {
      const calibInput = page.locator('#calibration-file-input');
      if (await calibInput.count() > 0) {
        await calibInput.setInputFiles('/Users/harryhua/Documents/GitHub/model-converter/demo/calibration.zip');
        console.log(`✓ 文件 3/3 已上传: calibration.zip`);
        uploadedCount++;
      }
    } catch (e) {
      console.log(`⚠ 上传校准数据集失败（可选）:`, e.message);
    }

    console.log(`\n成功上传 ${uploadedCount}/3 个文件`);

    await page.waitForTimeout(1500);

    // 点击转换按钮（支持中英文）
    console.log('\n--- 点击转换按钮 ---');
    const button = page.locator('button:has-text("Start")').or(
      page.locator('button:has-text("开始转换")')
    ).or(
      page.locator('button:has-text("开始")')
    ).or(
      page.locator('button[type="submit"]')
    ).first();

    if (await button.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('✓ 找到转换按钮');

      // 截图：点击前
      await page.screenshot({ path: 'tests/e2e/screenshots/test2-before-click.png' });

      await button.click();
      console.log('✓ 已点击转换按钮');

      // 等待 API 响应
      await page.waitForTimeout(5000);

      // 输出所有收集的 API 响应
      console.log('\n=== 收集到的所有 API 响应 ===');
      apiResponses.forEach((resp, index) => {
        console.log(`\n响应 #${index + 1}:`);
        console.log(JSON.stringify(resp, null, 2));
      });

      // 保存到文件
      const fs = require('fs');
      fs.writeFileSync(
        'tests/e2e/api-responses.json',
        JSON.stringify(apiResponses, null, 2)
      );
      console.log('\n✓ API 响应已保存到 tests/e2e/api-responses.json');
    } else {
      console.log('✗ 未找到转换按钮');
    }
  });
});
