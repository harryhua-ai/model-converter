# 校准数据集指南

## 概述

本文档提供校准数据集的详细指南，包括数据准备、最佳实践和常见问题解答。

## 什么是校准数据集？

校准数据集用于量化过程中调整模型参数，使 int8 量化后的模型保持较高的精度。与训练数据集不同，校准数据集**不需要标注**。

### 为什么需要校准数据集？

**量化原理**:
- Float32 → Int8 需要确定缩放因子
- 缩放因子取决于数据分布
- 校准数据集提供代表性样本

**精度影响**:
| 校准方式 | 精度损失 | 适用场景 |
|---------|---------|---------|
| Fake Quantization | 5-10% | 快速原型验证 |
| 真实校准数据集 | 1-3% | 生产环境部署 |

## 数据准备

### 图片要求

**格式支持**:
- `.jpg` / `.jpeg`
- `.png`
- `.bmp`（部分支持）

**分辨率**:
- 与模型输入尺寸一致
- 可以是原始图片（系统自动缩放）

**颜色空间**:
- RGB（推荐）
- BGR（OpenCV 格式）
- 灰度图（自动转换）

### 数据量建议

| 模型复杂度 | 最小数量 | 推荐数量 | 最大数量 |
|-----------|---------|---------|---------|
| 小型（YOLOv8n） | 32 | 100 | 200 |
| 中型（YOLOv8s/m） | 50 | 150 | 200 |
| 大型（YOLOv8l/x） | 100 | 200 | 200 |

**注意**: 系统自动限制最大 200 张图片，防止内存溢出。

### 数据分布

**场景覆盖**:
- ✅ 不同光照条件（白天/夜晚/室内/室外）
- ✅ 不同拍摄角度（正面/侧面/俯视）
- ✅ 不同背景环境（简单/复杂/动态）
- ✅ 不同目标状态（单个/多个/遮挡）

**时间分布**:
- ✅ 不同时间段采集
- ✅ 不同季节/天气
- ✅ 不同设备拍摄

**难度分布**:
- ✅ 简单样本（60%）
- ✅ 中等样本（30%）
- ✅ 困难样本（10%）

### 数据选择策略

#### 策略 1: 随机采样

```python
import os
import random
import shutil

def random_sampling(source_dir: str, output_dir: str, num_samples: int = 100):
    """随机采样图片"""
    # 获取所有图片
    image_files = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(root, f))

    # 随机采样
    sampled = random.sample(image_files, min(num_samples, len(image_files)))

    # 复制到输出目录
    os.makedirs(output_dir, exist_ok=True)
    for i, src in enumerate(sampled):
        dst = os.path.join(output_dir, f"calib_{i:04d}.jpg")
        shutil.copy2(src, dst)

    print(f"已采样 {len(sampled)} 张图片到 {output_dir}")
```

#### 策略 2: 聚类采样（推荐）

```python
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image

def cluster_sampling(source_dir: str, output_dir: str, num_samples: int = 100):
    """基于聚类的采样（覆盖更多场景）"""
    # 提取图片特征
    features = []
    image_files = []

    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(root, f)
                img = Image.open(img_path).resize((64, 64))
                features.append(np.array(img).flatten())
                image_files.append(img_path)

    features = np.array(features)

    # K-means 聚类
    kmeans = KMeans(n_clusters=num_samples, random_state=42)
    labels = kmeans.fit_predict(features)

    # 从每个聚类中选择距离中心最近的样本
    sampled = []
    for i in range(num_samples):
        cluster_indices = np.where(labels == i)[0]
        if len(cluster_indices) > 0:
            # 选择第一个样本
            sampled.append(image_files[cluster_indices[0]])

    # 复制到输出目录
    os.makedirs(output_dir, exist_ok=True)
    for i, src in enumerate(sampled):
        dst = os.path.join(output_dir, f"calib_{i:04d}.jpg")
        shutil.copy2(src, dst)

    print(f"已采样 {len(sampled)} 张图片到 {output_dir}")
```

## 数据格式

### ZIP 文件结构

**推荐结构 1**: 扁平结构
```
calibration.zip
├── image_001.jpg
├── image_002.jpg
├── image_003.png
└── ...
```

**推荐结构 2**: 子目录结构
```
calibration.zip
├── day/
│   ├── day_001.jpg
│   └── day_002.jpg
├── night/
│   ├── night_001.jpg
│   └── night_002.jpg
└── indoor/
    ├── indoor_001.jpg
    └── indoor_002.jpg
```

**系统处理逻辑**:
1. 解压 ZIP 文件
2. 递归遍历所有子目录
3. 查找 `.jpg/.jpeg/.png` 文件
4. 返回第一个包含图片的目录

### 创建 ZIP 文件

**方法 1: 命令行**

```bash
# 假设图片在 calibration_images/ 目录
cd calibration_images/
zip -r ../calibration.zip *.jpg *.png

# 验证 ZIP 文件
unzip -l ../calibration.zip
```

**方法 2: Python 脚本**

```python
import zipfile
import os

def create_calibration_zip(image_dir: str, output_zip: str):
    """创建校准数据集 ZIP 文件"""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, image_dir)
                    zipf.write(file_path, arcname)

    print(f"已创建校准 ZIP: {output_zip}")
    print(f"文件数量: {len(zipf.namelist())}")
```

## 最佳实践

### 数据质量检查

