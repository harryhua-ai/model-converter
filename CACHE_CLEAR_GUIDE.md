# 浏览器缓存清除指南

## 问题描述
如果您的 Web 界面显示以下错误信息：
- `解析到的类别数量: null`
- `未能解析类别数量`
- 或者界面功能与最新版本不一致

可能是因为浏览器缓存了旧版本的代码。

---

## ✅ 解决方案

### 方法 1: 硬刷新（推荐）

**Windows/Linux:**
- 按 `Ctrl + Shift + R`
- 或 `Ctrl + F5`

**Mac:**
- 按 `Cmd + Shift + R`

---

### 方法 2: 清除浏览器缓存

#### Chrome/Edge
1. 打开开发者工具（`F12` 或 `Ctrl+Shift+I`）
2. **右键点击**浏览器地址栏旁边的刷新按钮
3. 选择 **"清空缓存并硬性重新加载"**

#### Firefox
1. 按 `Ctrl + Shift + Delete`
2. 选择 "缓存"
3. 点击 "立即清除"
4. 刷新页面（`F5`）

#### Safari
1. 按 `Cmd + Option + E`
2. 刷新页面（`Cmd + R`）

---

### 方法 3: 开发者工具强制刷新

1. 打开开发者工具（`F12`）
2. 切换到 **Network（网络）** 标签
3. 勾选 **"Disable cache（禁用缓存）"**
4. 刷新页面（`F5`）

---

## ✅ 验证缓存已清除

打开浏览器控制台（`F12` → Console 标签），应该看到：

```
✅ 已加载最新版本
当前 JS 文件: index-DuzcnAYB.js
```

或者上传 YAML 文件后应该看到：

```
解析到的类别数量: 30
```

而不是：

```
解析到的类别数量: null
未能解析类别数量
```

---

## 📝 当前版本信息

**最新前端版本:**
- 构建时间: 2025-03-12 23:20
- JS 文件名: `index-DuzcnAYB.js`
- 包含修复:
  - ✅ YAML 解析支持多种格式（names, classes, labels, categories）
  - ✅ 改进的错误信息显示
  - ✅ 类别数量自动识别

---

## 🔍 检查当前加载的版本

在浏览器控制台执行：

```javascript
// 检查当前加载的 JS 文件
const scripts = document.querySelectorAll('script[src]');
scripts.forEach(script => {
  if (script.src.includes('index-')) {
    console.log('当前加载的文件:', script.src.split('/').pop());
  }
});
```

**预期输出:** `index-DuzcnAYB.js`

如果显示其他文件名（如 `index-DTmlQgHt.js`），说明需要清除缓存。
