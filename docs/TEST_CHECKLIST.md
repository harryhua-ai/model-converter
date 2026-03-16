# NE301 模型转换测试清单

## 测试环境准备状态

### ✅ 后端服务
- **状态**: 运行中 (healthy)
- **地址**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **版本**: 3.0.0.1 (已应用最新修改)

### ✅ 前端界面
- **访问地址**: http://localhost:8000
- **状态**: 就绪

### ✅ Docker 环境
- **容器**: model-converter-api (运行中)
- **NE301 镜像**: camthink/ne301-dev:latest (可用)

---

## 测试流程

### 第 1 步：Web 界面上传和转换 (5-10 分钟)

#### 1.1 访问前端界面
```
http://localhost:8000
```

#### 1.2 准备测试模型
- **推荐**: YOLOv8n 模型 (最小，测试快)
- **输入尺寸**: 256×256 (快速测试)
- **类别数**: 80 (COCO 数据集)

#### 1.3 上传模型
1. 点击 "上传模型" 按钮
2. 选择 `.pt` 或 `.pth` 文件
3. 填写配置：
   - 模型类型: YOLOv8
   - 输入尺寸: 256
   - 类别数: 80
   - 置信度阈值: 0.25

#### 1.4 观察转换进度
- ✅ 实时进度条
- ✅ WebSocket 日志推送
- ✅ 步骤详情显示

#### 1.5 下载固件
- 转换完成后自动下载
- 文件名格式: `ne301_Model_v3.0.0.XXXX_pkg.bin`
- 预期版本: **3.0.0.1** 或更高

---

### 第 2 步：验证固件 (1 分钟)

#### 2.1 使用验证脚本
```bash
# 替换 <downloaded_file> 为实际下载的文件名
python3 scripts/verify_ota_firmware.py <downloaded_file>
```

#### 2.2 预期输出
```
✅ 所有验证通过！
- OTA Header: Magic ✅ | Version ✅ | Size ✅ | CRC32 ✅
- Model Package Header: Magic ✅ | Version ✅
- Firmware Version: 3.0.0.1
```

---

### 第 3 步：NE301 设备导入测试 (2-3 分钟)

#### 3.1 连接 NE301 设备
- 访问 NE301 Web 界面
- 或通过 API 连接

#### 3.2 上传固件
1. 导航到: **系统设置 → OTA 升级**
2. 选择固件类型: **AI 模型** (ai_model)
3. 上传下载的固件文件
4. **点击预检查**

#### 3.3 观察预检查结果

##### ✅ 成功场景
```
预检查通过 ✅
- 固件类型匹配
- 版本验证通过
- CRC32 验证通过
- 分区大小验证通过
```

##### ❌ 失败场景
```
预检查失败 ❌
错误原因: <具体错误信息>
```

**如果失败，记录以下信息**:
1. 完整的错误消息
2. 错误代码
3. 失败的验证步骤

---

## 关键验证点

### 🔍 版本号验证
- **期望版本**: 3.0.0.1
- **位置**: OTA header offset 0xA0-0xA7
- **格式**: [major, minor, patch, build_low, build_high, 0, 0, 0]
- **十六进制**: `03 00 00 01 00 00 00 00`

### 🔍 CRC32 验证
- **算法**: 标准 CRC32 (IEEE 802.3)
- **Python**: `zlib.crc32()`
- **C**: `generic_crc32()`
- **初始值**: 0xFFFFFFFF
- **最终 XOR**: 0xFFFFFFFF

### 🔍 Magic Number 验证
- **OTA Header**: `0x4F544155` ("OTAU")
- **Model Package Header**: `0x314D364E` ("N6M1")

---

## 测试结果记录

### 测试信息
- **测试日期**: _______________
- **测试人员**: _______________
- **模型文件**: _______________
- **固件文件**: _______________

### Web 转换测试
- [ ] 前端界面可访问
- [ ] 模型上传成功
- [ ] 转换进度实时显示
- [ ] 转换完成无错误
- [ ] 固件自动下载
- [ ] 版本号为 3.0.0.1

### 固件验证测试
- [ ] OTA Header 验证通过
- [ ] CRC32 验证通过
- [ ] Model Package Header 验证通过
- [ ] 文件大小合理 (5-6 MB)

### NE301 设备测试
- [ ] NE301 Web 界面可访问
- [ ] 固件上传成功
- [ ] **预检查通过** ⭐
- [ ] OTA 升级成功
- [ ] 模型加载成功
- [ ] 推理功能正常

---

## 如果测试失败

### 收集以下信息

#### 1. 后端日志
```bash
docker logs model-converter-api --tail 100 > backend_logs.txt
```

#### 2. 前端控制台错误
- 打开浏览器开发者工具 (F12)
- 查看 Console 标签
- 截图或复制所有错误信息

#### 3. NE301 设备日志
```bash
# 在 NE301 设备上运行
tail -n 100 /var/log/ota.log > ne301_ota_logs.txt
# 或
journalctl -u ota-service -n 100 > ne301_system_logs.txt
```

#### 4. 固件详细信息
```bash
# 使用 hexdump 查看前 180 字节
hexdump -C -n 180 <firmware.bin> > firmware_header.txt
```

---

## 快速命令参考

### 重启服务
```bash
docker restart model-converter-api
```

### 查看日志
```bash
docker logs model-converter-api -f
```

### 验证固件
```bash
python3 scripts/verify_ota_firmware.py <firmware.bin>
```

### 检查服务状态
```bash
curl http://localhost:8000/health | jq .
```

### 查看任务列表
```bash
curl http://localhost:8000/api/tasks | jq .
```

---

## 预期测试时间

| 步骤 | 预计时间 |
|------|---------|
| Web 上传和转换 | 5-10 分钟 |
| 固件验证 | 1 分钟 |
| NE301 导入测试 | 2-3 分钟 |
| **总计** | **8-14 分钟** |

---

## 成功标准

✅ **最低标准**: NE301 预检查通过
✅ **完整标准**: NE301 设备成功加载模型并执行推理

---

**测试准备完成时间**: 2026-03-16
**环境状态**: ✅ 就绪
**下一步**: 开始 Web 界面测试

祝测试顺利！🎯