```python
import os
from PIL import Image
from pathlib import Path

def validate_calibration_dataset(dataset_dir: str) -> dict:
    """验证校准数据集质量"""
    stats = {
        'total_images': 0,
        'valid_images': 0,
        'invalid_images': [],
        'formats': {},
        'resolutions': set(),
        'issues': []
    }

    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                stats['total_images'] += 1
                file_path = os.path.join(root, file)

                try:
                    # 检查图片
                    img = Image.open(file_path)
                    img.verify()

                    # 重新打开以获取详细信息
                    img = Image.open(file_path)
                    stats['valid_images'] += 1
                    stats['formats'][img.format] = stats['formats'].get(img.format, 0) + 1
                    stats['resolutions'].add(img.size)

                except Exception as e:
                    stats['invalid_images'].append(file_path)
                    stats['issues'].append(f"{file}: {str(e)}")

    # 打印统计信息
    print(f"总图片数: {stats['total_images']}")
    print(f"有效图片: {stats['valid_images']}")
    print(f"无效图片: {len(stats['invalid_images'])}")
    print(f"格式分布: {stats['formats']}")
    print(f"分辨率种类: {len(stats['resolutions'])}")

    if stats['issues']:
        print("\n问题列表:")
        for issue in stats['issues']:
            print(f"  - {issue}")

    return stats
```

### 数据增强（可选）

**注意**: 校准数据集通常**不需要**数据增强。但某些场景下可以适度使用。

**支持的增强**:
- ✅ 亮度调整（±20%）
- ✅ 对比度调整（±20%）
- ❌ 旋转/翻转（不推荐）
- ❌ 裁剪/缩放（不推荐）

### 数据隐私

**敏感信息处理**:
- ✅ 模糊人脸
- ✅ 遮挡车牌
- ✅ 移除 EXIF 元数据

```python
from PIL import Image
from PIL.ExifTags import TAGS

def remove_exif(image_path: str, output_path: str):
    """移除图片 EXIF 信息"""
    img = Image.open(image_path)

    # 创建新图片（不包含 EXIF）
    data = list(img.getdata())
    img_no_exif = Image.new(img.mode, img.size)
    img_no_exif.putdata(data)

    img_no_exif.save(output_path)
```

## 常见问题解答

### Q1: 校准数据集需要标注吗？

**A**: 不需要。校准数据集只需要原始图片，不需要标注文件（如 `.txt`, `.xml`, `.json`）。

### Q2: 校准数据集和测试数据集的区别？

**A**:
| 类型 | 用途 | 是否需要标注 | 数量 |
|------|------|-------------|------|
| 训练集 | 训练模型 | ✅ 需要 | 大（数千张） |
| 验证集 | 调参、早停 | ✅ 需要 | 中（数百张） |
| 测试集 | 评估性能 | ✅ 需要 | 中（数百张） |
| 校准集 | 量化校准 | ❌ 不需要 | 小（100-200张） |

### Q3: 可以使用训练数据集作为校准集吗？

**A**: 可以，但建议使用独立的验证集或测试集作为校准集，以避免过拟合。

### Q4: 校准数据集越多越好吗？

**A**: 不一定。过多的校准数据：
- ❌ 增加内存消耗
- ❌ 延长量化时间
- ❌ 不一定提高精度

**推荐**: 100-200 张代表性图片即可。

### Q5: 图片分辨率有什么要求？

**A**: 系统会自动调整图片分辨率到模型输入尺寸。建议：
- 原始图片分辨率 ≥ 模型输入尺寸
- 避免过度缩放（损失细节）
- 保持宽高比一致

### Q6: 可以混合不同场景的图片吗？

**A**: 可以，甚至推荐！混合不同场景可以提高模型的泛化能力。

### Q7: 校准数据集需要覆盖所有类别吗？

**A**: 理想情况下应该覆盖所有类别，但不是必须的。重点是覆盖数据分布。

### Q8: 没有 GPU 可以运行量化吗？

**A**: 可以。量化过程主要在 CPU 上运行，速度较快（通常几分钟）。

### Q9: 如何评估校准效果？

**A**:
```python
# 1. 量化前后精度对比
mAP_before = evaluate_model(model_float32, test_dataset)
mAP_after = evaluate_model(model_int8, test_dataset)

print(f"精度损失: {(mAP_before - mAP_after) / mAP_before * 100:.2f}%")

# 2. 推理速度对比
time_before = benchmark_inference(model_float32)
time_after = benchmark_inference(model_int8)

print(f"速度提升: {time_before / time_after:.2f}x")
```

### Q10: 校准数据集可以复用吗？

**A**: 可以。同一个校准集可以用于：
- 同一模型的不同量化配置
- 同类型的不同模型
- 不同版本的模型迭代

## 示例流程

### 完整的校准数据集准备流程

```bash
# 1. 收集原始图片
mkdir -p raw_images/
# ... 复制图片到 raw_images/

# 2. 验证图片质量
python validate_images.py raw_images/

# 3. 采样
python sample_images.py raw_images/ calibration_images/ --num 150

# 4. 再次验证
python validate_images.py calibration_images/

# 5. 创建 ZIP 文件
cd calibration_images/
zip -r ../calibration.zip *.jpg *.png

# 6. 验证 ZIP 文件
unzip -l ../calibration.zip | head -20
```

## 参考

- [TensorFlow 量化指南](https://www.tensorflow.org/lite/performance/post_training_quantization)
- [PyTorch 量化教程](https://pytorch.org/docs/stable/quantization.html)
- [ONNX Runtime 量化](https://onnxruntime.ai/docs/performance/quantization.html)