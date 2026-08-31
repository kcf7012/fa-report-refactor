"""PII 個資遮罩模組測試"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fa_improver.llm.redact import (
    RedactionResult,
    RedactionStats,
    is_pii_present,
    redact_pii,
    redact_pii_with_stats,
)


class TestRedactPhone:
    """電話遮罩測試"""

    def test_mask_phone_with_dashes(self):
        """遮罩 0912-345-678 格式"""
        assert redact_pii("電話:0912-345-678") == "電話:0912-***-678"

    def test_mask_phone_without_dashes(self):
        """遮罩 0912345678 格式(無分隔)"""
        assert redact_pii("電話:0912345678") == "電話:0912-***-678"

    def test_mask_phone_with_space(self):
        """遮罩 0912 345 678(空格分隔)"""
        assert redact_pii("電話:0912 345 678") == "電話:0912-***-678"

    def test_mask_multiple_phones(self):
        """多個電話同時遮罩"""
        text = "聯絡人A:0911-111-222 聯絡人B:0922-333-444"
        result = redact_pii(text)
        assert "0911-***-222" in result
        assert "0922-***-444" in result

    def test_no_phone_unchanged(self):
        """無電話不變動"""
        assert redact_pii("這是普通文字") == "這是普通文字"


class TestRedactEmail:
    """Email 遮罩測試"""

    def test_mask_simple_email(self):
        """遮罩簡單 Email"""
        assert redact_pii("Email:zhang@example.com") == "Email:z***@example.com"

    def test_mask_long_local_part(self):
        """遮罩長 local part 的 Email"""
        assert "alice***@company.com" in redact_pii("alice.wang@company.com")

    def test_mask_multiple_emails(self):
        """多個 Email"""
        text = "聯絡:a@x.com b@y.com"
        result = redact_pii(text)
        assert "a***@x.com" in result
        assert "b***@y.com" in result


class TestRedactChineseName:
    """中文姓名遮罩測試"""

    def test_mask_name_before_xiansheng(self):
        """張三先生 → 張*先生"""
        assert redact_pii("張三先生") == "張*先生"

    def test_mask_name_before_xiaojie(self):
        """李小綾小姐 → 李**小姐(3 字名保留首字)"""
        assert redact_pii("李小綾小姐") == "李**小姐"

    def test_mask_name_before_gongchengshi(self):
        """王大明工程師 → 王**工程師(3 字名保留首字)"""
        assert redact_pii("王大明工程師") == "王**工程師"

    def test_no_title_unchanged(self):
        """無稱謂不遮罩(避免誤判)"""
        text = "張三在會議中報告"  # 沒有先生/小姐等稱謂
        assert redact_pii(text) == text


class TestRedactIP:
    """IP 位址遮罩測試"""

    def test_mask_ipv4(self):
        """遮罩 IPv4"""
        assert "192.168.1.***" in redact_pii("Server IP:192.168.1.100")

    def test_mask_multiple_ips(self):
        """多個 IP"""
        text = "10.0.0.1 and 10.0.0.2"
        result = redact_pii(text)
        assert "10.0.0.***" in result


class TestRedactEmployeeId:
    """工號遮罩測試"""

    def test_mask_employee_id_with_dash(self):
        """EMP-12345"""
        assert "EMP***" in redact_pii("工號:EMP-12345")

    def test_mask_employee_id_without_dash(self):
        """EMP12345"""
        assert "EMP***" in redact_pii("工號:EMP12345")


class TestRedactIDNumber:
    """身分證字號遮罩測試"""

    def test_mask_id_number(self):
        """A123456789 → A1***"""
        assert "A1***" in redact_pii("身分證:A123456789")


class TestRedactCreditCard:
    """信用卡遮罩測試"""

    def test_mask_credit_card_with_spaces(self):
        """遮罩 4111 1111 1111 1111"""
        assert "**** **** **** 1111" in redact_pii("卡號:4111 1111 1111 1111")

    def test_mask_credit_card_with_dashes(self):
        """遮罩 4111-1111-1111-1111"""
        assert "**** **** **** 1111" in redact_pii("卡號:4111-1111-1111-1111")


class TestRedactCombined:
    """多種個資混合測試"""

    def test_mixed_pii_in_one_string(self):
        """電話 + Email + 姓名同時存在"""
        text = "聯絡人:張三 先生 電話:0912-345-678 Email:zhang@example.com"
        result = redact_pii(text)
        assert "張*先生" in result
        assert "0912-***-678" in result
        assert "z***@example.com" in result

    def test_clean_text_unchanged(self):
        """完全無個資的文字不變"""
        text = "FA 報告分析結論:良率偏低需改善製程參數"
        assert redact_pii(text) == text


class TestRedactWithStats:
    """遮罩統計測試"""

    def test_stats_basic(self):
        """統計基本欄位"""
        text = "電話:0912-345-678 Email:a@b.com"
        result = redact_pii_with_stats(text)
        assert isinstance(result, RedactionResult)
        assert result.stats.phones == 1
        assert result.stats.emails == 1
        assert result.stats.total == 2

    def test_stats_multiple_types(self):
        """多種個資統計"""
        text = """
        張三先生 0911-222-333 alice@x.com 192.168.1.1 EMP-12345
        """
        result = redact_pii_with_stats(text)
        assert result.stats.chinese_names >= 1
        assert result.stats.phones >= 1
        assert result.stats.emails >= 1
        assert result.stats.ips >= 1
        assert result.stats.employee_ids >= 1
        assert result.stats.total >= 5

    def test_stats_empty_text(self):
        """空字串統計為 0"""
        result = redact_pii_with_stats("")
        assert result.text == ""
        assert result.stats.total == 0

    def test_stats_no_pii(self):
        """無個資統計為 0"""
        result = redact_pii_with_stats("無個資的純文字")
        assert result.stats.total == 0

    def test_stats_addition(self):
        """RedactionStats 累加"""
        s1 = RedactionStats(phones=1, emails=2)
        s2 = RedactionStats(phones=3, emails=1, chinese_names=2)
        s1.add(s2)
        assert s1.phones == 4
        assert s1.emails == 3
        assert s1.chinese_names == 2


class TestIsPIIPresent:
    """PII 偵測測試"""

    def test_phone_detected(self):
        assert is_pii_present("電話 0912-345-678") is True

    def test_email_detected(self):
        assert is_pii_present("聯絡 a@b.com") is True

    def test_chinese_name_detected(self):
        assert is_pii_present("張三先生") is True

    def test_ip_detected(self):
        assert is_pii_present("Server: 192.168.1.1") is True

    def test_clean_text_not_detected(self):
        assert is_pii_present("良率偏低,需改善") is False

    def test_empty_not_detected(self):
        assert is_pii_present("") is False


class TestOpenAIClientRedactionIntegration:
    """OpenAI client 整合遮罩測試"""

    @patch("openai.OpenAI")
    def test_redact_disabled_by_default(self, mock_openai_class):
        """預設不遮罩(向後相容)"""
        mock_response = MagicMock()
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        from fa_improver.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="sk-test")
        assert client.redact_pii_before_send is False

        # 送出含電話的 user prompt
        client.complete("sys", "聯絡人:0912-345-678")

        # 應原封不動送出
        call_args = mock_client_instance.chat.completions.create.call_args
        assert "0912-345-678" in str(call_args)

    @patch("openai.OpenAI")
    def test_redact_enabled_masks_pii(self, mock_openai_class):
        """啟用遮罩後自動遮罩"""
        mock_response = MagicMock()
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        from fa_improver.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="sk-test", redact_pii_before_send=True)
        client.complete("sys prompt", "聯絡人:張三先生 0912-345-678")

        call_args = mock_client_instance.chat.completions.create.call_args
        sent_str = str(call_args)
        # 應已遮罩
        assert "張*先生" in sent_str
        assert "0912-***-678" in sent_str
        # 統計應累加
        assert client.total_redactions >= 2

    @patch("openai.OpenAI")
    def test_reset_stats_includes_redactions(self, mock_openai_class):
        """reset_stats 也會重置 total_redactions"""
        from fa_improver.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="sk-test", redact_pii_before_send=True)
        client.total_redactions = 5
        client.reset_stats()
        assert client.total_redactions == 0
