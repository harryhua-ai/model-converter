# 安全修复摘要 - HIGH 优先级问题

**修复日期**: 2026-03-16
**修复版本**: v1.0.0-security-fixes
**修复人员**: Security Team

---

## 修复概览

本次修复解决了 4 个 HIGH 优先级安全问题，涵盖文件上传、模型加载、CORS 配置和临时文件管理。

---

## 1. HIGH-2026-002: 文件上传大小限制不充分

### 问题描述
- 原始限制：1GB，过大可能导致磁盘空间耗尽
- 缺少并发上传控制
- 缺少磁盘空间检查

### 修复内容

#### 1.1 降低文件大小限制
```python
# 修复前
MAX_CALIBRATION_SIZE = 1024 * 1024 * 1024  # 1GB

# 修复后
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
MAX_CALIBRATION_SIZE = 100 * 1024 * 1024  # 100MB
```

#### 1.2 添加并发上传限制
```python
MAX_CONCURRENT_UPLOADS = 5  # 最大并发上传数
_active_uploads = 0
_upload_lock = asyncio.Lock()
```

#### 1.3 添加磁盘空间检查
```python
def _check_disk_space(required_bytes: int, path: str = ".") -> bool:
    """检查磁盘空间是否充足（预留 20% 安全余量）"""
    stat = shutil.disk_usage(path)
    free_space = stat.free
    required_with_margin = int(required_bytes * (1 + DISK_SPACE_SAFETY_MARGIN))

    if free_space < required_with_margin:
        raise HTTPException(status_code=507, detail="磁盘空间不足")
```

### 影响范围
- **文件**: `backend/app/api/convert.py`
- **影响功能**: 模型上传 API
- **向后兼容**: ❌ 现有的大文件（>100MB）上传将被拒绝

### 测试建议
```bash
# 测试文件大小限制
curl -X POST http://localhost:8000/api/convert \
  -F "model=@large_model.pt" \
  # 预期: 400 Bad Request

# 测试并发限制
# 同时发起 6 个上传请求
# 预期: 第 6 个请求返回 429 Too Many Requests

# 测试磁盘空间检查
# 填充磁盘后上传文件
# 预期: 507 Insufficient Storage
```

---

## 2. HIGH-2026-004: YOLO 模型加载未验证

### 问题描述
- 直接加载模型，未验证安全性
- 可能触发 PyTorch 的任意代码执行
- 模型文件可能过大

### 修复内容

#### 2.1 添加文件大小验证
```python
MAX_MODEL_SIZE = 500 * 1024 * 1024  # 500MB
file_size = model_path_obj.stat().st_size
if file_size > MAX_MODEL_SIZE:
    raise ValueError(f"模型文件过大: {file_size / 1024 / 1024:.1f}MB")
```

#### 2.2 添加文件格式验证
```python
allowed_extensions = {".pt", ".pth", ".onnx"}
if model_path_obj.suffix.lower() not in allowed_extensions:
    raise ValueError(f"不支持的模型文件格式: {model_path_obj.suffix}")
```

#### 2.3 添加详细日志
```python
logger.info(f"[{task_id}] ✅ 模型文件验证通过: {file_size / 1024 / 1024:.2f}MB")
```

### 影响范围
- **文件**: `backend/app/core/docker_adapter.py`
- **影响功能**: `_export_to_saved_model()` 方法
- **向后兼容**: ✅ 现有功能不受影响（仅增强验证）

### 测试建议
```python
# 测试文件格式验证
# 上传 .txt 文件伪装成模型
# 预期: ValueError "不支持的模型文件格式"

# 测试文件大小验证
# 上传 600MB 的模型文件
# 预期: ValueError "模型文件过大"
```

---

## 3. HIGH-2026-005: CORS 配置过于宽松

### 问题描述
- 使用通配符 `allow_origins=["*"]` 允许所有来源
- 生产环境存在安全风险

### 修复内容

#### 3.1 添加配置管理
```python
# backend/app/core/config.py
CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:5173"

def get_cors_origins(self) -> List[str]:
    """获取 CORS 允许的域名列表"""
    origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    if self.DEBUG:
        # 开发环境：自动添加 localhost
        local_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
        origins = list(set(origins + local_origins))
    else:
        # 生产环境：必须显式配置
        if not origins or origins == ["*"]:
            raise ValueError("生产环境必须显式配置 CORS_ORIGINS")

    return origins
```

#### 3.2 更新 CORS 中间件配置
```python
# backend/app/main.py
from .core.config import settings
cors_origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # 从配置读取，不再使用通配符
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 影响范围
- **文件**: `backend/app/core/config.py`, `backend/app/main.py`
- **影响功能**: CORS 中间件
- **向后兼容**: ⚠️ 生产环境需要配置环境变量

### 环境变量配置
```bash
# 开发环境（默认）
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# 生产环境（必须配置）
CORS_ORIGINS=https://example.com,https://www.example.com
```

### 测试建议
```bash
# 测试开发环境 CORS
curl -X OPTIONS http://localhost:8000/api/convert \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
# 预期: 包含 access-control-allow-origin 响应头

