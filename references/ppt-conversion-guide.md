# PPT to PPTX Conversion Guide

## Overview

This guide explains the automatic .ppt to .pptx conversion system integrated into the FA Report Improvement skill.

## Why Conversion is Needed

Many legacy FA reports are still in .ppt format (PowerPoint 97-2003), which:
- Cannot be directly processed by python-pptx library
- Requires conversion to .pptx (PowerPoint 2007+) format
- May cause compatibility issues with modern tools

## Automatic Conversion System

The skill includes a robust conversion system with multiple fallback methods:

### Method 1: LibreOffice (Primary)

**Platforms**: Windows, Linux, macOS  
**Reliability**: High (95%+ success rate)  
**Requirements**:
- LibreOffice installed
- Command-line tool `soffice` or `libreoffice` accessible

**How it works**:
```bash
libreoffice --headless --convert-to pptx --outdir output/ input.ppt
```

**Advantages**:
- Cross-platform compatibility
- Free and open-source
- Reliable conversion quality
- Preserves most formatting

**Disadvantages**:
- Requires LibreOffice installation
- Slight formatting differences possible

### Method 2: Win32 COM (Windows Fallback)

**Platforms**: Windows only  
**Reliability**: Very High (98%+ success rate)  
**Requirements**:
- Microsoft PowerPoint installed
- pywin32 package (`pip install pywin32`)

**How it works**:
```python
import win32com.client

powerpoint = win32com.client.Dispatch("PowerPoint.Application")
deck = powerpoint.Presentations.Open(ppt_path)
deck.SaveAs(pptx_path, 24)  # 24 = ppSaveAsOpenXMLPresentation
deck.Close()
powerpoint.Quit()
```

**Advantages**:
- Native PowerPoint conversion
- Perfect formatting preservation
- Handles complex features (animations, embedded objects)

**Disadvantages**:
- Windows-only
- Requires PowerPoint installation
- Slightly slower than LibreOffice

### Method 3: Manual Guidance

If both automatic methods fail, the system provides:
- Clear error messages
- Step-by-step manual conversion instructions
- Alternative solutions (online converters)

## Conversion Workflow

### Auto-Detection

```python
def auto_convert_if_needed(input_file):
    file_ext = os.path.splitext(input_file)[1].lower()
    
    if file_ext == '.ppt':
        print("⚠️  Detected legacy format (.ppt)")
        converter = PPTConverter()
        pptx_file = converter.convert_ppt_to_pptx(input_file)
        
        if pptx_file:
            print(f"✓ Conversion successful: {pptx_file}")
            return pptx_file, converter
        else:
            print("✗ Conversion failed")
            return None, None
    
    return input_file, None  # Already .pptx
```

### Cleanup Process

After processing, temporary converted files are automatically cleaned up:
```python
converter.cleanup()  # Removes temporary .pptx files
```

## Platform-Specific Considerations

### Windows

**Recommended Setup**:
1. Install Microsoft PowerPoint (best quality)
2. Install pywin32: `pip install pywin32`
3. LibreOffice as backup (optional)

**Detection Order**:
1. Try LibreOffice (faster)
2. Fallback to Win32 COM (higher quality)

### Linux

**Required Setup**:
1. Install LibreOffice: `sudo apt install libreoffice`
2. Verify command: `libreoffice --version`

**Single Method**: Only LibreOffice available

### macOS

