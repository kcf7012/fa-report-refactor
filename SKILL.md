---
name: fa-report-improvement
description: Improve semiconductor failure analysis (FA) reports based on professional 8D evaluation criteria. Supports both .ppt and .pptx formats with automatic conversion. Features dynamic content injection from LLM evaluations, multi-format JSON compatibility, and closed-loop execution manifests.
version: 2.3.0
entrypoint: scripts/improve_fa_report.py
inputs:
  - id: report
    label: FA 報告 (.ppt/pptx)
    type: file
    accept: .ppt,.pptx
    icon: 📊
  - id: evaluation_json
    label: 評核 JSON (.json)
    type: file
    accept: .json
    icon: 📜
  - id: prompt
    label: 優化提示詞 (選填)
    type: text
    placeholder: 例如：特別加強根因分析部分的統計數據性，或指定改善對策的具體方向...
    optional: true
---

# FA Report Improvement

## Overview

Comprehensive improvement system for semiconductor FA reports with automatic .ppt to .pptx conversion support.

**Key Features:**
- ✅ **Multi-Format JSON (v2.3.0)**: Supports both `dimensions` (flat) and `dimension_scores` (nested object) formats for maximum compatibility.
- ✅ **Object Array Improvements (v2.3.0)**: Handles `improvements` as either string array or object array (`{priority, item, suggestion}`).
- ✅ **Dynamic Injection (v2.2.0)**: Real-time extraction of improvement suggestions from evaluation JSON.
- ✅ **Success Manifest (v2.2.0)**: Automated generation of `_manifest.json` for LLM verification.

## Quick Start

When user provides FA report (**.ppt or .pptx**) for improvement:

1. **Auto-detect format** - Automatically converts .ppt if needed
2. **Analyze evaluation** - Parse JSON or text feedback
3. **Apply improvements** - Add missing critical content
4. **Verify quality** - Check visual layout

## Supported Formats

### Input Formats
- ✅ **.pptx** (PowerPoint 2007+) - Direct processing
- ✅ **.ppt** (PowerPoint 97-2003) - Auto-converts to .pptx

### Conversion Methods
1. **LibreOffice** (Linux/Mac/Windows) - Primary method
2. **Win32 COM** (Windows only) - Fallback method
3. **Manual guidance** - If auto-conversion fails

## Evaluation Dimensions

1. **基本資訊完整性** (15%) - FA number, engineer, batch, contact
2. **問題描述與定義** (15%) - Clear issue definition  
3. **分析方法與流程** (20%) - Tools, 8D process
4. **數據與證據支持** (20%) - Measurements, figures
5. **根因分析** (20%) - Statistical validation
6. **改善對策** (10%) - Preventive measures

## Improvement Workflow

### Step 1: Format Detection & Conversion

If .ppt file detected:
```
⚠️  Detected legacy format (.ppt)
✓ LibreOffice conversion attempt...
✓ Win32 COM fallback (Windows)...
✓ Conversion successful: report_converted.pptx
```

### Step 2: Evaluation Analysis

Parse evaluation JSON to identify scores and specific recommendations.
**JSON Resilience (v2.1.4)**: 
The script built-in logic automatically sanitizes malformed JSON (e.g., trailing dots, commas, and Markdown code blocks) before parsing. This ensures highly reliable performance when triggered directly via CLI by AI Agents like Claude or Gemini.

**Supported JSON Formats:**

1. **Array Format** (e.g., `_summary_gpt.json`):
```json
[{"total_score": 44.3, "dimensions": {...}}]
```

2. **Object Format** (e.g., `_summary.json`):
```json
{"total_score": 55.3, "dimensions": {...}}
```

3. **Nested Dimension Scores** (v2.3.0 New):
```json
{
  "dimension_scores": {
    "基本資訊完整性": {"score": 60, "weight": 15, "comment": "..."}
  },
  "improvements": [
    {"priority": "高", "item": "基本資訊", "suggestion": "補填批號..."}
  ]
}
```
The script auto-detects and normalizes all formats.

### Step 3: Apply Improvements

**Missing Basic Info (Score < 80)**:
- Add slide with FA#, engineer, batch, customer, contact, failure rate

