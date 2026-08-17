"""shuatipass Docker 集成测试（需要本机有 docker）"""
import pytest
import subprocess
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SAMPLE_PDF = PROJECT_DIR / "data" / "input" / "物理-高考真题-学科网.pdf"

docker_available = shutil.which("docker") is not None


@pytest.mark.skipif(not docker_available, reason="docker 未安装")
class TestDocker:
    """Docker 端到端测试 — 需要本机有 docker"""

    def test_docker_version(self):
        """docker 命令可用"""
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Docker version" in result.stdout

    def test_build_image(self, tmp_path):
        """能 build 镜像"""
        try:
            result = subprocess.run(
                ["docker", "build", "-t", "shuatipass:test-pytest", str(PROJECT_DIR)],
                capture_output=True, text=True, timeout=300,
            )
            assert result.returncode == 0, f"build failed:\n{result.stderr}"
        finally:
            subprocess.run(
                ["docker", "rmi", "shuatipass:test-pytest"],
                capture_output=True, text=True,
            )

    def test_help_command(self, tmp_path):
        """docker run shuatipass --help 应正常"""
        # 假设 test_build_image 已运行
        result = subprocess.run(
            ["docker", "run", "--rm", "shuatipass:test-pytest", "--help"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert "shuatipass" in result.stdout
        assert "parse" in result.stdout

    @pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="示例 PDF 不存在")
    def test_end_to_end_parse(self, tmp_path):
        """端到端：build + parse 示例 PDF + 验证 JSON"""
        # 1. build
        subprocess.run(
            ["docker", "build", "-t", "shuatipass:e2e", str(PROJECT_DIR)],
            capture_output=True, text=True, timeout=300,
        )

        # 2. 准备输出目录
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        img_dir = out_dir / "images"
        img_dir.mkdir()

        # 3. 解析
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{SAMPLE_PDF}:/data/input/test.pdf:ro",
                "-v", f"{out_dir}:/data/output",
                "shuatipass:e2e",
                "parse", "/data/input/test.pdf",
                "-o", "/data/output/result.json",
                "--images", "/data/output/images",
            ],
            capture_output=True, text=True, timeout=120,
        )
        # 4. 清理
        subprocess.run(
            ["docker", "rmi", "shuatipass:e2e"],
            capture_output=True, text=True,
        )

        # 5. 验证
        assert result.returncode == 0, f"parse failed:\n{result.stderr}\n{result.stdout}"
        assert (out_dir / "result.json").exists()

        import json
        with open(out_dir / "result.json") as f:
            data = json.load(f)
        total = sum(len(t["questions"]) for t in data["topics"])
        assert total > 500, f"题目数过少: {total}"
        assert data.get("config_name") == "学科网"
