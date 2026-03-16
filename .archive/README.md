# 归档文件说明

本目录包含项目中失效、过时或不再需要的文件，保留用于历史参考。

## 目录结构

```
.archive/
├── deprecated_docs/       # 失效的诊断和修复文档
├── deprecated_scripts/    # 失效的诊断和测试脚本
├── deprecated_tools/      # 已废弃的工具（旧版本）
├── temp_files/           # 临时文件和测试输出
├── .old/                 # 历史归档（早期版本）
├── tests/                # 历史测试文件
└── reports/              # 历史报告
```

## 归档内容

### deprecated_docs/ (13 个文件)

**NE301 问题诊断报告**:
- NE301_COMPLETE_FIX_REPORT.md - 完整修复报告
- NE301_DIAGNOSIS_SUMMARY.md - 诊断摘要
- NE301_FIRMWARE_SIZE_*.md - 固件大小问题分析和修复
- NE301_FIX_GUIDE.md - 修复指南
- NE301_OTA_DEEP_ANALYSIS.md - OTA 深度分析
- NE301_QUANTIZATION_FIX_REPORT.md - 量化修复报告
- NE301_VERSION_FIX_REPORT.md - 版本修复报告

**OTA 问题调查**:
- OTA_HEADER_INVESTIGATION_REPORT.md - OTA Header 调查
- OTA_VALIDATION_INVESTIGATION.md - OTA 验证调查
- OTA_VERSION_3_TEST_REPORT.md - OTA v3 测试报告

**测试清单**:
- TEST_CHECKLIST.md - 测试检查清单

**归档时间**: 2026-03-16
**归档原因**: 问题已解决，报告保留供历史参考

### deprecated_scripts/ (1 个文件)

- verify_ota_firmware.py - OTA 固件验证脚本（已集成到主代码中）

**归档时间**: 2026-03-16
**归档原因**: 功能已集成到核心代码，独立脚本不再需要

### deprecated_tools/ (2 个文件)

- tflite_quant.py - 旧版 ST 量化脚本
- user_config_quant.yaml - 旧版量化配置

**归档时间**: 2026-03-16
**归档原因**: 已迁移到 `backend/tools/quantization/` 目录

### temp_files/ (4 个文件)

- 0-model-training-and-deployment.md - 未使用的文档草稿
- test_output.json - 测试输出文件
- browser-test.js - 未使用的浏览器测试
- e2e_screenshots/ - E2E 测试截图

**归档时间**: 2026-03-16
**归档原因**: 临时文件，不再需要

## 保留策略

- **保留期限**: 长期保留，供历史参考
- **删除策略**: 除非项目重构，否则不主动删除
- **访问频率**: 低（仅在需要历史信息时访问）

## 当前有效文件位置

### 文档
- 工作流文档: `docs/WORKFLOW_*.md`
- 校准指南: `docs/CALIBRATION_GUIDE.md`
- 配置参考: `docs/CONFIGURATION_REFERENCE.md`
- 项目说明: `README.md`, `CLAUDE.md`

### 脚本
- 初始化脚本: `scripts/init-ne301.sh`
- 启动脚本: `scripts/start.sh`, `scripts/start.bat`
- 脚本说明: `scripts/README.md`

### 工具
- ST 量化脚本: `backend/tools/quantization/`

---

**最后更新**: 2026-03-16
**维护者**: 项目团队