**Insufficient Root Cause (Score < 80)**:
- Add statistical analysis: t-test, CI, control groups

**No Prevention (Score < 85)**:
- Add slide: process improvements, monitoring, training

**Improvement Trigger Thresholds:**
| Dimension | Threshold | Action |
|-----------|-----------|--------|
| 基本資訊完整性 | < 80 | Add dynamic basic info slide with suggestions |
| 根因分析 | < 80 | Add dynamic statistical analysis from LLM |
| 改善對策 | < 85 | Add dynamic prevention measures from LLM |

### Step 4: Success Manifest Generation
The script generates a `[output].manifest.json` recording exactly what was added. This enables **Closed-Loop Verification**:
```json
{
  "execution_status": "success",
  "added_slides": [{"dimension": "Root Cause", "suggestions_count": 3}],
  "summary_applied": true
}
```

### Step 4: Quality Verification

- Convert to PDF for visual check
- Verify no text overlap
- Confirm all additions are clear

## Implementation Details

### Using the Improvement Script

```bash
python scripts/improve_fa_report.py input.ppt eval.json output.pptx
# OR
python scripts/improve_fa_report.py input.pptx eval.json output.pptx
```

The script automatically:
1. Detects file format (.ppt or .pptx)
2. Converts if needed using available tools
3. Applies all improvements
4. Saves enhanced report
5. Cleans up temporary files

### Installation

⚠️ **Critical**: Always use virtual environment to avoid dependency conflicts and keep your system clean.

**Recommended Install with Virtual Environment**:
```bash
# Create virtual environment
cd ~/.claude/skills/fa-report-improvement
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install all dependencies
pip install -r requirements.txt

# Run installation script (checks everything)
python scripts/install.py
```

**Without Virtual Environment** (Not Recommended):
```bash
# ⚠️ Warning: Installs to global Python environment
pip install -r requirements.txt
python scripts/install.py
```

**Why Virtual Environment?**
- ✅ Prevents dependency conflicts
- ✅ Keeps system Python clean
- ✅ Easy to manage and remove
- ✅ No root/admin privileges needed
- ✅ Reproducible environments

**Python Requirements** (via requirements.txt):
- python-pptx >= 0.6.21 (Required)
- Pillow >= 9.0.0 (Required)
- pywin32 >= 305 (Optional, Windows only)

**Conversion Tools** (for .ppt support):

**LibreOffice method** (All platforms):
- LibreOffice installed
- Command-line access (soffice/libreoffice)
- Linux: `sudo apt install libreoffice`
- macOS/Windows: Download from https://www.libreoffice.org/

**Win32 COM method** (Windows only):
- PowerPoint installed
- pywin32: `pip install pywin32` (included in requirements.txt)

## Best Practices

1. **Format Flexibility**: Accept both .ppt and .pptx from users
2. **Auto-Detection**: Let script handle format conversion
3. **Preserve Content**: Only enhance, never replace technical analysis
4. **Match Formatting**: Maintain original report style
5. **Verify Data**: Ensure statistical values align with tests

## Error Handling

### Conversion Failures

If auto-conversion fails:
1. Try manual conversion in PowerPoint
2. Use online converters (CloudConvert, Zamzar)
3. Re-save as .pptx manually

### Processing Failures

- Check input file is valid PowerPoint
- Verify evaluation JSON structure
- Ensure output directory exists
- Review error messages for specific issues

- Review error messages for specific issues

### Encoding Issues (Windows)
- Script enforces UTF-8 output to prevent `cp950` errors.
- Ensure your terminal supports UTF-8.

## Integration with Other Tools

Works well with:
- `pptx` skill - Advanced PowerPoint operations
- `docx` skill - Supplementary documentation
- `xlsx` skill - Data analysis and statistics

## References

For detailed information:
- `references/evaluation-criteria.md` - Complete evaluation framework
- `references/improvement-templates.md` - Standard templates
- `references/statistical-methods.md` - Statistical validation
- `references/ppt-conversion-guide.md` - Format conversion details

---
**版本**: 2.2.0  
**最後更新**: 2026-01-31

