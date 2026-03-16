# Scripts 目录说明

本目录包含项目部署和验证相关的核心脚本。

## 📦 核心部署脚本

### start.sh
**用途**: Linux/macOS 平台启动脚本

**功能**:
- 自动检测并安装项目依赖
- 配置 Python 虚拟环境
- 启动后端和前端服务

**使用**:
```bash
./scripts/start.sh
```

**引用**: README.md、部署文档

---

### start.bat
**用途**: Windows 平台启动脚本

**功能**:
- Windows 平台自动安装依赖
- 配置 Python 虚拟环境
- 启动服务

**使用**:
```cmd
scripts\start.bat
```

**引用**: README.md、部署文档

---

### init-ne301.sh
**用途**: NE301 项目初始化脚本

**功能**:
- 自动克隆 NE301 项目仓库
- 拉取 NE301 Docker 镜像（camthink/ne301-dev:latest）
- 配置 NE301 开发环境

**使用**:
```bash
./scripts/init-ne301.sh
```

**引用**: Docker 容器启动流程、后端 Dockerfile

---

## 🔍 验证工具

### verify_ota_firmware.py
**用途**: OTA 固件验证工具

**功能**:
- 验证生成的固件格式是否正确
- 检查 OTA header 完整性
- 验证 Model Package header
- 检查 CRC32 校验和

**使用**:
```bash
python scripts/verify_ota_firmware.py <firmware.bin>
```

**输出示例**:
```
OTA Header:
  Magic: 0x4F544131
  Version: 1.0.0.1
  Size: 123456 bytes

Model Package Header:
  Model Name: yolov8n
  Input Size: 640
  Num Classes: 80

CRC32: 0xABCD1234 ✓
```

**适用场景**:
- 用户下载固件后验证完整性
- 开发调试时检查固件格式
- 自动化测试中的固件验证

---

## 📝 历史清理记录

**清理时间**: 2026-03-16

**清理内容**:
- 删除 19 个临时调试脚本
- 保留 4 个核心脚本
- 目录文件数: 23 → 4

**删除的脚本类型**:
- 版本测试脚本 (test_version_*.py, quick_test_v3.py)
- 问题诊断脚本 (diagnose_*.py)
- 临时修复脚本 (fix_*.py)
- E2E 测试 demo (e2e_test_demo.py)
- 其他临时验证脚本

**清理原因**:
- 所有临时问题已解决
- 正式测试已迁移至 tests/ 目录
- 简化项目结构，提高可维护性

---

## 🔗 相关文档

- [部署指南](../README.md#部署指南)
- [Docker 部署](../README.docker.md)
- [开发环境设置](../CLAUDE.md#开发环境设置)