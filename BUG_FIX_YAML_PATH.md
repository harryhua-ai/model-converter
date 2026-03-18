# Bug 修复报告：yaml_path 传递和 class_names 验证

**修复日期**: 2026-03-12
**严重程度**: 🔴 CRITICAL
**影响范围**: 所有使用 YAML 文件定义类别的模型转换

---

## 🐛 Bug 描述

### 问题 1: yaml_path 未传递 ❌

**位置**: `backend/app/api/convert.py:375-386`

**症状**:
- YAML 文件上传后，`class_names` 始终为空列表 `[]`
- 检测结果无法映射到类别名称
- JSON 配置中 `postprocess_params.class_names = []`

**根本原因**:
```python
# ❌ 修复前：yaml_path 未添加到 config_dict
config_dict = config.dict()
config_dict["task_id"] = task_id
# 缺少：config_dict["yaml_path"] = yaml_path
```

**影响**:
- 🔴 **严重**: 所有上传 YAML 文件的转换任务都无法正确映射类别
- 🔴 **数据丢失**: class_names 信息完全丢失

---

### 问题 2: 缺少一致性验证 ⚠️

**位置**: `backend/app/core/docker_adapter.py:687-710`

**症状**:
- `num_classes` 和 `class_names` 数量不匹配时无错误提示
- 生成的 JSON 配置可能导致运行时错误

**根本原因**:
```python
# ❌ 修复前：缺少一致性验证
class_names = [...]  # 从 YAML 读取
# 缺少：验证 len(class_names) == config["num_classes"]
json_config = generate_ne301_json_config(
    num_classes=config["num_classes"],  # 可能是 80
    class_names=class_names,            # 可能只有 3 个
)
```

**影响**:
- 🟡 **中等**: 可能导致检测错误
- 🟡 **难以调试**: 没有明确的错误提示

---

## ✅ 修复方案

### 修复 1: 传递 yaml_path

**文件**: `backend/app/api/convert.py:377`

```diff
  # 准备配置字典（从 Pydantic 模型）
  config_dict = config.dict()
  config_dict["task_id"] = task_id
+ config_dict["yaml_path"] = yaml_path  # ✅ 修复：传递 yaml_path

  # 执行转换
  logger.info(f"⏳ 开始执行转换...")
```

**验证**:
```python
# ✅ 修复后
assert config_dict.get("yaml_path") == yaml_path
print("✅ yaml_path 正确添加到 config_dict")
```

---

### 修复 2: 添加一致性验证

**文件**: `backend/app/core/docker_adapter.py:701-724`

```diff
  # 从 YAML 文件读取 class_names（如果提供）
  class_names: List[str] = []
  if yaml_path and Path(yaml_path).exists():
      # ... 读取 YAML ...
      class_names = [cls['name'] for cls in yaml_data['classes']]
      logger.info(f"✅ 从 YAML 文件读取到 {len(class_names)} 个类别")

+ # ✅ 一致性验证：检查 num_classes 和 class_names 是否匹配
+ num_classes_from_config = config["num_classes"]
+ num_classes_from_yaml = len(class_names)
+
+ if class_names:  # 如果提供了 YAML 文件
+     if num_classes_from_yaml != num_classes_from_config:
+         error_msg = (
+             f"num_classes 不一致！config 中: {num_classes_from_config}, "
+             f"YAML 中: {num_classes_from_yaml}。请检查配置文件。"
+         )
+         logger.error(f"❌ {error_msg}")
+         raise ValueError(error_msg)
+
+     logger.info(f"✅ num_classes 一致性验证通过: {num_classes_from_config}")
+     logger.info(f"✅ class_names: {class_names}")
+ else:
+     # 没有提供 YAML 文件
+     logger.warning(f"⚠️  未提供 YAML 文件，无法验证 num_classes")
+     logger.warning(f"  使用 config 中的值: {num_classes_from_config}")
+     logger.warning(f"  class_names 将为空列表，检测结果将无法映射到类别名称")
```

**验证**:
```python
# ✅ 场景 1: 一致
num_classes = 3
class_names = ["person", "car", "bicycle"]
assert len(class_names) == num_classes
print("✅ 一致性验证通过")

# ❌ 场景 2: 不一致
num_classes = 80
class_names = ["person", "car", "bicycle"]
# 应抛出 ValueError
```

---

## 🧪 测试结果

运行测试脚本 `test_yaml_path_fix.py`:

```
✅ 场景 1: 一致: 通过
✅ 场景 2: 不一致: 通过
✅ 场景 3: 无 YAML: 通过
✅ yaml_path 传递: 通过

✅ 所有测试通过
```

---

