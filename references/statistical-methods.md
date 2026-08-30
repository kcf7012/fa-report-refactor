# Statistical Validation Methods for FA

## t-Test for Independent Samples

**Use Case**: Compare means between normal vs failed samples

**Requirements**:
- Two independent groups (n ≥ 3, ideally n ≥ 5)
- Continuous data
- Approximately normal distribution

**Implementation**:
```python
from scipy import stats
t_statistic, p_value = stats.ttest_ind(normal_group, failed_group)
```

**Interpretation**:
- p < 0.01: Highly significant
- p < 0.05: Significant
- p ≥ 0.05: No significant difference

## Confidence Intervals

**95% CI Formula**:
```
CI = x̄ ± (t_critical × SE)
where SE = s / √n
```

**Example**: Mean difference = 304 ± 150 → CI [154, 454]

## Reporting Format

"DVT normal samples (M=1548, SD=150) vs PVT failed (M=1852, SD=200), t(8)=3.24, p<0.01, 95% CI [154, 454]"

## Template Text

"Statistical analysis confirms significant difference. t-test shows failed samples had significantly higher [parameter] (p < [value]), providing strong evidence for [root cause]."

---
**版本**: 2.1.2  
**最後更新**: 2026-01-28

