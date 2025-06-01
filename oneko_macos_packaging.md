# Oneko macOS Packaging Guide

## Method 1: PyInstaller (Recommended for beginners)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Create a spec file for better control
Create `oneko.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['oneko.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('theme_orange_cat', 'theme_orange_cat'),
        ('oneko.icns', '.'),
        ('oneko.ico', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='oneko',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression - can cause issues with Qt
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX compression
    upx_exclude=[],
    name='oneko',
)

app = BUNDLE(
    coll,
    name='Oneko.app',
    icon='oneko.icns',
    bundle_identifier='com.yourname.oneko',
    info_plist={
        'CFBundleName': 'Oneko',
        'CFBundleDisplayName': 'Oneko',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': False,  # Set to False so it appears in dock initially
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
    },
)
```

### Step 3: Build the app
```bash
pyinstaller oneko.spec
```

This creates `dist/Oneko.app` - a complete macOS application bundle.

### Step 4: Test the app
```bash
open dist/Oneko.app
```

## Method 2: Create DMG installer

### Option A: Using create-dmg (recommended)

1. Install create-dmg:
```bash
brew install create-dmg
```

2. Create the DMG:
```bash
create-dmg \
  --volname "Oneko Installer" \
  --volicon "oneko.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Oneko.app" 175 120 \
  --hide-extension "Oneko.app" \
  --app-drop-link 425 120 \
  "Oneko-Installer.dmg" \
  "dist/"
```

### Option B: Manual DMG creation

1. Create a temporary folder:
```bash
mkdir dmg_temp
cp -R dist/Oneko.app dmg_temp/
```

2. Create alias to Applications folder:
```bash
ln -s /Applications dmg_temp/Applications
```

3. Create DMG:
```bash
hdiutil create -volname "Oneko" -srcfolder dmg_temp -ov -format UDZO Oneko-Installer.dmg
```

## Method 3: Homebrew Cask (for wider distribution)

Create a Homebrew cask for easy installation:

1. Fork homebrew-cask repository
2. Create `Casks/oneko.rb`:

```ruby
cask "oneko" do
  version "1.0.0"
  sha256 "your_dmg_sha256_here"

  url "https://github.com/yourusername/oneko/releases/download/v#{version}/Oneko-Installer.dmg"
  name "Oneko"
  desc "Desktop cat that chases your cursor"
  homepage "https://github.com/yourusername/oneko"

  app "Oneko.app"

  zap trash: [
    "~/Library/LaunchAgents/com.oneko.plist",
  ]
end
```

## Method 4: Notarization (for distribution outside App Store)

For wider distribution without Gatekeeper warnings:

### Step 1: Code signing
```bash
codesign --force --deep --sign "Developer ID Application: Your Name" dist/Oneko.app
```

### Step 2: Create signed DMG
```bash
hdiutil create -volname "Oneko" -srcfolder dist -ov -format UDZO temp.dmg
codesign --sign "Developer ID Application: Your Name" temp.dmg
mv temp.dmg Oneko-Installer.dmg
```

### Step 3: Notarize with Apple
```bash
xcrun notarytool submit Oneko-Installer.dmg --keychain-profile "notarytool-profile" --wait
```

### Step 4: Staple the notarization
```bash
xcrun stapler staple Oneko-Installer.dmg
```

## Quick Start Instructions

For the simplest approach:

1. **Install PyInstaller**: `pip install pyinstaller`
2. **Create the spec file** (copy the content above into `oneko.spec`)
3. **Build**: `pyinstaller oneko.spec`
4. **Test**: `open dist/Oneko.app`
5. **Create DMG**: Use create-dmg or manual method above

## File Structure
Make sure your files are organized like this:
```
oneko/
├── oneko.py
├── oneko.spec
├── oneko.icns
├── oneko.ico
└── theme_orange_cat/
    ├── 1.GIF
    ├── 2.GIF
    └── ... (all GIF files)
```

## Distribution Tips

1. **GitHub Releases**: Upload your DMG to GitHub releases for easy distribution
2. **Include README**: Add installation instructions
3. **Test on clean system**: Always test your installer on a fresh Mac
4. **Consider signing**: For wider distribution, invest in Apple Developer Program ($99/year)

The PyInstaller + create-dmg approach gives you a professional-looking installer that users can simply drag-and-drop to install Oneko on their Macs.