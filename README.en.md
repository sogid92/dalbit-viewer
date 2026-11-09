# Dalbit Viewer

A fullscreen image viewer for Windows. The interface stays out of the way until you need it.

**한국어:** [README.md](README.md)

## How to run

**Run the EXE**

Download `DalbitViewer-<version>-win64.zip` from [Releases](https://github.com/sogid92/dalbit-viewer/releases), extract it, and run `DalbitViewer\DalbitViewer.exe`. Keep the folder intact; the EXE will not start if it is moved out or the other files are deleted.

**Run from source** (Python 3.10 or newer)

```bat
pip install -r requirements.txt
python main.py [image / folder / ZIP / CBZ path]
```

Without a path, a file picker opens. You can open a folder or an archive instead of a single image.

## Set as default app

To open images in Dalbit Viewer by double-clicking, register it in Windows once.

**Option 1: Right-click a file**

1. Right-click an image file.
2. Choose **Open with** → **Choose another app**.
3. If it is not listed, use **Look for another app on this PC** and select `DalbitViewer\DalbitViewer.exe`.
4. Check **Always use this app** and confirm.

**Option 2: Windows Settings**

1. Open **Settings** → **Apps** → **Default apps**.
2. Search for the extension (for example `.jpg`, `.png`) and click it.
3. Select **Dalbit Viewer** from the list.

Each extension must be set separately. Supported associations: BMP, JPG, JPEG, JFIF, PNG, GIF, WebP, TIFF, AVIF, ICO, PPM, JXL, DDS, TGA, CBZ

Windows does not allow an app to change the default silently, so this has to be done once manually. After that, double-clicking opens the viewer.

## Controls

| Input | Action |
|---|---|
| Esc, top bar ✕ | Quit |
| ← → ↑ ↓ / WASD | Pan while zoomed; at the edge, previous/next |
| PageUp / PageDown, Space / Backspace | Previous / next |
| Home / End | First / last |
| Mouse wheel | Previous/next or zoom, per settings (default: previous/next) |
| Ctrl + mouse wheel | Zoom or previous/next, per settings (default: zoom) |
| 9 / 8 / 0 | Fit screen / fit width / original size |
| Double-click | Toggle fit ↔ original |
| Drag | Move a zoomed image |
| Alt+Enter | Toggle fullscreen / windowed |
| Ctrl+O | Open a file |
| Ctrl+S | Open settings |
| L | Viewed folders |
| Move mouse to top | Show the top bar |
| Move mouse to bottom | Show the bottom slider |

Shortcuts can be changed in Settings → Shortcuts. A few keys (arrows, PageUp/PageDown, Space, etc.) are fixed.

## Settings

Open with the Settings button in the top bar or `Ctrl+S`. Changes apply and save immediately.

- **Language**: Korean / English. Only the first launch follows the Windows display language; after that, change it here.
- **Interpolation**: Zoom quality. The selected method's description is shown in the dialog.
- **Image size**: Default size when opening a new image
- **Mouse wheel**: Choose the wheel / Ctrl+wheel roles
- **Background**: Black / dark gray / white
- **Bottom slider**: Auto / always / never
- **Start/end behavior**: Loop / stop / go to next folder
- **Next folder order**: Only enabled with "go to next folder"

## Viewed folders (L)

Folders are recorded when you move to the next folder with the "go to next folder" behavior. Checked folders can be moved to the Windows Recycle Bin or removed from the list only. Drive roots, the user home, Windows default folders, and system folders cannot be deleted.

## Supported formats

- Images: JPG, PNG, GIF, WebP, TIFF, BMP, AVIF, and other formats supported by Pillow
- Archives: ZIP, CBZ (viewed without extracting)
- Animated GIF/WebP: first frame only
- HEIC/HEIF, RAW, and RAR/CBR are not supported

## Files

`settings.json` and `viewed_folders.json` are stored next to the executable (or `main.py`). If an image fails to load, the cause is written to `viewer_error.log` in the same folder.
