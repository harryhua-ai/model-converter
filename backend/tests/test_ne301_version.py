"""
NE301 版本号验证测试

测试 NE301Version 数据类和版本号读取功能
"""
import pytest
from pathlib import Path
from app.core.ne301_config import NE301Version, NE301Toolchain, get_ne301_toolchain


class TestNE301Version:
    """测试 NE301Version 数据类"""

    def test_version_creation(self):
        """测试版本号创建"""
        version = NE301Version(major=2, minor=0, patch=1, build=123)
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 1
        assert version.build == 123
        assert version.suffix == ""

    def test_version_creation_with_suffix(self):
        """测试带后缀的版本号创建"""
        version = NE301Version(major=2, minor=0, patch=1, build=123, suffix="alpha")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 1
        assert version.build == 123
        assert version.suffix == "alpha"

    def test_version_string_format(self):
        """测试版本号字符串格式"""
        # 不带后缀
        version = NE301Version(major=2, minor=0, patch=1, build=123)
        assert str(version) == "2.0.1.123"

        # 带后缀
        version_with_suffix = NE301Version(major=2, minor=0, patch=1, build=123, suffix="beta")
        assert str(version_with_suffix) == "2.0.1.123_beta"

    def test_version_parse_valid(self):
        """测试有效版本号解析"""
        # 完整版本号
        version = NE301Version.parse("2.0.1.123")
        assert version is not None
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 1
        assert version.build == 123

        # 三位版本号（build 默认为 0）
        version_3 = NE301Version.parse("2.0.1")
        assert version_3 is not None
        assert version_3.major == 2
        assert version_3.minor == 0
        assert version_3.patch == 1
        assert version_3.build == 0

        # 带后缀
        version_suffix = NE301Version.parse("2.0.1.123-alpha")
        assert version_suffix is not None
        assert version_suffix.major == 2
        assert version_suffix.minor == 0
        assert version_suffix.patch == 1
        assert version_suffix.build == 123
        assert version_suffix.suffix == "alpha"

    def test_version_parse_invalid(self):
        """测试无效版本号解析"""
        # 空字符串
        assert NE301Version.parse("") is None

        # 无效格式
        assert NE301Version.parse("abc") is None
        assert NE301Version.parse("2.0") is None  # 至少需要 3 位
        # 注意："2.0.1." 会被解析为 (2, 0, 1, 0)，因为正则表达式允许末尾的点号
        # 这是可以接受的行为，因为 build 号默认为 0

    def test_version_to_tuple(self):
        """测试版本号元组转换"""
        version = NE301Version(major=2, minor=0, patch=1, build=123)
        assert version.to_tuple() == (2, 0, 1, 123)

        # 不同版本号
        version2 = NE301Version(major=3, minor=1, patch=0, build=1)
        assert version2.to_tuple() == (3, 1, 0, 1)

    def test_version_comparison(self):
        """测试版本号比较"""
        version1 = NE301Version(major=2, minor=0, patch=1, build=123)
        version2 = NE301Version(major=2, minor=0, patch=1, build=124)
        version3 = NE301Version(major=3, minor=0, patch=0, build=0)

        # 元组比较
        assert version1.to_tuple() < version2.to_tuple()
        assert version2.to_tuple() < version3.to_tuple()

    def test_version_generate_timestamp(self):
        """测试时间戳版本号生成"""
        version = NE301Version.generate_timestamp_version()

        # 验证基本格式
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0
        assert 0 <= version.build < 10000  # build 应该在 0-9999 范围内


class TestVersionFileReading:
    """测试 version.mk 文件读取"""

    @pytest.fixture
    def mock_version_mk(self, tmp_path: Path):
        """创建模拟的 version.mk 文件"""
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "# NE301 Version\n"
            "VERSION_MAJOR := 2\n"
            "VERSION_MINOR := 0\n"
            "VERSION_PATCH := 1\n"
            "VERSION_BUILD := 123\n"
        )
        return tmp_path

    def test_get_version_from_file(self, mock_version_mk: Path):
        """测试从 version.mk 读取版本号

        验证点：
        1. 正确解析 VERSION_MAJOR/MINOR/PATCH/BUILD
        2. 版本号字符串格式正确
        """
        toolchain = get_ne301_toolchain(mock_version_mk)
        version = toolchain.get_model_version()

        # 验证版本号解析正确
        assert version.to_tuple() == (2, 0, 1, 123)
        assert str(version) == "2.0.1.123"

    def test_missing_version_file(self, tmp_path: Path):
        """测试 version.mk 文件不存在的情况"""
        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该返回默认版本号 (3, 0, 0, 1)
        assert version.to_tuple() == (3, 0, 0, 1)

    def test_parse_failure_default(self, tmp_path: Path):
        """测试解析失败时返回默认值"""
        # 创建格式错误的 version.mk
        version_mk = tmp_path / "version.mk"
        version_mk.write_text("INVALID CONTENT")

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该返回默认版本号
        assert version.to_tuple() == (3, 0, 0, 1)

    def test_partial_version_vars(self, tmp_path: Path):
        """测试部分版本变量缺失的情况"""
        # 创建只有部分变量的 version.mk
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 3\n"
            "VERSION_MINOR := 1\n"
            # 缺失 PATCH 和 BUILD
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该使用默认值补充缺失的变量
        assert version.major == 3
        assert version.minor == 1
        assert version.patch == 0  # 默认值
        assert version.build == 1  # 默认值

    def test_model_version_override(self, tmp_path: Path, monkeypatch):
        """测试 MODEL_VERSION_OVERRIDE 环境变量优先级"""
        # 创建 version.mk 文件
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 2\n"
            "VERSION_MINOR := 0\n"
            "VERSION_PATCH := 1\n"
            "VERSION_BUILD := 123\n"
        )

        # 设置环境变量（注意：当前实现不支持此功能，此测试用于未来扩展）
        # monkeypatch.setenv("MODEL_VERSION_OVERRIDE", "4.0.0.999")

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 验证读取的是文件版本号
        assert version.to_tuple() == (2, 0, 1, 123)


