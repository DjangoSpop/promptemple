# PromptForge Pro - Icon Fix Instructions

## Problem
The extension is looking for PNG icon files but we only have an SVG file.

## Solution Options

### Option 1: Use the Icon Generator HTML File
1. Open `icon-generator.html` in your web browser
2. The page will show the original SVG and generated PNG previews
3. Click each "Download" button to save:
   - `icon16.png` (16x16 pixels)
   - `icon32.png` (32x32 pixels)  
   - `icon48.png` (48x48 pixels)
   - `icon128.png` (128x128 pixels)
4. Save these files in the `icons/` folder, replacing the existing placeholder files
5. Reload the extension in Chrome

### Option 2: Use Online SVG to PNG Converter
1. Go to any online SVG to PNG converter (like convertio.co, cloudconvert.com)
2. Upload the `icons/icon.svg` file
3. Convert to PNG at different sizes: 16x16, 32x32, 48x48, 128x128
4. Download and rename the files as mentioned above
5. Place them in the `icons/` folder

### Option 3: Use Image Editing Software
1. Open `icons/icon.svg` in GIMP, Photoshop, or any image editor
2. Export/Save As PNG at each required size
3. Save with the correct filenames in the `icons/` folder

## Current Status
- ✅ Manifest updated to expect PNG files
- ✅ Placeholder files created (these need to be replaced with actual PNGs)
- ✅ Icon generator HTML file available
- ⚠️ Temporary placeholder files are actually SVG content - they need proper PNG replacements

## Quick Test
After creating the PNG files:
1. Go to `chrome://extensions/`
2. Click the refresh button on the PromptForge Pro extension
3. The error should be resolved

The extension should now load properly with the correct icon files!