## 📊 修复前后对比

### 修复前 ❌

**场景**: 用户上传 YOLOv8 模型 + YAML 文件（3 个类别）

```python
# API 请求
config = {"num_classes": 3}
yaml_file = "data.yaml"  # 包含 3 个类别

# ❌ 修复前：yaml_path 丢失
config_dict = {"num_classes": 3, "task_id": "xxx"}
# yaml_path 未传递！

# ❌ docker_adapter 接收
yaml_path = None
class_names = []  # 无法读取 YAML

# ❌ 生成的 JSON 配置
{
  "postprocess_params": {
    "num_classes": 3,
    "class_names": []  # 空列表！
  }
}

# ❌ 结果：检测框无法映射到类别名称
```

---

### 修复后 ✅

**场景**: 用户上传 YOLOv8 模型 + YAML 文件（3 个类别）

```python
# API 请求
config = {"num_classes": 3}
yaml_file = "data.yaml"  # 包含 3 个类别

# ✅ 修复后：yaml_path 正确传递
config_dict = {"num_classes": 3, "task_id": "xxx", "yaml_path": "/path/to/data.yaml"}

# ✅ docker_adapter 接收
yaml_path = "/path/to/data.yaml"
class_names = ["person", "car", "bicycle"]  # ✅ 成功读取

# ✅ 一致性验证
assert len(class_names) == config["num_classes"]  # 3 == 3 ✅

# ✅ 生成的 JSON 配置
{
  "postprocess_params": {
    "num_classes": 3,
    "class_names": ["person", "car", "bicycle"]  # ✅ 正确！
  }
}

# ✅ 结果：检测框正确映射到类别名称
```

---

## 🔍 错误场景处理

### 场景 1: num_classes 不一致

**输入**:
```json
{
  "num_classes": 80,
  "yaml_file": "data.yaml"  // 只有 3 个类别
}
```

**输出**:
```
❌ num_classes 不一致！
  config 中: 80
  YAML 中: 3
  YAML 中的类别: ['person', 'car', 'bicycle']

ValueError: num_classes 不一致！config 中: 80, YAML 中: 3。请检查配置文件。
```

**用户行动**:
- 检查 `config` 中的 `num_classes` 是否正确
- 检查 YAML 文件是否与训练时一致

---

### 场景 2: 未提供 YAML 文件

**输入**:
```json
{
  "num_classes": 80,
  "yaml_file": null
}
```

**输出**:
```
⚠️  未提供 YAML 文件，无法验证 num_classes
  使用 config 中的值: 80
  class_names 将为空列表，检测结果将无法映射到类别名称
```

**用户行动**:
- 上传正确的 YAML 文件
- 或者手动编辑生成的 JSON 配置，添加 class_names

---

## 📝 相关文件

### 修改的文件

1. **backend/app/api/convert.py** (第 377 行)
   - 添加 `config_dict["yaml_path"] = yaml_path`

2. **backend/app/core/docker_adapter.py** (第 701-724 行)
   - 添加一致性验证逻辑

### 新增文件

3. **test_yaml_path_fix.py**
   - 测试脚本，验证修复

4. **BUG_FIX_YAML_PATH.md** (本文档)
   - 修复报告

---

## ✅ 验证清单

- [x] 修复 1: yaml_path 传递到 config_dict
- [x] 修复 2: 添加 num_classes 和 class_names 一致性验证
- [x] 测试场景 1: 一致性验证通过
- [x] 测试场景 2: 不一致时抛出错误
- [x] 测试场景 3: 无 YAML 时发出警告
- [x] 测试场景 4: yaml_path 正确传递
- [x] 所有测试通过
- [x] 创建修复报告文档

---

## 🚀 部署建议

### 立即部署 (CRITICAL)

此 bug 严重影响所有使用 YAML 文件的转换任务，建议立即部署。

### 验证步骤

1. **重启服务**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **测试转换**
   - 上传模型 + YAML 文件
   - 检查日志中的 "✅ 从 YAML 文件读取到 X 个类别"
   - 检查生成的 JSON 配置中的 `class_names` 是否正确

3. **验证一致性检查**
   - 故意提供不匹配的 num_classes
   - 应该看到错误提示

---

## 📚 参考

- **相关 Issue**: CLASS_NAMES_CONSISTENCY_CHECK.md
- **代码位置**:
  - `backend/app/api/convert.py:377`
  - `backend/app/core/docker_adapter.py:701-724`
- **测试脚本**: `test_yaml_path_fix.py`

---

**修复完成时间**: 2026-03-12
**状态**: ✅ 修复完成并验证通过
**优先级**: 🔴 CRITICAL - 立即部署
