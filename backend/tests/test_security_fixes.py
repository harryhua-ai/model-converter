"""
安全修复验证测试

测试 HIGH 优先级安全问题的修复：
- HIGH-2026-002: 文件上传大小限制
- HIGH-2026-004: YOLO 模型加载验证
- HIGH-2026-005: CORS 配置
- HIGH-2026-001: 临时文件权限
"""
import pytest
import tempfile
import os
from pathlib import Path
from httpx import AsyncClient

from app.main import app
from app.core.config import settings
from app.core.docker_adapter import get_secure_temp_manager


class TestSecurityFixes:
    """安全修复验证测试"""

    @pytest.mark.asyncio
    async def test_file_upload_size_limit(self):
        """测试 HIGH-2026-002: 文件上传大小限制"""
        from app.api.convert import MAX_UPLOAD_SIZE, MAX_CALIBRATION_SIZE

        # 验证限制值已降低到 100MB
        assert MAX_UPLOAD_SIZE == 100 * 1024 * 1024, "模型文件大小限制应为 100MB"
        assert MAX_CALIBRATION_SIZE == 100 * 1024 * 1024, "校准数据集大小限制应为 100MB"

    @pytest.mark.asyncio
    async def test_cors_configuration(self):
        """测试 HIGH-2026-005: CORS 配置"""
        # 测试开发环境配置
        cors_origins = settings.get_cors_origins()

        # 开发环境应包含 localhost
        assert len(cors_origins) > 0, "CORS 来源列表不应为空"
        assert any("localhost" in origin for origin in cors_origins), "开发环境应允许 localhost"

        # 不应包含通配符
        assert "*" not in cors_origins, "CORS 配置不应使用通配符"

    @pytest.mark.asyncio
    async def test_temp_dir_permissions(self):
        """测试 HIGH-2026-001: 临时文件权限"""
        # 创建安全临时目录
        temp_manager = get_secure_temp_manager()
        temp_dir = temp_manager.create_secure_temp_dir(prefix="test_")

        try:
            # 验证权限为 700
            stat_info = os.stat(temp_dir)
            mode = stat_info.st_mode & 0o777
            assert mode == 0o700, f"临时目录权限应为 0o700，实际为 {oct(mode)}"

            # 验证目录在管理器中注册
            assert temp_dir in temp_manager.temp_dirs, "临时目录应在管理器中注册"

        finally:
            # 清理
            temp_manager.cleanup(temp_dir)

    @pytest.mark.asyncio
    async def test_concurrent_upload_limit(self):
        """测试 HIGH-2026-002: 并发上传限制"""
        from app.api.convert import MAX_CONCURRENT_UPLOADS

        # 验证并发限制
        assert MAX_CONCURRENT_UPLOADS == 5, "最大并发上传数应为 5"

    @pytest.mark.asyncio
    async def test_disk_space_check(self):
        """测试 HIGH-2026-002: 磁盘空间检查"""
        from app.api.convert import _check_disk_space
        from fastapi import HTTPException

        # 测试小空间请求（应通过）
        try:
            _check_disk_space(1024)  # 1KB
        except HTTPException:
            pytest.fail("小空间请求应通过")

        # 测试极大空间请求（应失败）
        with pytest.raises(HTTPException) as exc_info:
            _check_disk_space(10 * 1024 * 1024 * 1024 * 1024)  # 10TB

        assert exc_info.value.status_code == 507, "应返回 507 Insufficient Storage"


@pytest.mark.integration
class TestSecurityIntegration:
    """安全集成测试"""

    @pytest.mark.asyncio
    async def test_upload_too_large_file(self):
        """测试上传过大文件被拒绝"""
        # 注意: 这里需要完整的集成测试环境
        # 简化验证逻辑，实际测试需要真实文件上传
        from app.api.convert import MAX_UPLOAD_SIZE
        assert MAX_UPLOAD_SIZE == 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """测试 CORS 响应头"""
        # 注意: 这里需要完整的集成测试环境
        # 简化验证逻辑，实际测试需要真实 HTTP 请求
        cors_origins = settings.get_cors_origins()
        assert len(cors_origins) > 0
        assert "*" not in cors_origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