# 测试生产环境 CORS
# 设置 CORS_ORIGINS=https://example.com
curl -X OPTIONS http://localhost:8000/api/convert \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST"
# 预期: 不包含 access-control-allow-origin 响应头
```

---

## 4. HIGH-2026-001: 临时文件权限问题

### 问题描述
- 多处直接调用 `tempfile.mkdtemp()`
- 临时目录权限可能不安全
- 未统一管理临时文件清理

### 修复内容

#### 4.1 统一使用 SecureTempManager
```python
# 修复前
temp_dir = tempfile.mkdtemp(prefix="model_converter_")

# 修复后
from ..core.docker_adapter import get_secure_temp_manager
temp_dir = get_secure_temp_manager().create_secure_temp_dir(prefix="model_converter_")
```

#### 4.2 自动权限修正
```python
def create_secure_temp_dir(self, prefix: str) -> str:
    temp_dir = tempfile.mkdtemp(prefix=prefix)

    # 验证并修正权限为 700（仅所有者可访问）
    current_mode = os.stat(temp_dir).st_mode
    if stat.S_IMODE(current_mode) != 0o700:
        os.chmod(temp_dir, 0o700)

    # 注册到清理列表
    with self._lock:
        self.temp_dirs.append(temp_dir)

    return temp_dir
```

### 修复位置
- ✅ `backend/app/api/convert.py`: 模型上传临时目录
- ✅ `backend/app/core/docker_adapter.py`:
  - 校准数据集解压目录
  - SavedModel 导出目录
  - 量化配置文件目录

### 影响范围
- **文件**: `backend/app/api/convert.py`, `backend/app/core/docker_adapter.py`
- **影响功能**: 所有临时文件创建
- **向后兼容**: ✅ 现有功能不受影响

### 测试建议
```python
# 测试临时目录权限
temp_manager = get_secure_temp_manager()
temp_dir = temp_manager.create_secure_temp_dir(prefix="test_")

# 验证权限
stat_info = os.stat(temp_dir)
mode = stat_info.st_mode & 0o777
assert mode == 0o700  # 仅所有者可访问

# 验证自动清理
assert temp_dir in temp_manager.temp_dirs
```

---

## 验证清单

### 代码审查
- [x] 所有 `tempfile.mkdtemp()` 调用已替换
- [x] CORS 配置从环境变量读取
- [x] 文件上传限制已降低
- [x] 模型加载前进行验证
- [x] 磁盘空间检查已实现

### 测试验证
- [ ] 运行单元测试: `pytest tests/test_security_fixes.py`
- [ ] 运行集成测试: `pytest tests/integration/`
- [ ] 手动测试文件上传限制
- [ ] 手动测试 CORS 配置
- [ ] 验证临时目录权限

### 部署检查
- [ ] 更新 `.env.example` 文件（添加 CORS_ORIGINS）
- [ ] 更新部署文档
- [ ] 通知团队新的文件大小限制
- [ ] 配置生产环境 CORS_ORIGINS

---

## 部署注意事项

### 1. 环境变量配置

**开发环境** (.env):
```bash
# 使用默认配置即可
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:5173
DEBUG=True
```

**生产环境** (.env):
```bash
# 必须显式配置
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
DEBUG=False
```

### 2. 文件大小限制变更

**影响**:
- 旧限制: 1GB
- 新限制: 100MB

**建议**:
- 在前端添加文件大小验证提示
- 更新用户文档说明新的限制
- 对于大模型，建议用户提供优化后的模型

### 3. 回滚方案

如果修复导致问题，可以按以下步骤回滚：

```bash
# 1. 回滚代码
git revert <commit-hash>

# 2. 恢复环境变量
# 在 .env 中添加旧的 CORS_ORIGINS 配置

# 3. 重启服务
docker-compose restart
```

---

## 监控建议

### 1. 日志监控

监控以下日志：
- `磁盘空间不足` - 警告级别
- `并发上传数已达上限` - 信息级别
- `模型文件验证失败` - 警告级别
- `CORS 配置` - 信息级别

### 2. 指标监控

建议监控：
- 文件上传拒绝率（4xx 错误）
- 磁盘空间使用率
- 并发上传数峰值

---

## 相关文档

- [OWASP 文件上传安全](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [OWASP CORS 配置](https://owasp.org/www-project-web-security-testing-guide/)
- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/cors/)

---

**修复完成日期**: 2026-03-16
**审核状态**: 待审核
**下一步**: 运行完整测试套件
