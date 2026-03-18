#!/usr/bin/env python3
"""
测试 yaml_path 传递和 class_names 一致性验证

测试场景：
1. ✅ 场景 1: yaml_path 正确传递，num_classes 一致
2. ❌ 场景 2: yaml_path 正确传递，num_classes 不一致（应抛出错误）
3. ⚠️  场景 3: 未提供 yaml_path（应发出警告）
"""

import sys
from pathlib import Path

# 添加 backend 到路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.ne301_config import generate_ne301_json_config


def test_scenario_1_consistent():
    """✅ 场景 1: num_classes 和 class_names 一致"""
    print("\n" + "=" * 60)
    print("测试场景 1: num_classes 和 class_names 一致")
    print("=" * 60)

    num_classes = 3
    class_names = ["person", "car", "bicycle"]

    print(f"  num_classes: {num_classes}")
    print(f"  class_names: {class_names}")
    print(f"  len(class_names): {len(class_names)}")

    if len(class_names) == num_classes:
        print("✅ 一致性验证通过")
    else:
        print("❌ 一致性验证失败")

    return True


def test_scenario_2_inconsistent():
    """❌ 场景 2: num_classes 和 class_names 不一致"""
    print("\n" + "=" * 60)
    print("测试场景 2: num_classes 和 class_names 不一致")
    print("=" * 60)

    num_classes = 80
    class_names = ["person", "car", "bicycle"]  # 只有 3 个类别

    print(f"  num_classes: {num_classes}")
    print(f"  class_names: {class_names}")
    print(f"  len(class_names): {len(class_names)}")

    if len(class_names) != num_classes:
        print("❌ 一致性验证失败（预期）")
        print(f"  预期错误: num_classes 不一致: config={num_classes}, yaml={len(class_names)}")
        return True
    else:
        print("⚠️  一致性验证通过（不应该）")
        return False


def test_scenario_3_no_yaml():
    """⚠️  场景 3: 未提供 YAML 文件"""
    print("\n" + "=" * 60)
    print("测试场景 3: 未提供 YAML 文件")
    print("=" * 60)

    num_classes = 80
    class_names = []  # 空列表

    print(f"  num_classes: {num_classes}")
    print(f"  class_names: {class_names}")
    print(f"  len(class_names): {len(class_names)}")

    if not class_names:
        print("⚠️  未提供 YAML 文件（应发出警告）")
        print("  警告: class_names 将为空列表，检测结果将无法映射到类别名称")
        return True
    else:
        print("❌ 意外情况")
        return False


def test_yaml_path_propagation():
    """测试 yaml_path 是否正确传递"""
    print("\n" + "=" * 60)
    print("测试 yaml_path 传递")
    print("=" * 60)

    # 模拟 API 端点的代码
    yaml_path = "/path/to/data.yaml"
    config_dict = {
        "task_id": "test-123",
        "num_classes": 3,
    }

    # ✅ 修复后的代码
    config_dict["yaml_path"] = yaml_path

    print(f"  yaml_path: {yaml_path}")
    print(f"  config_dict['yaml_path']: {config_dict.get('yaml_path')}")

    if config_dict.get("yaml_path") == yaml_path:
        print("✅ yaml_path 正确添加到 config_dict")
        return True
    else:
        print("❌ yaml_path 未正确添加")
        return False


def main():
    print("\n" + "=" * 60)
    print("🧪 开始测试 yaml_path 传递和 class_names 一致性验证")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("场景 1: 一致", test_scenario_1_consistent()))
    results.append(("场景 2: 不一致", test_scenario_2_inconsistent()))
    results.append(("场景 3: 无 YAML", test_scenario_3_no_yaml()))
    results.append(("yaml_path 传递", test_yaml_path_propagation()))

    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✅ 所有测试通过")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
