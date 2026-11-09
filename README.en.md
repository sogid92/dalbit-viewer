# Dalbit Viewer

A fullscreen image viewer for Windows. The interface stays out of the way until you need it.

**한국어:** [README.md](README.md)

## Requirements

- Windows 10/11
- Python 3.10 or newer (only to run from source or build the EXE)
- Pillow

## Run without Python (regular users)

Download `DalbitViewer-<version>-win64.zip` from [Releases](https://github.com/sogid92/dalbit-viewer/releases).

1. Extract the ZIP.
2. Run `DalbitViewer\DalbitViewer.exe`.

No Python installation is required. Do not move the EXE out of its folder or delete the other files, or it will not start.
To open images by double-clicking in Explorer, run `register.bat` once from that folder.

## Run

```bat
pip install -r requirements.txt
python main.py [image / folder / ZIP / CBZ path]
```

Without a path, a file picker opens. You can open a folder or an archive instead of a single image.

## Build an EXE

Double-click `build_exe.bat`. The result is `dist\DalbitViewer\DalbitViewer.exe`.

To run on a PC without Python, copy the whole `dist\DalbitViewer` folder. The EXE alone will not run. To register the file association on that PC too, put `register.bat` in the same folder and run it.

## Open from Explorer

Run `install.bat` once. It builds the EXE and registers the file association. Use `uninstall.bat` to remove it.

Windows may still require you to pick the app once in Default apps. The association must point to `DalbitViewer.exe`, not to `main.py` or a `.bat` file.

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