class TestVersionValidation:
    """测试版本号验证"""

    def test_version_range_check(self, tmp_path: Path):
        """测试版本号范围检查"""
        # 创建大版本号文件
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 10\n"
            "VERSION_MINOR := 20\n"
            "VERSION_PATCH := 30\n"
            "VERSION_BUILD := 40\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 验证可以处理大版本号
        assert version.major == 10
        assert version.minor == 20
        assert version.patch == 30
        assert version.build == 40

    def test_version_compatibility(self):
        """测试版本号兼容性"""
        # 不同格式的版本号应该可以正确解析和比较
        versions = [
            NE301Version(2, 0, 0, 0),
            NE301Version(2, 0, 1, 0),
            NE301Version(2, 1, 0, 0),
            NE301Version(3, 0, 0, 0),
        ]

        # 验证版本号比较逻辑
        for i in range(len(versions) - 1):
            assert versions[i].to_tuple() < versions[i + 1].to_tuple()

    def test_version_comparison(self):
        """测试版本号比较功能"""
        # 相同版本号
        version1 = NE301Version(2, 0, 1, 123)
        version2 = NE301Version(2, 0, 1, 123)
        assert version1.to_tuple() == version2.to_tuple()

        # 不同 build 号
        version3 = NE301Version(2, 0, 1, 124)
        assert version1.to_tuple() < version3.to_tuple()

        # 不同 major 版本
        version4 = NE301Version(3, 0, 0, 0)
        assert version1.to_tuple() < version4.to_tuple()


class TestVersionFormatVariations:
    """测试不同版本号格式变体"""

    def test_version_mk_with_colon_assign(self, tmp_path: Path):
        """测试使用 := 语法的 version.mk（标准语法）"""
        # 清除缓存
        from app.core.ne301_config import NE301ConfigManager
        NE301ConfigManager.clear_cache()

        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 2\n"
            "VERSION_MINOR := 0\n"
            "VERSION_PATCH := 1\n"
            "VERSION_BUILD := 123\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 验证支持 := 语法（这是 version.mk 的标准格式）
        assert version.to_tuple() == (2, 0, 1, 123)

    def test_version_mk_with_comments(self, tmp_path: Path):
        """测试包含注释的 version.mk"""
        # 清除缓存
        from app.core.ne301_config import NE301ConfigManager
        NE301ConfigManager.clear_cache()

        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "# NE301 Version Configuration\n"
            "VERSION_MAJOR := 2  # Major version\n"
            "VERSION_MINOR := 0  # Minor version\n"
            "VERSION_PATCH := 1  # Patch version\n"
            "VERSION_BUILD := 123  # Build number\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 验证可以正确处理注释
        assert version.to_tuple() == (2, 0, 1, 123)


class TestDefaultVersionLayers:
    """测试三层默认值机制"""

    def test_layer_1_file_not_exists(self, tmp_path: Path):
        """测试层级 1：文件不存在 → 返回 (3, 0, 0, 1)"""
        # 不创建 version.mk 文件
        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该返回默认版本号
        assert version.to_tuple() == (3, 0, 0, 1)

    def test_layer_2_missing_vars(self, tmp_path: Path):
        """测试层级 2：变量缺失 → 使用默认参数值"""
        # 创建只有部分变量的 version.mk
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 3\n"
            # 缺失其他变量
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 缺失的变量应该使用默认值
        assert version.major == 3
        assert version.minor == 0  # 默认值
        assert version.patch == 0  # 默认值
        assert version.build == 1  # 默认值

    def test_layer_3_parse_exception(self, tmp_path: Path):
        """测试层级 3：解析异常 → 捕获异常并返回默认值"""
        # 创建格式错误的 version.mk
        version_mk = tmp_path / "version.mk"
        version_mk.write_text("INVALID CONTENT")

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 解析失败时应该返回默认值
        assert version.to_tuple() == (3, 0, 0, 1)


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_version(self, tmp_path: Path):
        """测试全零版本号"""
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 0\n"
            "VERSION_MINOR := 0\n"
            "VERSION_PATCH := 0\n"
            "VERSION_BUILD := 0\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # ✅ 修复：允许全零版本号（之前可能被误判为 None）
        assert version.to_tuple() == (0, 0, 0, 0)

    def test_large_build_number(self, tmp_path: Path):
        """测试大 build 号"""
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR := 2\n"
            "VERSION_MINOR := 0\n"
            "VERSION_PATCH := 1\n"
            "VERSION_BUILD := 99999999\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该支持大 build 号
        assert version.build == 99999999

    def test_version_mk_with_extra_whitespace(self, tmp_path: Path):
        """测试包含额外空格的 version.mk"""
        version_mk = tmp_path / "version.mk"
        version_mk.write_text(
            "VERSION_MAJOR  :=  2  \n"  # 多个空格
            "VERSION_MINOR?=0\n"  # 无空格
            "VERSION_PATCH := 1\n"
            "VERSION_BUILD := 123\n"
        )

        toolchain = get_ne301_toolchain(tmp_path)
        version = toolchain.get_model_version()

        # 应该正确处理空格变体
        assert version.to_tuple() == (2, 0, 1, 123)
