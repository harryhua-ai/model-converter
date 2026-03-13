# backend/tests/test_docker_adapter.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
from app.core.docker_adapter import DockerToolChainAdapter

@pytest.mark.unit
def test_check_docker():
    """测试 Docker 检测"""
    adapter = DockerToolChainAdapter()
    available, error = adapter.check_docker()
    # 需要安装 docker 才能测试
    assert isinstance(available, bool)
    assert isinstance(error, str)

@pytest.mark.unit
def test_check_image():
    """测试镜像检查"""
    adapter = DockerToolChainAdapter()
    result = adapter.check_image()
    assert isinstance(result, bool)

@pytest.mark.unit
def test_pull_image_no_callback():
    """测试拉取镜像（无回调）"""
    adapter = DockerToolChainAdapter()
    # Skip if Docker not available
    available, _ = adapter.check_docker()
    if not available:
        pytest.skip("Docker not available")

    # This test would actually pull the image, so we might want to skip it
    # or mock it in actual CI/CD
    # For now, just verify the method exists
    assert hasattr(adapter, 'pull_image')

@pytest.mark.unit
def test_convert_model():
    """测试模型转换（使用 mock）"""
    from pathlib import Path
    from unittest.mock import patch, MagicMock
    import tempfile

    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    # Mock container run
    adapter.client.containers.run.return_value = b"Conversion successful"

    # 创建临时模型文件
    with tempfile.NamedTemporaryFile(suffix=".tflite", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'parent', MagicMock(resolve=MagicMock(return_value=Path("/tmp")))):
                with patch.object(Path, 'absolute', MagicMock(return_value=Path("/tmp/outputs"))):
                    with patch("builtins.open", MagicMock()):
                        result = adapter.convert_model(
                            task_id="test-123",
                            model_path=tmp_path,
                            config={
                                "input_size": [640, 640],
                                "num_classes": 80,
                                "model_type": "yolov8",
                                "quantization": "int8"
                            }
                        )

        assert "ne301_model_test-123.bin" in result
        adapter.client.containers.run.assert_called_once()
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

@pytest.mark.unit
def test_convert_model_no_docker():
    """测试无 Docker 时的错误处理"""
    adapter = DockerToolChainAdapter()
    adapter.client = None

    with pytest.raises(RuntimeError, match="Docker client not available"):
        adapter.convert_model("test", "/tmp/test.tflite", {})

@pytest.mark.unit
def test_prepare_ne301_project():
    """测试 NE301 项目准备（新实现 - 使用 generate_ne301_json_config）"""
    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    config = {
        "input_size": 640,
        "num_classes": 80,
        "model_type": "yolov8"
    }

    # 创建临时 TFLite 文件
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.tflite') as tflite_file:
        tflite_file.write(b'\x00' * 10240)  # 10KB
        tflite_file.flush()

        # 调用新方法
        with patch('shutil.copy2'):
            with patch.object(Path, 'mkdir'):
                with patch('builtins.open', create=True):
                    result = adapter._prepare_ne301_project(
                        task_id="test-123",
                        quantized_tflite=tflite_file.name,
                        config=config,
                        yaml_path=None
                    )

    # 验证结果
    assert result is not None
    assert result.exists()


@pytest.mark.unit
def test_prepare_ne301_project_defaults():
    """测试 NE301 项目准备使用默认值"""
    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    config = {
        "input_size": 480,
        "num_classes": 10,
        "model_type": "yolov8"
    }

    # 创建临时 TFLite 文件
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.tflite') as tflite_file:
        tflite_file.write(b'\x00' * 5120)  # 5KB
        tflite_file.flush()

        # 调用新方法
        with patch('shutil.copy2'):
            with patch.object(Path, 'mkdir'):
                with patch('builtins.open', create=True):
                    result = adapter._prepare_ne301_project(
                        task_id="test-456",
                        quantized_tflite=tflite_file.name,
                        config=config,
                        yaml_path=None
                    )

    # 验证结果
    assert result is not None

# ============================================================
# 新增：_get_host_path 方法的单元测试（4级回退机制）
# ============================================================

@pytest.mark.unit
def test_get_host_path_docker_inspect():
    """测试优先级 1: docker inspect 获取宿主机路径"""
    adapter = DockerToolChainAdapter()

    mock_mounts = [
        {
            "Destination": "/workspace/ne301",
            "Source": "/host/path/ne301",
            "Type": "bind"
        },
        {
            "Destination": "/app/uploads",
            "Source": "/host/path/uploads",
            "Type": "bind"
        }
    ]

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_mounts)
        )

        result = adapter._get_host_path(Path("/workspace/ne301"))

        assert result == "/host/path/ne301"
        mock_run.assert_called_once()

@pytest.mark.unit
def test_get_host_path_inference_from_other_mounts():
    """测试优先级 2: 从其他挂载点推断宿主机路径"""
    adapter = DockerToolChainAdapter()

    mock_mounts = [
        {
            "Destination": "/app/uploads",
            "Source": "/host/project/uploads",
            "Type": "bind"
        }
    ]

    # Mock docker inspect 返回挂载信息
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_mounts)
        )

        # Mock 推断的路径存在
        # Path("/host/project/uploads").parent.parent = Path("/host")
        # Path("/host") / "ne301" = Path("/host/ne301")
        with patch("pathlib.Path.exists", return_value=True):
            result = adapter._get_host_path(Path("/workspace/ne301"))

        # 从 /host/project/uploads 推断：parent.parent 是 /host
        # 因此 ne301 路径应为 /host/ne301
        assert result == "/host/ne301"

