"""PPT (.ppt) 到 PPTX (.pptx) 轉換工具測試

覆蓋情境:
1. .pptx 輸入直通
2. 副檔名判斷邏輯
3. LibreOffice 不可用時的失敗處理
4. cleanup 機制
5. 不支援的副檔名處理
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fa_improver.utils.ppt_converter import PPTConverter


class TestConvertIfNeeded:
    """測試 convert_if_needed:副檔名判斷與路徑處理"""

    def test_pptx_input_returns_same_path(self, tmp_path: Path):
        """給 .pptx 應該直接返回原路徑,不呼叫 LibreOffice"""
        pptx = tmp_path / "report.pptx"
        pptx.write_bytes(b"fake pptx content")

        converter = PPTConverter()
        result = converter.convert_if_needed(pptx)

        assert result == pptx
        assert converter.temp_files == []  # 沒產生 temp 檔

    def test_ppt_extension_recognized(self, tmp_path: Path):
        """給 .ppt 應該嘗試轉換(會失敗,因 fake 檔)"""
        ppt = tmp_path / "report.ppt"
        ppt.write_bytes(b"fake ppt content")

        converter = PPTConverter()

        # 模擬 LibreOffice 不可用
        with patch.object(converter, "_try_libreoffice", return_value=None):
            result = converter.convert_if_needed(ppt)

        # 轉換失敗應該回 None(不是 raise)
        assert result is None

    def test_uppercase_extension_normalized(self, tmp_path: Path):
        """副檔名大小寫不敏感:.PPTX 應視為 pptx"""
        pptx = tmp_path / "REPORT.PPTX"
        pptx.write_bytes(b"fake content")

        converter = PPTConverter()
        result = converter.convert_if_needed(pptx)

        assert result == pptx
        assert converter.temp_files == []

    def test_unknown_extension_passes_through(self, tmp_path: Path):
        """未知副檔名(如 .docx)直接返回原路徑(交給上層處理)"""
        docx = tmp_path / "report.docx"
        docx.write_bytes(b"fake")

        converter = PPTConverter()
        result = converter.convert_if_needed(docx)

        assert result == docx


class TestConvertPptToPptx:
    """測試 convert_ppt_to_pptx:LibreOffice 整合"""

    def test_returns_none_when_libreoffice_unavailable(self, tmp_path: Path):
        """LibreOffice 不可用時,return None(而非 raise)"""
        ppt = tmp_path / "report.ppt"
        ppt.write_bytes(b"fake")

        converter = PPTConverter()
        with (
            patch.object(converter, "_try_libreoffice", return_value=None),
            patch("fa_improver.utils.ppt_converter.sys.platform", "linux"),
        ):
            result = converter.convert_ppt_to_pptx(ppt)

        assert result is None

    def test_returns_converted_path_when_libreoffice_succeeds(self, tmp_path: Path):
        """LibreOffice 成功時,回傳轉換後的 .pptx 路徑並加入 temp_files"""
        ppt = tmp_path / "report.ppt"
        pptx = tmp_path / "report.pptx"
        ppt.write_bytes(b"fake ppt")
        pptx.write_bytes(b"converted pptx")

        converter = PPTConverter()
        with patch.object(converter, "_try_libreoffice", return_value=pptx):
            result = converter.convert_ppt_to_pptx(ppt)

        assert result == pptx
        assert pptx in converter.temp_files


class TestTryLibreOffice:
    """測試 _try_libreoffice:指令執行細節"""

    def test_returns_none_when_no_libreoffice_installed(self, tmp_path: Path):
        """所有 LibreOffice 路徑都不存在時,return None"""
        ppt = tmp_path / "report.ppt"

        converter = PPTConverter()

        # 模擬所有指令都 FileNotFoundError
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = converter._try_libreoffice(ppt)

        assert result is None

    def test_returns_none_on_timeout(self, tmp_path: Path):
        """subprocess timeout 時,return None"""
        import subprocess

        ppt = tmp_path / "report.ppt"

        converter = PPTConverter()

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="libreoffice", timeout=3),
        ):
            result = converter._try_libreoffice(ppt)

        assert result is None

    def test_skips_paths_with_nonzero_exit_code(self, tmp_path: Path):
        """非零退出碼的 libreoffice 路徑會被跳過"""
        ppt = tmp_path / "report.ppt"

        converter = PPTConverter()

        # 模擬 --version 回傳非 0
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"error"

        with patch("subprocess.run", return_value=mock_result):
            result = converter._try_libreoffice(ppt)

        assert result is None


class TestCleanup:
    """測試 cleanup:臨時檔清理"""

    def test_removes_tracked_temp_files(self, tmp_path: Path):
        """tracked temp_files 應被刪除"""
        temp = tmp_path / "temp.pptx"
        temp.write_bytes(b"to be deleted")

        converter = PPTConverter()
        converter.temp_files.append(temp)
        converter.cleanup()

        assert not temp.exists()

    def test_silently_skips_missing_files(self, tmp_path: Path):
        """temp_files 已被外部刪除時,不應 raise"""
        temp = tmp_path / "gone.pptx"
        # 不建立檔案

        converter = PPTConverter()
        converter.temp_files.append(temp)
        converter.cleanup()  # 不應 raise

    def test_handles_permission_errors_gracefully(self, tmp_path: Path):
        """刪除權限不足時,不應 raise"""
        temp = tmp_path / "locked.pptx"
        temp.write_bytes(b"content")

        converter = PPTConverter()
        converter.temp_files.append(temp)

        with patch.object(Path, "unlink", side_effect=PermissionError):
            converter.cleanup()  # 不應 raise

    def test_empty_temp_files_is_noop(self):
        """沒有 temp_files 時,cleanup 是 no-op"""
        converter = PPTConverter()
        converter.cleanup()  # 不應 raise

        assert converter.temp_files == []
