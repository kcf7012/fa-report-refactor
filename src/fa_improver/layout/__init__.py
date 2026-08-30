"""版面處理:layout 選擇、placeholder 調整、母片保護"""

from .protector import MasterProtector, MasterSnapshot
from .selector import find_content_layout

__all__ = ["MasterProtector", "MasterSnapshot", "find_content_layout"]