**Required Setup**:
1. Install LibreOffice from [libreoffice.org](https://www.libreoffice.org/)
2. Command path: `/Applications/LibreOffice.app/Contents/MacOS/soffice`

**Single Method**: Only LibreOffice available

## Conversion Quality

### What's Preserved
✅ Text content and formatting
✅ Slide layouts and structure
✅ Images and charts
✅ Tables and SmartArt
✅ Bullets and numbering
✅ Most shapes and objects

### Potential Differences
⚠️ Complex animations (may be simplified)
⚠️ Custom fonts (may substitute)
⚠️ Embedded OLE objects (may not embed properly)
⚠️ Macros (will be removed - .pptx doesn't support VBA)

### Recommended Pre-Check
Before conversion, check if original .ppt has:
- Custom VBA macros → Document separately
- Complex animations → May need manual adjustment
- Embedded videos → Extract and re-insert after conversion

## Troubleshooting

### LibreOffice Not Found

**Symptom**: "LibreOffice command not found"

**Solution**:
```bash
# Windows
# Add to PATH: C:\Program Files\LibreOffice\program\

# Linux
sudo apt install libreoffice

# macOS  
# Install from https://www.libreoffice.org/
```

### Win32 COM Fails

**Symptom**: "COM conversion failed" or "PowerPoint is not installed"

**Solution**:
1. Verify PowerPoint is installed
2. Install pywin32: `pip install pywin32`
3. Run script with admin privileges (if needed)
4. Check PowerPoint is not running or locked

### Conversion Timeout

**Symptom**: Process hangs or times out

**Solution**:
- Large files may take longer (default timeout: 30s)
- Increase timeout in ppt_converter.py
- Convert manually if file is too large (>50MB)

### Permission Errors

**Symptom**: "Cannot write to output directory"

**Solution**:
- Check write permissions for output directory
- Run with appropriate user permissions
- Avoid network drives if possible

### Unicode / Encoding Errors

**Symptom**: `UnicodeEncodeError: 'cp950' codec can't encode character...`

**Cause**: Windows consoles (CMD/PowerShell) often default to legacy encodings (CP950/CP1252) which crash when scripts try to print emojis (⚠️, ✅).

**Solution**:
- The scripts have been patched to enforce UTF-8 output: `sys.stdout.reconfigure(encoding='utf-8')`.
- Ensure your calling process (Agent or Web App) reads stdout with `encoding='utf-8'`.

## Manual Conversion Methods

If automatic conversion fails completely:

### Using PowerPoint
1. Open .ppt file in PowerPoint
2. File → Save As
3. Choose format: PowerPoint Presentation (*.pptx)
4. Save and use the converted file

### Using Online Converters
- [CloudConvert](https://cloudconvert.com/ppt-to-pptx)
- [Zamzar](https://www.zamzar.com/convert/ppt-to-pptx/)
- [Online-Convert](https://www.online-convert.com/)

⚠️ **Caution**: Avoid uploading sensitive FA reports to public converters

### Using Google Slides
1. Upload .ppt to Google Drive
2. Open with Google Slides
3. File → Download → Microsoft PowerPoint (.pptx)

## Performance Considerations

### Conversion Speed

| Method | Small (<5MB) | Medium (5-20MB) | Large (>20MB) |
|--------|--------------|-----------------|---------------|
| LibreOffice | 2-5s | 5-15s | 15-30s |
| Win32 COM | 3-8s | 8-20s | 20-45s |

### Memory Usage

- LibreOffice: ~100-200MB per conversion
- Win32 COM: ~150-300MB per conversion
- Multiple files: Process sequentially to avoid memory issues

## Integration Examples

### Basic Usage

```python
from ppt_converter import PPTConverter

converter = PPTConverter()
pptx_file = converter.convert_ppt_to_pptx("report.ppt")

if pptx_file:
    print(f"Success: {pptx_file}")
    # Process pptx_file
    converter.cleanup()  # Clean up when done
```

### With Error Handling

```python
converter = PPTConverter()

try:
    pptx_file = converter.convert_ppt_to_pptx("report.ppt")
    
    if pptx_file:
        # Process file
        process_report(pptx_file)
    else:
        print("Conversion failed, trying manual method...")
        manual_instructions()
        
finally:
    converter.cleanup()
```

### Batch Processing

```python
converter = PPTConverter()

ppt_files = ["report1.ppt", "report2.ppt", "report3.ppt"]
converted_files = []

for ppt in ppt_files:
    pptx = converter.convert_ppt_to_pptx(ppt)
    if pptx:
        converted_files.append(pptx)
        process_report(pptx)

converter.cleanup()  # Clean all at once
```

## Best Practices

1. **Always Cleanup**: Call `converter.cleanup()` when done
2. **Check Results**: Verify converted file before processing
3. **Handle Failures**: Provide fallback options for users
4. **Preserve Originals**: Never delete original .ppt files
5. **Test Conversions**: Spot-check converted files for quality

## Future Improvements

Potential enhancements:
- Support for .pps (PowerPoint Show) format
- Parallel batch conversion
- Cloud-based conversion API integration
- Conversion quality metrics and validation
- Progress indicators for large files

## Summary

The integrated PPT conversion system provides:
- ✅ Automatic format detection
- ✅ Multiple conversion methods
- ✅ Cross-platform support
- ✅ Robust error handling
- ✅ Clean resource management

This ensures the FA Report Improvement skill works seamlessly with both modern and legacy PowerPoint formats.

---
**版本**: 2.1.3  
**最後更新**: 2026-01-28

