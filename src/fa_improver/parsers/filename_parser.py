"""從檔名提取 FA 報告資訊"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FilenameInfo:
    """從檔名解析出的資訊"""

    date: str = ""  # YYYY/MM/DD
    date_id: str = ""  # YYMMDD(用於 FA 編號)
    customer: str = ""
    project: str = ""
    full_stem: str = ""

    def to_fa_id(self, suffix: str = "001") -> str:
        """產生 FA 編號"""
        if self.date_id:
            return f"FA-{self.date_id}-{suffix}"
        return f"FA-{suffix}"


def parse_filename(path: str | Path) -> FilenameInfo:
    """從檔名解析資訊

    支援格式:
    - 260811_Kobo_ZHT_RA6080_SPcomFailI
    - MS_Meishan_ADO_445239_260716
    - N160JCN-EEK project 1pcs NG sample analysis report 260810

    啟發式:
    - 從尾部掃描 6 位數字作為日期
    - 客戶名:日期之前的倒数第二個部分(跳過可能的公司名縮寫如 MS)
    """
    p = Path(path)
    stem = p.stem

    info = FilenameInfo(full_stem=stem)

    # 切分:只認 _ 與空格,不認 -(因 - 在型號裡常見如 N160JCN-EEK)
    parts = [p for p in re.split(r"[_\s]+", stem) if p]

    # 找出日期(6 位數字)及其索引
    date_idx = -1
    for i in range(len(parts) - 1, -1, -1):
        part = parts[i]
        if part.isdigit() and len(part) == 6:
            info.date_id = part
            info.date = f"20{part[0:2]}/{part[2:4]}/{part[4:6]}"
            date_idx = i
            break

    # 客戶 = 日期之前第二個非空部分(跳過可能是公司縮寫的最前部分)
    non_date_parts = [p for i, p in enumerate(parts) if i != date_idx]
    if len(non_date_parts) >= 2:
        # 如果第一個部分是純大寫縮寫且 < 5 字(如 MS),跳過它
        if re.match(r"^[A-Z]{2,4}$", non_date_parts[0]) and len(non_date_parts) >= 2:
            info.customer = non_date_parts[1]
            info.project = " ".join(non_date_parts[2:])
        else:
            info.customer = non_date_parts[0]
            info.project = " ".join(non_date_parts[1:])
    elif len(non_date_parts) == 1:
        info.customer = non_date_parts[0]

    return info