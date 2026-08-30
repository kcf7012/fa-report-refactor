"""檔名解析器測試"""

from pathlib import Path

from fa_improver.parsers.filename_parser import parse_filename


class TestFilenameParser:
    """檔名解析測試"""

    def test_kobo_format(self):
        """Kobo 報告格式"""
        info = parse_filename(Path("260811_Kobo_ZHT_RA6080_SPcomFailI.pptx"))
        assert info.date_id == "260811"
        assert info.date == "2026/08/11"
        assert info.customer == "Kobo"
        assert info.project == "ZHT RA6080 SPcomFailI"
        assert info.to_fa_id() == "FA-260811-001"

    def test_meishan_format(self):
        """MS Meishan 報告格式"""
        info = parse_filename(Path("MS_Meishan_ADO_445239_260716.pptx"))
        assert info.date_id == "260716"
        assert info.date == "2026/07/16"
        assert info.customer == "Meishan"
        assert info.project == "ADO 445239"  # 不含日期本身

    def test_n160jcn_format(self):
        """N160JCN-EEK 報告格式"""
        info = parse_filename(
            Path("N160JCN-EEK project 1pcs NG sample analysis report 260810.pptx")
        )
        assert info.date_id == "260810"
        assert info.customer == "N160JCN-EEK"  # - 不作分隔
        assert "project" in info.project.lower()

    def test_fa_id_generation(self):
        """FA 編號生成"""
        info = parse_filename(Path("test_260811.pptx"))
        assert info.to_fa_id() == "FA-260811-001"
        assert info.to_fa_id("042") == "FA-260811-042"

    def test_no_date_in_filename(self):
        """無日期的檔名"""
        info = parse_filename(Path("report.pptx"))
        assert info.date_id == ""
        assert info.date == ""
        assert info.customer == "report"