@pytest.mark.unit
def test_get_host_path_from_proc_mounts():
    """测试优先级 3: 从 /proc/mounts 读取宿主机路径"""
    adapter = DockerToolChainAdapter()

    # Mock docker inspect 失败
    with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
        # Mock /proc/mounts 内容
        mock_mounts_content = "/host/path/ne301 /workspace/ne301 ext4 rw 0 0\n"

        # 创建 mock file object
        mock_file = MagicMock()
        mock_file.__enter__ = lambda self: self
        mock_file.__exit__ = lambda self, *args: None
        mock_file.__iter__ = lambda self: iter(mock_mounts_content.strip().split("\n"))

        with patch("builtins.open", return_value=mock_file):
            result = adapter._get_host_path(Path("/workspace/ne301"))

            # 从 /proc/mounts 读取第一列（宿主机路径）
            # "/host/path/ne301 /workspace/ne301 ..." → parts[0] = "/host/path/ne301"
            assert result == "/host/path/ne301"

@pytest.mark.unit
def test_get_host_path_from_env_var():
    """测试优先级 4: 从环境变量获取宿主机路径"""
    adapter = DockerToolChainAdapter()

    # Mock 所有其他方法失败
    with patch("subprocess.run", return_value=MagicMock(returncode=1)):
        with patch.dict("os.environ", {"NE301_HOST_PATH": "/env/var/ne301"}):
            result = adapter._get_host_path(Path("/workspace/ne301"))

            assert result == "/env/var/ne301"

@pytest.mark.unit
def test_get_host_path_all_methods_fail():
    """测试所有方法都失败时返回 None"""
    adapter = DockerToolChainAdapter()

    # Mock 所有方法都失败
    with patch("subprocess.run", return_value=MagicMock(returncode=1)):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch.dict("os.environ", {}, clear=True):
                result = adapter._get_host_path(Path("/workspace/ne301"))

                assert result is None

@pytest.mark.unit
def test_get_host_path_docker_inspect_exception():
    """测试 docker inspect 抛出异常时的处理"""
    adapter = DockerToolChainAdapter()

    with patch("subprocess.run", side_effect=Exception("Docker not available")):
        # 应该捕获异常并继续尝试其他方法
        # 这里测试至少不会崩溃
        try:
            result = adapter._get_host_path(Path("/workspace/ne301"))
            # 结果可能是 None 或从其他方法获取的路径
            assert result is None or isinstance(result, str)
        except Exception as e:
            pytest.fail(f"get_host_path 应该处理异常，但抛出了: {e}")

@pytest.mark.unit
def test_build_ne301_model_without_host_path():
    """测试无法获取宿主机路径时抛出错误"""
    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    # Mock _get_host_path 返回 None
    with patch.object(adapter, "_get_host_path", return_value=None):
        with pytest.raises(RuntimeError, match="无法获取宿主机路径"):
            adapter._build_ne301_model(
                task_id="test-123",
                ne301_project_path=Path("/workspace/ne301"),
                quantized_tflite="/tmp/test.tflite"
            )

@pytest.mark.unit
def test_build_ne301_model_with_host_path():
    """测试成功获取宿主机路径时执行 Docker 命令"""
    adapter = DockerToolChainAdapter()
    adapter.client = Mock()
    adapter.ne301_image = "camthink/ne301-dev:latest"

    mock_host_path = "/host/path/ne301"

    # Mock _get_host_path 返回宿主机路径
    with patch.object(adapter, "_get_host_path", return_value=mock_host_path):
        # Mock subprocess.run（Docker 命令执行）
        with patch("subprocess.Popen") as mock_popen:
            # Mock 进程成功执行
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_process.returncode = 0

            # Mock stdout 返回成功日志
            mock_process.stdout = iter([
                "✓ Starting NE301 build...",
                "✓ Package created"
            ])

            mock_popen.return_value = mock_process

            # Mock .bin 文件生成
            bin_file = MagicMock()
            bin_file.exists.return_value = True

            with patch.object(Path, "glob", return_value=[bin_file]):
                with patch("shutil.copy2"):
                    with patch.object(Path, "mkdir"):  # Mock mkdir
                        result = adapter._build_ne301_model(
                            task_id="test-123",
                            ne301_project_path=Path("/workspace/ne301"),
                            quantized_tflite="/tmp/test.tflite"
                        )

                        # 验证返回结果
                        assert result is not None
                        assert "ne301_model_test-123.bin" in str(result)

                        # 验证 Docker 命令使用了宿主机路径
                        call_args = mock_popen.call_args
                        cmd = call_args[0][0]  # 获取命令列表
                        assert mock_host_path in " ".join(cmd)
            assert "-v" in cmd
            mount_index = cmd.index("-v") + 1
            assert cmd[mount_index].startswith(mock_host_path)
