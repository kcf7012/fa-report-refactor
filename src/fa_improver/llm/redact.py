"""PII(個資)遮罩模組

在半導體 FA 報告中,常含有工程師姓名、電話、Email 等個資。
在送給 LLM(OpenAI 等外部 API)評估前,應自動遮罩這些敏感資料。

支援遮罩:
- 電話號碼(台灣手機 09xx-xxx-xxx、09xxxxxxxx)
- Email(user@example.com)
- 中文姓名(2-4 字常見姓名)
- IP 位址(IPv4)
- 工號(EMP-xxxxx / EMPxxxxx)
- 身分證字號(台灣格式)
- 信用卡號(16 碼)

使用方式:
    >>> from fa_improver.llm.redact import redact_pii
    >>> redact_pii("聯絡人:張三 電話:0912-345-678 Email:zhang@example.com")
    '聯絡人:張* 電話:0912-***-*** Email:z***@example.com'
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RedactionStats:
    """遮罩統計資料"""

    phones: int = 0
    emails: int = 0
    chinese_names: int = 0
    ips: int = 0
    employee_ids: int = 0
    id_numbers: int = 0
    credit_cards: int = 0
    total: int = 0

    def add(self, other: RedactionStats) -> None:
        """累加遮罩統計"""
        self.phones += other.phones
        self.emails += other.emails
        self.chinese_names += other.chinese_names
        self.ips += other.ips
        self.employee_ids += other.employee_ids
        self.id_numbers += other.id_numbers
        self.credit_cards += other.credit_cards
        self.total += other.total


@dataclass
class RedactionResult:
    """遮罩結果"""

    text: str
    stats: RedactionStats = field(default_factory=RedactionStats)


# ============= 遮罩規則 =============

# 台灣手機:09xx-xxx-xxx 或 09xxxxxxxx(10 碼)
_PHONE_PATTERN = re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}")

# Email
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# IPv4 位址
_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# 工號:EMP-12345 或 EMP12345
_EMP_ID_PATTERN = re.compile(r"\bEMP[-\s]?\d{4,8}\b", re.IGNORECASE)

# 台灣身分證字號:1 個英文字母 + 1 或 2(性別) + 8 碼數字
_ID_NUMBER_PATTERN = re.compile(r"\b[A-Z][12]\d{8}\b")

# 信用卡:13-19 碼數字(每 4 碼一組,可含空格或橫線)
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[\s-]?){3,4}\d{1,4}\b")

# 中文姓名:2-4 個中文字,後面接「先生/小姐/經理/工程師/課長/部長/主任」
# 中間可有空白(中英文之間),限制在職務稱謂前後以降低誤判
_CHINESE_NAME_PATTERN = re.compile(
    r"([\u4e00-\u9fff]{2,4})[\s　]*(?=(?:先生|小姐|經理|工程師|課長|部長|主任|協理|副理|博士))"
)


# ============= 遮罩函式 =============


def _mask_phone(match: re.Match) -> str:
    """遮罩電話:保留前 4 碼(09xx),中間 3 碼變 ***,保留後 3 碼"""
    phone = match.group(0)
    digits = re.sub(r"[^0-9]", "", phone)

    if len(digits) == 10 and digits.startswith("09"):
        return f"{digits[:4]}-***-{digits[-3:]}"
    # fallback:保留前 2 碼,其餘變 *
    return digits[:2] + "*" * (len(digits) - 2)


def _mask_email(match: re.Match) -> str:
    """遮罩 Email:保留第 1 個字母 + *** @ domain"""
    email = match.group(0)
    if "@" not in email:
        return "*" * len(email)
    local, domain = email.split("@", 1)
    if not local:
        return "*" * len(email)
    # 若 local part 包含「.」,保留到第一個點(如 alice.wang → alice***)
    if "." in local:
        head = local.split(".", 1)[0]
        return f"{head}***@{domain}"
    return f"{local[0]}***@{domain}"


def _mask_ip(match: re.Match) -> str:
    """遮罩 IP:前三碼 xxx,最後一段變 ***"""
    ip = match.group(0)
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "***"


def _mask_employee_id(match: re.Match) -> str:
    """遮罩工號:保留前 3 碼,後面變 ***"""
    emp_id = match.group(0)
    return emp_id[:3] + "***"


def _mask_id_number(match: re.Match) -> str:
    """遮罩身分證字號:保留前 2 碼,後面變 ***"""
    id_num = match.group(0)
    return id_num[:2] + "***"


def _mask_credit_card(match: re.Match) -> str:
    """遮罩信用卡:只保留最後 4 碼"""
    cc = match.group(0)
    digits = re.sub(r"[^0-9]", "", cc)
    if len(digits) >= 13:
        return "**** **** **** " + digits[-4:]
    return "*" * len(cc)


def _mask_chinese_name(match: re.Match) -> str:
    """遮罩中文姓名:保留姓(第 1 字),後面變 *"""
    name = match.group(1)
    return name[0] + "*" * (len(name) - 1)


# ============= 公開 API =============


def redact_pii(text: str) -> str:
    """遮罩文字中的個資(PII),回傳遮罩後的字串

    Args:
        text: 原始文字

    Returns:
        遮罩後的字串

    Example:
        >>> redact_pii("聯絡人:張三 電話:0912-345-678")
        '聯絡人:張* 電話:0912-***-***'
    """
    result = redact_pii_with_stats(text)
    return result.text


def redact_pii_with_stats(text: str) -> RedactionResult:
    """遮罩個資並回傳統計資料

    Args:
        text: 原始文字

    Returns:
        RedactionResult 包含遮罩後文字與各類型遮罩次數
    """
    stats = RedactionStats()
    redacted = text

    # 電話
    redacted, n = _PHONE_PATTERN.subn(_mask_phone, redacted)
    stats.phones = n

    # Email
    redacted, n = _EMAIL_PATTERN.subn(_mask_email, redacted)
    stats.emails = n

    # IP 位址
    redacted, n = _IP_PATTERN.subn(_mask_ip, redacted)
    stats.ips = n

    # 工號
    redacted, n = _EMP_ID_PATTERN.subn(_mask_employee_id, redacted)
    stats.employee_ids = n

    # 身分證字號
    redacted, n = _ID_NUMBER_PATTERN.subn(_mask_id_number, redacted)
    stats.id_numbers = n

    # 信用卡
    redacted, n = _CREDIT_CARD_PATTERN.subn(_mask_credit_card, redacted)
    stats.credit_cards = n

    # 中文姓名(放最後,避免遮罩後的字串影響其他規則)
    redacted, n = _CHINESE_NAME_PATTERN.subn(_mask_chinese_name, redacted)
    stats.chinese_names = n

    stats.total = (
        stats.phones
        + stats.emails
        + stats.ips
        + stats.employee_ids
        + stats.id_numbers
        + stats.credit_cards
        + stats.chinese_names
    )

    return RedactionResult(text=redacted, stats=stats)


def is_pii_present(text: str) -> bool:
    """快速檢查文字是否含有個資(無需完整遮罩)

    Args:
        text: 原始文字

    Returns:
        True 若包含任何已知的 PII 模式
    """
    patterns = [
        _PHONE_PATTERN,
        _EMAIL_PATTERN,
        _IP_PATTERN,
        _EMP_ID_PATTERN,
        _ID_NUMBER_PATTERN,
        _CREDIT_CARD_PATTERN,
        _CHINESE_NAME_PATTERN,
    ]
    return any(p.search(text) for p in patterns)
