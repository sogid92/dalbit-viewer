<p align="center">
  <img src="icon.png" width="128" alt="Dalbit Viewer icon">
</p>

# Dalbit Viewer

Undisturbed time with your images.

No ads, no installation. The UI never blocks your view — from the moment you open an image, focus only on looking.

A lightweight Windows image viewer, about 14MB.

**한국어:** [README.md](README.md)

## Highlights

### Browse folders and archives in the order you want

Organize comics or photos into folders, and it moves to the next item automatically when you finish one.

- Folders step to folders, and archives (CBZ/ZIP) step to archives. The two never mix
- Sort by name ascending/descending or date modified ascending/descending
- Folders without images are skipped
- Movement stays inside the parent folder of the item you opened. It never escapes upward
- Choose what happens at the end: loop, stop, or go to the next item

### Clean up the items you finished in one go

Press `L` to open the viewed list. Folders and archives are recorded automatically as you browse.

- Check several items, or use **Select All** to pick them all at once
- **Move to Trash** sends the actual folders and archives to the Windows Recycle Bin
- **Remove from list** leaves the disk untouched and only cleans the list
- Drive roots, the user home, Windows default folders, and system folders are protected from accidental deletion

### Fill the screen with the image

- Opens fullscreen; the top bar appears only when the mouse moves to the top
- The cursor hides after 2 seconds and returns when you move it
- The bottom slider jumps quickly through the current folder
- Background can be black, dark gray, or white

### View archives without extracting

- Open ZIP and CBZ files directly and page through the images inside
- No need to unpack comic archives into folders

### Tune the viewing and controls to your taste

- Six interpolation methods: NEAREST for pixel art, LANCZOS for photos
- Two wheel layouts: wheel for navigation or wheel for zoom
- Reassign the main shortcuts
- Korean / English

### Light, and leaves nothing behind

- No ads, no account, no tracking, no internet connection
- No installer: extract and run
- Settings are stored only inside the program folder. If you register it as the default app, an entry is added to the Windows registry

## How to run

**Run the EXE**

Download `DalbitViewer-<version>-win64.zip` from [Releases](https://github.com/sogid92/dalbit-viewer/releases), extract it, and run `DalbitViewer\DalbitViewer.exe`. Keep the folder intact; the EXE will not start if it is moved out or the other files are deleted.

Without an image it opens an icon start screen. It remembers the last window size and position, and starts fullscreen if you closed it in fullscreen. Cancelling the file picker keeps the app running, so you can open Settings or register the file association right away.

- **Resize**: drag any edge (top, bottom, left, right) or corner. All eight directions work, like a normal Windows window. Minimum is 560×320.
- **Move**: drag an empty part of the top bar.
- **Fullscreen**: `Alt+Enter` or the fullscreen button in the top bar. Press again to return to the previous window size.

**Run from source** (Python 3.10 or newer)

```bat
pip install -r requirements.txt
python main.py [image / folder / ZIP / CBZ path]
```

Without a path, a file picker opens. You can open a folder or an archive instead of a single image.

## Set as default app

To add **Open with Dalbit Viewer** to the right-click menu for archives and to list image extensions in the **Open with** menu and Default apps candidates, register once in the settings dialog.

1. Open **Settings** in the top bar.
2. At the bottom under **Explorer Registration**, press **Register**.
3. The status changes to registered and you are done.

Press **Remove** in the same place to undo it. The current state is shown under the buttons.

Registration only works when running the EXE. Running from source (`python main.py`) shows a notice instead.

**Registering does not change your default apps.** To make Dalbit Viewer the default, set it in Windows once after registering.

**Option 1: Right-click a file (one extension at a time)**

1. Right-click an image file.
2. Choose **Open with** → **Choose another app**.
3. Select **Dalbit Viewer** from the list. If it is missing, use **Look for another app on this PC** and pick `DalbitViewer\DalbitViewer.exe`.
4. Check **Always use this app** and confirm.

**Option 2: Windows Settings (one extension at a time)**

1. Open **Settings** → **Apps** → **Default apps**.
2. Under **Choose default apps by file type**, search for the extension (for example `.jpg`, `.png`) and click it.
3. Select **Dalbit Viewer** from the list.

**Option 3: All at once (per app)**

1. Open **Settings** → **Apps** → **Default apps** and click **Dalbit Viewer**.
2. Press **Set default** to assign all supported extensions at once.

**To revert**: choose another app (for example BandiView) in the same screen.

Each extension must be set separately. Supported associations: BMP, JPG, JPEG, JFIF, JPE, PNG, GIF, WebP, TIFF, TIF, AVIF, ICO, PPM, PGM, PNM, JXL, DDS, TGA, CBZ, ZIP

Archives (CBZ/ZIP) only get the right-click menu entry; the default app is left unchanged, so an existing archive program keeps its association.

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
| L | Viewed items |
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
- **Start/end behavior**: Loop / stop / go to next item (folder or archive)
- **Next item order**: Only enabled with "go to next item"

## Supported formats

- Images: JPG, PNG, GIF, WebP, TIFF, BMP, AVIF, and other formats supported by Pillow
- Archives: ZIP, CBZ (viewed without extracting)
- Animated GIF/WebP: first frame only
- HEIC/HEIF, RAW, and RAR/CBR are not supported

## Files

`settings.json` and `viewed_folders.json` are stored next to the executable (or `main.py`). If an image fails to load, the cause is written to `viewer_error.log` in the same folder.
