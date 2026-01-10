# FFmpeg Installation Guide

The Media Converter app requires FFmpeg to work. Follow these steps:

## Windows Installation

### Option 1: Download Pre-built FFmpeg (Recommended)
1. Go to https://ffmpeg.org/download.html
2. Click on Windows icon
3. Download the full build (not essentials)
4. Extract the zip file to a folder like `C:\ffmpeg`
5. Add FFmpeg to Windows PATH:
   - Right-click "This PC" or "My Computer" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", click "New"
   - Variable name: `PATH`
   - Variable value: `C:\ffmpeg\bin` (or wherever you extracted it)
   - Click OK and restart your computer

### Option 2: Use Chocolatey (if you have it installed)
```powershell
choco install ffmpeg
```

### Option 3: Use Windows Package Manager
```powershell
winget install ffmpeg
```

## Verify Installation

After installation, test it in PowerShell:
```powershell
ffmpeg -version
```

If it shows the version information, FFmpeg is correctly installed.

## Then run the app:
```powershell
python app.py
```

And open Chrome to: http://localhost:8080
