#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
달빛뷰어 — 미니멀 이미지 뷰어 (UI 없음, 전체화면 전용)
- 이미지 열면 UI 없이 이미지 하나만 전체화면으로 표시
- 메뉴/툴바/상태바/정보 패널/필터/히스토그램 없음. Canvas 1개만 존재
- 조작은 키보드 + 마우스만. 화면에 어떤 글자/버튼도 띄우지 않음
- 보간기법(확대/축소 시 픽셀 계산 방식) 6종 지원, I 키로 순환, 1~6 키로 직접 선택
  설정은 settings.json에 저장되어 다음 실행에도 유지됨
- 의존성: Python 3.10+, Pillow (pip install Pillow)
- 실행: python main.py [이미지/폴더/압축파일 경로]
  경로를 안 주면 파일 선택 대화상자가 뜬 뒤 전체화면으로 열림
- EXE 빌드 (Windows): build_exe.bat 실행
"""
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk, ImageOps
    try:
        import pillow_avif  # noqa: F401  # AVIF 지원이 있으면 자동 활성화
    except Exception:
        pass
except ImportError:
    print("Pillow가 필요합니다: pip install Pillow")
    raise

# ---------- 언어 ----------
# 한국어 원문을 키로 쓰는 경량 번역. UI 문자열만 tr()로 감싼다.
_LANG = "ko"
TRANSLATIONS = {
    "한국어": "Korean",
    "언어": "Language",
    "달빛뷰어": "Dalbit Viewer",
    "파일 ▾": "File ▾",
    "설정(Settings)": "Settings",
    "설정": "Settings",
    "너비 맞춤": "Fit Width",
    "화면 맞춤": "Fit Screen",
    "원본 크기": "Original Size",
    "열람한 폴더 목록": "Viewed Items",
    "창모드 (Alt+Enter)": "Windowed (Alt+Enter)",
    "전체화면 (Alt+Enter)": "Fullscreen (Alt+Enter)",
    "최소화": "Minimize",
    "이전 크기로": "Restore",
    "최대화": "Maximize",
    "닫기": "Close",
    "파일 열기...  (O)": "Open File...  (O)",
    "압축파일 열기...  (ZIP/CBZ)": "Open Archive...  (ZIP/CBZ)",
    "열람한 폴더 목록...  (L)": "Viewed Items...  (L)",
    "탐색기 연결": "Explorer Registration",
    "등록": "Register",
    "해제": "Remove",
    "등록되어 있습니다.\n"
    "· 압축파일(CBZ/ZIP) 우클릭 메뉴에 '달빛뷰어로 열기' 추가\n"
    "· 이미지 확장자(JPG/PNG 등)를 '연결 프로그램' 목록과 기본 앱 후보에 추가\n"
    "기본 앱은 바뀌지 않습니다. Windows 설정 > 기본 앱에서 직접 선택하세요.":
        "Registered.\n"
        "· Adds 'Open with Dalbit Viewer' to the archive (CBZ/ZIP) right-click menu\n"
        "· Adds image extensions (JPG/PNG, etc.) to the 'Open with' list and Default apps candidates\n"
        "Your default apps are not changed. Choose Dalbit Viewer in Windows Settings > Default apps.",
    "등록되지 않았습니다. '등록'을 누르면 다음이 추가됩니다.\n"
    "· 압축파일(CBZ/ZIP) 우클릭 메뉴 '달빛뷰어로 열기'\n"
    "· 이미지 확장자를 '연결 프로그램' 목록과 기본 앱 후보에 추가\n"
    "기본 앱은 바뀌지 않습니다.":
        "Not registered. Press Register to add:\n"
        "· 'Open with Dalbit Viewer' to the archive (CBZ/ZIP) right-click menu\n"
        "· Image extensions to the 'Open with' list and Default apps candidates\n"
        "Your default apps are not changed.",
    "압축파일 우클릭 메뉴에 '달빛뷰어로 열기'를 등록했습니다.":
        "Added 'Open with Dalbit Viewer' to the archive right-click menu.",
    "탐색기 연결을 해제했습니다.\n기존 압축 프로그램의 연결은 그대로 유지됩니다.":
        "Explorer registration removed.\nYour existing archive program keeps its association.",
    "EXE로 실행할 때만 등록할 수 있습니다.\n\n릴리스 ZIP에서 DalbitViewer.exe를 실행한 뒤 다시 시도하세요.":
        "Registration works only when running the EXE.\n\nRun DalbitViewer.exe from the release ZIP and try again.",
    "작업을 완료하지 못했습니다.": "The operation could not be completed.",
    "파일 연결 등록은 Windows에서만 지원합니다.":
        "File association is only supported on Windows.",
    "파일 연결 등록은 EXE로 빌드한 뒤에 실행하세요.":
        "Build the EXE first to register file associations.",
    "먼저 EXE를 만든 뒤 그 파일에서 실행하세요.":
        "Create the EXE first, then run it.",
    "파일 연결 해제는 Windows에서만 지원합니다.":
        "Removing the association is only supported on Windows.",
    "등록 실패: %s": "Registration failed: %s",
    "등록 완료: %s": "Registered: %s",
    "연결된 확장자: %s": "Associated extensions: %s",
    "압축파일은 우클릭 메뉴에서 '달빛뷰어로 열기'로 열 수 있습니다.":
        "Archives can be opened from the right-click menu with 'Open with Dalbit Viewer'.",
    "기본 앱으로 지정하려면 Windows 설정 > 기본 앱에서 한 번 선택하세요.":
        "To set it as the default app, choose it once in Windows Settings > Default apps.",
    "파일 연결 해제 완료.": "File association removed.",
    "보간기법 (확대/축소 품질)": "Interpolation (zoom quality)",
    "이미지 크기": "Image Size",
    "너비 맞춤 (8)": "Fit Width (8)",
    "화면 맞춤 (9)": "Fit Screen (9)",
    "원본 100% (0)": "Original 100% (0)",
    "단축키 설정...": "Shortcuts...",
    "마우스 휠 동작": "Mouse Wheel",
    "휠 = 이동, Ctrl+휠 = 확대/축소 (기본)": "Wheel = navigate, Ctrl+Wheel = zoom (default)",
    "휠 = 확대/축소, Ctrl+휠 = 이동": "Wheel = zoom, Ctrl+Wheel = navigate",
    "배경색": "Background",
    "검정": "Black",
    "어두운 회색": "Dark Gray",
    "흰색": "White",
    "하단 슬라이드바": "Bottom Slider",
    "마우스 아래로 내리면 표시": "Show when mouse moves down",
    "항상 표시": "Always show",
    "표시 안 함": "Never show",
    "처음/끝 동작": "Start/End Behavior",
    "반복 (끝에서 다시 처음으로)": "Loop (wrap around)",
    "멈춤 (끝에서 더 이상 이동 안 함)": "Stop at ends",
    "다음 폴더로 이동": "Go to next item",
    "다음 항목으로 이동 (폴더·압축파일)": "Go to next item (folder or archive)",
    "다음 폴더 순서": "Next Item Order",
    "다음 항목 순서": "Next Item Order",
    "이름 오름차순": "Name ascending",
    "이름 내림차순": "Name descending",
    "수정날짜 오름차순": "Date modified ascending",
    "수정날짜 내림차순": "Date modified descending",
    "단축키 설정": "Shortcuts",
    "키 버튼을 누른 뒤 새 키를 누르세요. Esc는 취소입니다. (Alt는 포함되지 않습니다.)":
        "Click a key button, then press a new key. Esc cancels. (Alt is not stored.)",
    "키 입력...": "Press key...",
    "새 단축키를 누르세요. (Esc 취소)": "Press the new shortcut. (Esc to cancel)",
    "일반 키를 누르세요.": "Press a regular key.",
    "%s 키는 고정 단축키입니다.": "%s is a fixed shortcut.",
    "%s 키는 '%s'에 이미 사용 중입니다.": "%s is already used by '%s'.",
    "저장되었습니다.": "Saved.",
    "기본값으로 복원했습니다.": "Defaults restored.",
    "기본값": "Defaults",
    "기본 조작\n"
    "방향키 / WASD : 확대 시 화면 이동, 맞춤 보기에서는 이전·다음\n"
    "PageUp / PageDown, Space / Backspace : 이전·다음\n"
    "Home / End : 처음·마지막\n"
    "Alt+Enter : 전체화면\n"
    "Ctrl+O : 파일 열기\n"
    "마우스 휠 : 설정에 따라 이동/확대·축소 (기본: 이동)\n"
    "Ctrl + 마우스 휠 : 설정에 따라 확대·축소/이동 (기본: 확대·축소)\n"
    "Esc : 종료":
        "Basic Controls\n"
        "Arrows / WASD: pan when zoomed, prev/next in fit view\n"
        "PageUp / PageDown, Space / Backspace: prev/next\n"
        "Home / End: first/last\n"
        "Alt+Enter: fullscreen\n"
        "Ctrl+O: open file\n"
        "Mouse wheel: navigate or zoom per settings (default: navigate)\n"
        "Ctrl + mouse wheel: zoom or navigate per settings (default: zoom)\n"
        "Esc: quit",
    "열람한 목록": "Viewed Items",
    "항목을 체크한 뒤 아래 버튼을 누르세요. 휴지통 이동은 실제 삭제, 목록 제거는 이 목록에서만 숨깁니다.":
        "Check items, then use the buttons below. Move to Trash deletes them; Remove only hides them from this list.",
    "전체 선택": "Select All",
    "체크 %d개 / 전체 %d개": "%d checked / %d total",
    "기록된 항목이 없습니다. 끝까지 본 뒤 다음으로 넘어가면 추가됩니다.":
        "No items recorded yet. An item is added after you reach its end and move on.",
    "끝까지 본 항목 %d개": "%d items viewed to the end",
    "%d개를 목록에서 제거했습니다. (디스크는 그대로)":
        "Removed %d from the list. (Files on disk are unchanged)",
    "\n... 외 %d개": "\n... and %d more",
    "\n\n현재 보고 있는 항목이 포함되어 있어 화면이 비워집니다.":
        "\n\nThe item you are viewing is included, so the view will be cleared.",
    "%d개 항목을 휴지통으로 보냅니다.\n폴더는 하위 파일도 함께 이동합니다.\n\n%s%s\n\n계속할까요?":
        "Move %d items to the Trash?\nFiles inside folders will move too.\n\n%s%s\n\nContinue?",
    "휴지통으로 이동": "Move to Trash",
    "%d개를 휴지통으로 보냈습니다.": "Moved %d to the Trash.",
    "휴지통으로 보낸 항목이 없습니다.": "No items were moved to the Trash.",
    " %d개 실패.": " %d failed.",
    "일부 폴더를 이동하지 못했습니다": "Some folders could not be moved",
    "체크한 항목을 휴지통으로 이동": "Move Checked to Trash",
    "체크한 항목을 목록에서만 제거": "Remove Checked from List",
    "폴더 열기": "Open Folder",
    "압축파일 열기 (풀지 않고 보기)": "Open Archive (view without extracting)",
    "모든 파일": "All Files",
    "압축파일": "Archives",
    "이미지 열기": "Open Image",
    "이미지": "Images",
    "이미지를 열 수 없습니다.": "Cannot open the image.",
    "이미지를 열 수 없습니다": "Cannot Open Image",
    "%s\n\n%s\n\n지원: JPG/PNG/GIF/WebP/TIFF/BMP/AVIF 등\n"
    "HEIC/HEIF, CLIP, 최신 RAW는 이 빌드에서 지원하지 않습니다.\n"
    "자세한 원인은 viewer_error.log를 확인하세요.":
        "%s\n\n%s\n\nSupported: JPG/PNG/GIF/WebP/TIFF/BMP/AVIF, etc.\n"
        "HEIC/HEIF, CLIP, and the latest RAW formats are not supported in this build.\n"
        "See viewer_error.log for details.",
    "파일이 존재하지 않습니다.": "The file does not exist.",
    "폴더 안에 표시할 이미지가 없습니다.": "No displayable images in this folder.",
    "압축파일 안에 표시할 이미지가 없습니다.": "No displayable images in this archive.",
    "압축파일 열기 오류: %s": "Failed to open archive: %s",
    "지원하지 않는 파일 형식입니다: %s": "Unsupported file type: %s",
    "다음: ": "Next: ",
    "이전: ": "Previous: ",
    "마지막 항목입니다": "This is the last item.",
    "첫 번째 항목입니다": "This is the first item.",
    "경로를 확인할 수 없습니다.": "Cannot resolve the path.",
    "경로가 존재하지 않습니다.": "The path does not exist.",
    "폴더나 압축파일만 삭제할 수 있습니다.": "Only folders and archives can be deleted.",
    "드라이브 루트는 삭제할 수 없습니다.": "Drive roots cannot be deleted.",
    "사용자 홈 폴더는 삭제할 수 없습니다.": "The user home folder cannot be deleted.",
    "프로그램 폴더는 삭제할 수 없습니다.": "The program folder cannot be deleted.",
    "시스템 폴더는 삭제할 수 없습니다.": "System folders cannot be deleted.",
    "Windows 기본 폴더는 삭제할 수 없습니다.": "Windows default folders cannot be deleted.",
    "휴지통 이동은 Windows에서만 지원합니다.": "Moving to the Trash is only supported on Windows.",
    "Windows 오류 0x%X": "Windows error 0x%X",
    "취소되었습니다.": "Cancelled.",
    "가장 빠름 · 화질 거침 · 도트/픽셀아트용": "Fastest · rough quality · for pixel art",
    "빠름 · 축소에 강함 · 영역 평균": "Fast · strong for downscaling · area average",
    "빠름 · 부드러운 편 · 주변 4픽셀 평균": "Fast · fairly smooth · averages 4 nearby pixels",
    "보통 · 선명 · 축소 시 디테일 유지": "Moderate · sharp · keeps detail when downscaling",
    "느린 편 · 고화질 · 주변 16픽셀 참조": "Slower · high quality · samples 16 nearby pixels",
    "가장 느림 · 최고 화질 · 기본값": "Slowest · best quality · default",
    "%d/%d · 무한 반복": "%d/%d · looping",
    "%d/%d · 1회 재생": "%d/%d · once",
    "%d/%d · %d/%d회": "%d/%d · %d/%d plays",
    "재생 완료 · 1회": "Finished · once",
    "재생 완료 · %d회": "Finished · %d plays",
}


def set_language(lang):
    global _LANG
    _LANG = lang if lang in ("ko", "en") else "ko"


def tr(text):
    return TRANSLATIONS.get(text, text) if _LANG == "en" else text


def detect_system_language():
    # 첫 실행에서만 사용한다. Windows UI 언어가 한국어면 ko, 그 외는 en.
    if os.name == "nt":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "ko" if (langid & 0x3FF) == 0x12 else "en"
        except Exception:
            pass
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        if os.environ.get(var, "").lower().startswith("ko"):
            return "ko"
    return "en"


IMG_EXTS = {".bmp", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".tif",
            ".ico", ".ppm", ".pgm", ".pnm", ".avif", ".jxl", ".dds", ".tga"}
ARCHIVE_EXTS = {".zip", ".cbz"}
VERSION = "1.3.2"  # EXE가 최신인지 확인용: EXE --version 으로 출력됨


def animation_play_count(im):
    # GIF의 loop는 첫 재생 후 추가 반복 횟수, WebP/APNG의 loop는 총 재생 횟수다.
    loop = im.info.get("loop")
    if loop is None:
        return 1
    if loop == 0:
        return 0  # 무한 반복
    return loop + 1 if getattr(im, "format", "") == "GIF" else loop


def log_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "viewer_error.log"
    return Path(__file__).resolve().parent / "viewer_error.log"


def log_error(msg):
    # 정상 시청 중에는 UI를 띄우지 않으므로, 실패 원인은 로그 파일에만 남긴다.
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write("[%s] argv=%r %s\n" % (datetime.now().isoformat(timespec="seconds"),
                                            sys.argv, msg))
    except Exception:
        pass

# 보간기법: (이름, Pillow 필터, 설명)
# 보간기법은 표준 6종으로 구현한다.
# 일반 이미지 뷰어/편집기에서 통용되는 표준 6종을 Pillow 필터로 구현했다.
INTERPOLATIONS = [
    ("NEAREST", Image.NEAREST, "가장 빠름 · 화질 거침 · 도트/픽셀아트용"),
    ("BOX", Image.BOX, "빠름 · 축소에 강함 · 영역 평균"),
    ("BILINEAR", Image.BILINEAR, "빠름 · 부드러운 편 · 주변 4픽셀 평균"),
    ("HAMMING", Image.HAMMING, "보통 · 선명 · 축소 시 디테일 유지"),
    ("BICUBIC", Image.BICUBIC, "느린 편 · 고화질 · 주변 16픽셀 참조"),
    ("LANCZOS", Image.LANCZOS, "가장 느림 · 최고 화질 · 기본값"),
]
DEFAULT_INTERP = 5  # LANCZOS


# 사용자 설정 가능한 단축키: (action_id, 표시 이름, 기본 키)
SHORTCUT_ACTIONS = [
    ("width", "너비 맞춤", "8"),
    ("fit", "화면 맞춤", "9"),
    ("original", "원본 크기", "0"),
    ("settings", "설정", "control-s"),
    ("viewed", "열람한 폴더 목록", "l"),
]
SHORTCUT_DEFAULTS = {a: d for a, _label, d in SHORTCUT_ACTIONS}
SHORTCUT_LABELS = {a: label for a, label, _d in SHORTCUT_ACTIONS}

# 단축키 설정에서 바꿀 수 없는 기본 조작 키
FIXED_SHORTCUT_KEYS = {
    "space", "backspace", "left", "right", "up", "down",
    "a", "d", "w", "s", "home", "end",
    "alt-return", "control-o", "prior", "next", "return",
    "tab", "iso_left_tab",
}
_MODIFIER_KEYSYMS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Win_L", "Win_R", "Super_L", "Super_R", "Caps_Lock", "Num_Lock",
}


def normalize_key_id(event):
    # Tk 이벤트를 저장/비교용 키 ID로 정규화한다. 예: Ctrl+S -> "control-s"
    # Alt는 단축키에 포함하지 않는다.
    ks = event.keysym
    if ks in _MODIFIER_KEYSYMS:
        return None
    key = ks.lower()
    mods = []
    if event.state & 0x4:
        mods.append("control")
    if mods:
        return "-".join(mods + [key])
    return key


def format_key_id(key_id):
    if not key_id:
        return ""
    parts = key_id.split("-")
    mods = []
    while parts and parts[0] in ("control", "alt"):
        mods.append(parts.pop(0))
    key = "-".join(parts)
    names = {
        "escape": "Esc", "prior": "PageUp", "next": "PageDown",
        "space": "Space", "backspace": "Backspace", "return": "Enter",
        "f11": "F11", "plus": "+", "minus": "-", "equal": "=",
        "home": "Home", "end": "End", "left": "←", "right": "→",
        "up": "↑", "down": "↓",
    }
    if len(key) == 1:
        key_name = key.upper()
    else:
        key_name = names.get(key, key.capitalize())
    mod_names = {"control": "Ctrl", "alt": "Alt"}
    return "+".join([mod_names.get(m, m) for m in mods] + [key_name])


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def settings_path():
    # EXE로 실행 중이면 EXE 옆, 스크립트면 main.py 옆에 저장
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "settings.json"
    return Path(__file__).resolve().parent / "settings.json"


DEFAULT_SETTINGS = {
    "language": "",             # 첫 실행에서 시스템 언어로 채워짐 / ko, en
    "interpolation": "LANCZOS",
    "fit_mode": "fit",          # fit / width / original
    "wheel_mode": "navigate",   # navigate: 휠=이동+Ctrl+휠=줌 / zoom: 휠=줌+Ctrl+휠=이동
    "bg_color": "black",        # black / darkgray / white
    "slider_mode": "auto",      # auto: 마우스를 아래로 내리면 표시 / always: 항상 표시 / never: 표시 안 함
    "end_behavior": "loop",     # loop: 처음/끝에서 반복 / stop: 처음/끝에서 멈춤 / next_folder: 다음 항목(폴더·압축파일)으로 이동
    "next_folder_sort": "name_asc",  # name_asc / name_desc / mtime_asc / mtime_desc
    "shortcuts": {},            # action_id -> key_id (예: "rotate": "r", "settings": "control-s")
    "window_geometry": "",      # 마지막 창 위치/크기 (예: 1000x720+780+360)
    "window_mode": "normal",    # normal / maximized / fullscreen
}
BG_COLORS = {"black": "#000000", "darkgray": "#1a1a1a", "white": "#ffffff"}
CHROME_HEIGHT = 38
CHROME_BG = "#1e1e1e"
CHROME_FG = "#e8e8e8"
CHROME_HOVER = "#3a3a3a"


def load_settings():
    data = dict(DEFAULT_SETTINGS)
    try:
        raw = json.loads(settings_path().read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for k, v in raw.items():
                if k in data:
                    data[k] = v
    except Exception:
        pass
    # 유효성 보정
    if data.get("interpolation", "").upper() not in [n for n, _f, _d in INTERPOLATIONS]:
        data["interpolation"] = "LANCZOS"
    if data.get("fit_mode") not in ("fit", "width", "original"):
        data["fit_mode"] = "fit"
    if data.get("wheel_mode") not in ("navigate", "zoom"):
        data["wheel_mode"] = "navigate"
    if data.get("bg_color") not in BG_COLORS:
        data["bg_color"] = "black"
    if data.get("slider_mode") not in ("auto", "always", "never"):
        data["slider_mode"] = "auto"
    if data.get("end_behavior") not in ("loop", "stop", "next_folder"):
        data["end_behavior"] = "loop"
    if data.get("next_folder_sort") not in ("name_asc", "name_desc", "mtime_asc", "mtime_desc"):
        data["next_folder_sort"] = "name_asc"
    if data.get("window_mode") not in ("normal", "maximized", "fullscreen"):
        data["window_mode"] = "normal"
    if not isinstance(data.get("window_geometry"), str):
        data["window_geometry"] = ""
    raw_shortcuts = data.get("shortcuts")
    if not isinstance(raw_shortcuts, dict):
        data["shortcuts"] = {}
    else:
        data["shortcuts"] = {
            str(k): str(v) for k, v in raw_shortcuts.items()
            if isinstance(k, str) and isinstance(v, str) and v
        }
    return data


def save_settings(data):
    try:
        settings_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def viewed_folders_path():
    # settings.json과 같은 위치에 저장
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "viewed_folders.json"
    return Path(__file__).resolve().parent / "viewed_folders.json"


def load_viewed_folders():
    try:
        raw = json.loads(viewed_folders_path().read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    out = []
    seen = set()
    for p in raw:
        if not isinstance(p, str) or not p:
            continue
        key = os.path.normcase(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def save_viewed_folders(paths):
    try:
        viewed_folders_path().write_text(
            json.dumps(paths, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log_error("viewed folders save failed: %s" % e)


def remember_viewed_folder(folder):
    # 최근에 본 폴더/압축파일을 맨 앞에 둔다. 같은 항목은 한 번만.
    try:
        p = str(Path(folder).resolve())
    except Exception:
        return
    key = os.path.normcase(p)
    paths = load_viewed_folders()
    if paths and os.path.normcase(paths[0]) == key:
        # 이미 맨 앞이면 파일을 다시 쓰지 않는다 (키 반복 시 불필요한 I/O 방지)
        return
    paths = [x for x in paths if os.path.normcase(x) != key]
    paths.insert(0, p)
    save_viewed_folders(paths)


def _path_key(path):
    try:
        return os.path.normcase(str(Path(path).resolve()))
    except Exception:
        return os.path.normcase(str(path))


def _path_is_under(child, parent):
    # 대소문자/구분자 차이를 무시하고 child가 parent 안(또는 같음)인지 확인
    c = _path_key(child).rstrip("\\/")
    p = _path_key(parent).rstrip("\\/")
    return c == p or c.startswith(p + os.sep)


def drop_nested_paths(paths):
    # 조상과 자손을 함께 선택해도 조상만 남긴다 (자손은 어차피 함께 삭제됨).
    kept = []
    for raw in sorted(paths, key=lambda x: len(Path(x).parts)):
        if any(_path_is_under(raw, k) for k in kept):
            continue
        kept.append(raw)
    return kept


def prune_viewed_folders(deleted):
    keep = []
    for p in load_viewed_folders():
        if any(_path_is_under(p, d) for d in deleted):
            continue
        keep.append(p)
    save_viewed_folders(keep)


def _shell_folder_guards():
    # Windows 기본 폴더(바탕화면/문서/다운로드/사진 등)는 통째로 삭제하지 못하게 한다.
    guards = []
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                for name in ("Desktop", "Personal", "My Pictures", "My Video", "My Music",
                             "{374DE290-123F-4565-9164-39C4925E467B}"):
                    try:
                        val, _ = winreg.QueryValueEx(key, name)
                    except OSError:
                        continue
                    if not isinstance(val, str):
                        continue
                    g = Path(os.path.expandvars(val))
                    if g.is_absolute():
                        guards.append(g)
        except OSError:
            pass
    # 레지스트리를 못 읽는 환경을 위한 보조
    for name in ("Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music"):
        guards.append(Path.home() / name)
    return guards


def nav_kind(path):
    # 이동 종류: 폴더는 폴더끼리, 압축파일은 압축파일끼리만 이웃이 된다.
    try:
        p = Path(path)
    except Exception:
        return "dir"
    return "archive" if p.suffix.lower() in ARCHIVE_EXTS else "dir"


def nav_siblings(root, sort_mode="name_asc", kind=None):
    # 이동 범위 안의 후보. kind를 주면 같은 종류만 (dir/archive).
    try:
        entries = [p for p in Path(root).iterdir()
                   if p.is_dir() or p.suffix.lower() in ARCHIVE_EXTS]
    except Exception:
        return []
    if kind is not None:
        entries = [p for p in entries if nav_kind(p) == kind]

    def mtime(p):
        try:
            return p.stat().st_mtime
        except OSError:
            return 0

    if sort_mode == "name_desc":
        entries.sort(key=lambda p: p.name.lower(), reverse=True)
    elif sort_mode == "mtime_asc":
        entries.sort(key=lambda p: (mtime(p), p.name.lower()))
    elif sort_mode == "mtime_desc":
        entries.sort(key=lambda p: (-mtime(p), p.name.lower()))
    else:  # name_asc
        entries.sort(key=lambda p: p.name.lower())
    return [str(p.resolve()) for p in entries]


def deletion_block_reason(path):
    # 실제 삭제 전 안전 검사. 이유가 있으면 문자열, 허용이면 None.
    try:
        p = Path(path).resolve()
    except Exception:
        return tr("경로를 확인할 수 없습니다.")
    if not p.exists():
        return tr("경로가 존재하지 않습니다.")
    if not p.is_dir() and p.suffix.lower() not in ARCHIVE_EXTS:
        return tr("폴더나 압축파일만 삭제할 수 있습니다.")
    if p.parent == p:
        return tr("드라이브 루트는 삭제할 수 없습니다.")
    app_dir = (Path(sys.executable).parent if getattr(sys, "frozen", False)
               else Path(__file__).resolve().parent)
    # 홈은 '홈 자체/홈의 상위'만 막고, 홈 안의 사진 폴더는 허용한다.
    if _path_is_under(Path.home(), p):
        return tr("사용자 홈 폴더는 삭제할 수 없습니다.")
    if _path_is_under(p, app_dir) or _path_is_under(app_dir, p):
        return tr("프로그램 폴더는 삭제할 수 없습니다.")
    protected = []
    for env in ("WINDIR", "ProgramFiles", "ProgramFiles(x86)", "ProgramData",
                "APPDATA", "LOCALAPPDATA"):
        val = os.environ.get(env)
        if val:
            protected.append(Path(val))
    for g in protected:
        if _path_is_under(p, g) or _path_is_under(g, p):
            return tr("시스템 폴더는 삭제할 수 없습니다.")
    for g in _shell_folder_guards():
        if _path_key(p) == _path_key(g):
            return tr("Windows 기본 폴더는 삭제할 수 없습니다.")
    return None


def move_to_recycle_bin(path, owner=None):
    # Windows 셸의 휴지통 이동 API. 실패하면 (False, 이유)를 돌려준다.
    if os.name != "nt":
        return False, tr("휴지통 이동은 Windows에서만 지원합니다.")
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    # shortcut: SHFileOperation는 MAX_PATH(260자)에 가까운 경로에서 실패할 수 있다.
    # 그런 경로가 실제로 문제가 되면 IFileOperation(COM)으로 교체한다.
    buf = ctypes.create_unicode_buffer(str(path) + "\0")
    op = SHFILEOPSTRUCTW()
    op.hwnd = owner or None
    op.wFunc = 3  # FO_DELETE
    op.pFrom = ctypes.cast(buf, wintypes.LPCWSTR)
    op.pTo = None
    # ALLOWUNDO(휴지통) | NOCONFIRMATION(자체 확인창 사용) | WANTNUKEWARNING(영구 삭제 경고)
    op.fFlags = 0x0040 | 0x0010 | 0x4000
    try:
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    except Exception as e:
        return False, str(e)
    if res != 0:
        return False, tr("Windows 오류 0x%X") % res
    if op.fAnyOperationsAborted:
        return False, tr("취소되었습니다.")
    return True, None


def load_interp_index():
    data = load_settings()
    name = str(data.get("interpolation", "LANCZOS")).upper()
    for i, (n, _f, _d) in enumerate(INTERPOLATIONS):
        if n == name:
            return i
    return DEFAULT_INTERP


class Viewer(tk.Tk):
    def __init__(self, start_path=None):
        super().__init__()
        self.overrideredirect(True)
        # 시작 시 CWD를 프로그램 폴더로 옮겨둔다.
        # 탐색기 더블클릭 시 CWD가 이미지 폴더일 수 있는데, 그러면
        # 그 폴더를 목록에서 삭제할 때 윈도우가 CWD를 잠가 막는다.
        # CWD만 미리 옮겨서 회피한다.
        try:
            _safe = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
            os.chdir(str(_safe))
        except Exception:
            pass
        self.settings = load_settings()
        lang = self.settings.get("language")
        if lang not in ("ko", "en"):
            # 언어는 첫 실행에서만 시스템 설정을 따른다. 이후에는 설정 창에서만 변경.
            lang = detect_system_language()
            self.settings["language"] = lang
            save_settings(self.settings)
        set_language(lang)
        self._shortcuts = dict(SHORTCUT_DEFAULTS)
        stored_shortcuts = self.settings.get("shortcuts", {})
        if isinstance(stored_shortcuts, dict):
            for _action in SHORTCUT_DEFAULTS:
                _val = stored_shortcuts.get(_action)
                if isinstance(_val, str) and _val:
                    self._shortcuts[_action] = _val
        self._rebuild_shortcut_map()
        # 폴더 이동 토스트 팝업 상태
        self._toast = None
        self._toast_after = None
        self._toast_label = None
        self.title(tr("달빛뷰어"))
        self.minsize(560, 320)
        self._apply_window_icon()
        bg = BG_COLORS.get(self.settings.get("bg_color", "black"), "#000000")
        self.configure(bg=bg)
        # 테두리 없는 자체 제목 표시줄. 전체화면은 Win32 창 크기/최상위로 처리한다.
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # 지난번 창 위치/크기를 기억했다가 복원. 없으면 작은 창으로 시작.
        saved_geo = self._saved_window_geometry()
        if saved_geo:
            self._window_geometry = saved_geo
        else:
            start_w = min(1000, max(640, int(sw * 0.55)))
            start_h = min(720, max(480, int(sh * 0.55)))
            self._window_geometry = "%dx%d+%d+%d" % (
                start_w, start_h, max(0, (sw - start_w) // 2), max(0, (sh - start_h) // 2))
        self.geometry(self._window_geometry)
        try:
            self.attributes("-topmost", False)
        except tk.TclError:
            pass
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        # 방향키 패닝 1회 이동량 (px)
        self.canvas.configure(xscrollincrement=60, yscrollincrement=60)
        self.canvas.pack(fill="both", expand=True)

        self.items = []  # [{name, path, arc, arc_name}]
        self.index = -1
        self.zoom = 1.0
        self.fit_mode = self.settings.get("fit_mode", "fit")  # fit / width / original / zoom
        self.interp_idx = load_interp_index()
        self.wheel_mode = self.settings.get("wheel_mode", "navigate")
        self.slider_mode = self.settings.get("slider_mode", "auto")
        self.end_behavior = self.settings.get("end_behavior", "loop")
        self.next_folder_sort = self.settings.get("next_folder_sort", "name_asc")
        self._current_dir = None
        self._nav_root = None  # 다음 폴더 이동 범위: 처음 연 폴더의 부모. 이 밖으로는 절대 안 올라감.
        self._photo = None
        self._canvas_image_id = None
        self._anim_after = None
        self._anim_im = None
        self._anim_frame = 0
        self._anim_loops_done = 0
        self._anim_total = 0
        self._anim_plays = 0
        self._anim_done = False
        self._anim_bar_visible = False
        self._cache = {}
        self._drag = None
        self._last_error = None
        self._render_after = None
        self._fast_nav = False
        self._disp_size = (0, 0)
        self._need_center = False
        self._edge_armed = {}
        self._edge_released = {}
        self._cursor_hide_after = None
        self._cursor_hidden = False
        self._modal_open = False
        self._fit_var = tk.StringVar(value=self.fit_mode)
        self._slider_updating = False
        self._slider_target = None
        self._slider_visible = False
        self._hide_bar_after = None
        self._chrome_visible = False
        self._chrome_hide_after = None
        self._file_dropdown = None
        self._tooltip = None
        self._keep_topmost_windowed = False
        self._suppress_topmost_drop = False
        self._fullscreen = False
        self._maximized = False
        self._drag_offset = None
        self._resize_origin = None
        self._edge_cursor_value = ""

        self._build_bottom_bar()
        self._build_anim_bar()
        self._build_chrome()
        self._bind_keys()
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<Motion>", self._on_mouse_move)
        # 창 가장자리에서 8방향 크기 조절. 위젯 없이 좌표로만 판정한다.
        for w in (self, self.canvas, self._chrome):
            w.bind("<Motion>", self._on_edge_motion, add="+")
            w.bind("<ButtonPress-1>", self._resize_start, add="+")
            w.bind("<B1-Motion>", self._resize_move, add="+")
            w.bind("<ButtonRelease-1>", self._resize_end, add="+")
        # 테두리 없는 창을 작업 표시줄/Alt+Tab에 등록하고 전체화면 크기로 고정
        self.update_idletasks()
        self.after(0, self._init_native_window)

        # 시작 경로: 명령줄 인자 > 없으면 아이콘 시작 화면
        target = start_path or (sys.argv[1] if len(sys.argv) > 1 else None)
        if target:
            if not self._load_path(target):
                # 탐색기 연결로 실행했는데 초기 화면만 뜨는 경우의 대부분은
                # 여기서 걸린다: 구버전 EXE(인자 무시) 또는 지원하지 않는 포맷.
                self._show_load_error(target)
                self._show_welcome() or self._open_dialog_or_quit()
        else:
            if not self._show_welcome():
                self._open_dialog_or_quit()
        self._redraw()
        self._apply_slider_mode()
        # 시작 후 2초간 움직임 없으면 커서 숨김
        self._reset_cursor_timer()
        self._destroyed = False

    def _saved_window_geometry(self):
        # settings.json에 저장된 마지막 창 위치/크기. 형식이 깨졌거나 화면 밖이면 None.
        geo = str(self.settings.get("window_geometry") or "")
        m = re.match(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$", geo)
        if not m:
            return None
        w, h, x, y = (int(v) for v in m.groups())
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(560, min(w, sw))
        h = max(320, min(h, sh))
        # 모니터 구성이 바뀌어 창이 화면 밖으로 완전히 나간 경우는 가운데로.
        if x + w < 80 or y + 40 < 0 or x > sw - 80 or y > sh - 40:
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
        return "%dx%d+%d+%d" % (w, h, x, y)

    def _save_window_state(self):
        # 종료 시 마지막 창 상태를 저장한다. 전체화면/최대화였으면 그 사실도 함께.
        try:
            if self._is_fullscreen():
                mode = "fullscreen"
            elif self._maximized:
                mode = "maximized"
            else:
                mode = "normal"
            geo = self._window_geometry if mode != "normal" else self.geometry()
            data = load_settings()
            data["window_geometry"] = geo or ""
            data["window_mode"] = mode
            save_settings(data)
        except Exception:
            pass

    def _apply_window_icon(self):
        # 창/작업 표시줄 아이콘. EXE에는 아이콘이 내장되지만 Tk 창에는 직접 지정해야 한다.
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) \
            else Path(__file__).resolve().parent
        for name in ("icon.ico", "icon.png"):
            p = base / name
            if not p.exists():
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    p = Path(meipass) / name
            if not p.exists():
                continue
            try:
                if p.suffix.lower() == ".ico":
                    self.iconbitmap(str(p))
                else:
                    # 창 아이콘은 ico만 받으므로 PNG에서 임시 ico를 만든다.
                    tmp = Path(tempfile.gettempdir()) / "dalbit_window_icon.ico"
                    img = Image.open(p).convert("RGBA")
                    img.save(tmp, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
                    self.iconbitmap(str(tmp))
                self._window_icon_photo = ImageTk.PhotoImage(
                    Image.open(p).convert("RGBA"), master=self)
                self.iconphoto(False, self._window_icon_photo)
                return
            except Exception:
                continue

    def _welcome_image_path(self):
        # 시작 화면에 쓸 아이콘. EXE는 빌드 시 함께 넣은 파일을 찾는다.
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).parent / "icon.png")
            if getattr(sys, "_MEIPASS", None):
                candidates.append(Path(sys._MEIPASS) / "icon.png")
        candidates.append(Path(__file__).resolve().parent / "icon.png")
        for c in candidates:
            if c.exists():
                return c
        return None

    def _show_welcome(self):
        # 이미지 없이 실행했을 때 기본 아이콘 화면을 띄운다. 설정/연결 등록을 바로 할 수 있다.
        path = self._welcome_image_path()
        if path is None:
            return False
        try:
            icon = Image.open(path)
            icon.load()
        except Exception:
            return False
        self._welcome_icon = icon.convert("RGBA")
        self._draw_welcome()
        return True

    def _draw_welcome(self):
        self._stop_animation()
        self._canvas_image_id = None
        icon = getattr(self, "_welcome_icon", None)
        if icon is None:
            return
        try:
            cw = self.canvas.winfo_width() or self.winfo_screenwidth()
            ch = self.canvas.winfo_height() or self.winfo_screenheight()
            if cw <= 1 or ch <= 1:
                return
            side = max(64, int(min(cw, ch) * 0.45))
            scale = side / max(icon.width, icon.height)
            w = max(1, int(icon.width * scale))
            h = max(1, int(icon.height * scale))
            scaled = icon.resize((w, h), Image.LANCZOS)
            bg = BG_COLORS.get(self.settings.get("bg_color", "black"), "#000000")
            canvas_img = Image.new("RGBA", (cw, ch), bg)
            canvas_img.paste(scaled, ((cw - w) // 2, (ch - h) // 2), scaled)
            self._welcome_photo = ImageTk.PhotoImage(canvas_img.convert("RGB"),
                                                     master=self.canvas)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self._welcome_photo,
                                     anchor="center")
            self.canvas.config(scrollregion=(0, 0, cw, ch))
        except Exception:
            pass

    def _on_canvas_configure(self, event=None):
        if self.items:
            self._redraw()
        else:
            self._draw_welcome()

    def destroy(self):
        # 종료 시 타이머/토스트 정리
        if not getattr(self, "_destroyed", False):
            self._destroyed = True
            self._save_window_state()
            self._cancel_scheduled_redraw()
            self._stop_animation()
            self._hide_tooltip()
            self._close_file_menu()
            self._cancel_chrome_hide()
            try:
                self._hide_folder_toast()
            except Exception:
                pass
            try:
                if getattr(self, "_cursor_hide_after", None) is not None:
                    self.after_cancel(self._cursor_hide_after)
            except Exception:
                pass
        try:
            super().destroy()
        except Exception:
            pass

    # ---------- 키 / 마우스 (화면에 아무것도 띄우지 않음) ----------
    def _bind_keys(self):
        # 종료: Esc. 모달 창이나 단축키 입력 중에는 그 창이 Esc를 먼저 처리한다.
        self.bind("<Escape>", self._on_escape_main)
        # 방향키: 확대 시에는 화면 스크롤(패닝), 끝에서 한 번 더 누르면 이전/다음
        # 축소/맞춤 상태(스크롤 불가)에서는 바로 이전/다음으로 이동
        self.bind("<Left>", lambda e: self._pan_or_navigate(-1, 0))
        self.bind("<Right>", lambda e: self._pan_or_navigate(1, 0))
        self.bind("<Up>", lambda e: self._pan_or_navigate(0, -1))
        self.bind("<Down>", lambda e: self._pan_or_navigate(0, 1))
        # WASD = 방향키와 동일
        self.bind("<Key-a>", lambda e: self._pan_or_navigate(-1, 0))
        self.bind("<Key-A>", lambda e: self._pan_or_navigate(-1, 0))
        self.bind("<Key-d>", lambda e: self._pan_or_navigate(1, 0))
        self.bind("<Key-D>", lambda e: self._pan_or_navigate(1, 0))
        self.bind("<Key-w>", lambda e: self._pan_or_navigate(0, -1))
        self.bind("<Key-W>", lambda e: self._pan_or_navigate(0, -1))
        self.bind("<Key-s>", lambda e: self._pan_or_navigate(0, 1))
        self.bind("<Key-S>", lambda e: self._pan_or_navigate(0, 1))
        # 키 뗌 감지: 끝에서 대기 중이던 방향은 뗐다가 다시 눌러야 이동
        self.bind("<KeyRelease-Left>", lambda e: self._on_pan_key_release(-1, 0))
        self.bind("<KeyRelease-Right>", lambda e: self._on_pan_key_release(1, 0))
        self.bind("<KeyRelease-Up>", lambda e: self._on_pan_key_release(0, -1))
        self.bind("<KeyRelease-Down>", lambda e: self._on_pan_key_release(0, 1))
        self.bind("<KeyRelease-a>", lambda e: self._on_pan_key_release(-1, 0))
        self.bind("<KeyRelease-A>", lambda e: self._on_pan_key_release(-1, 0))
        self.bind("<KeyRelease-d>", lambda e: self._on_pan_key_release(1, 0))
        self.bind("<KeyRelease-D>", lambda e: self._on_pan_key_release(1, 0))
        self.bind("<KeyRelease-w>", lambda e: self._on_pan_key_release(0, -1))
        self.bind("<KeyRelease-W>", lambda e: self._on_pan_key_release(0, -1))
        self.bind("<KeyRelease-s>", lambda e: self._on_pan_key_release(0, 1))
        self.bind("<KeyRelease-S>", lambda e: self._on_pan_key_release(0, 1))
        # 고정 보조 페이지 키 (PageUp/PageDown은 고정, 나머지는 위 설정 가능)
        self.bind("<Prior>", lambda e: self._key_navigate(self.prev))
        self.bind("<Next>", lambda e: self._key_navigate(self.next))
        self.bind("<space>", lambda e: self._key_navigate(self.next))
        self.bind("<BackSpace>", lambda e: self._key_navigate(self.prev))
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Home>", lambda e: self.goto(0))
        self.bind("<End>", lambda e: self.goto(len(self.items) - 1))
        # 고정 보조 전체화면 키 (F/F11은 제거, Alt+Enter만 사용)
        self.bind("<Alt-Return>", lambda e: self.toggle_fullscreen())
        self.bind("<Alt-KP_Enter>", lambda e: self.toggle_fullscreen())
        # 고정 보조 파일 열기
        self.bind("<Control-o>", lambda e: self._open_dialog_or_quit())
        self.bind("<Control-O>", lambda e: self._open_dialog_or_quit())
        # 사용자 설정 단축키 디스패처
        self.bind("<KeyPress>", self._on_shortcut_key)
        self.bind("<KeyRelease>", lambda e: self._end_fast_nav())

        # 마우스: 휠 동작은 설정(wheel_mode)에 따름. 기본 navigate: 휠=이동, Ctrl+휠=줌
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._on_button_wheel(-1, e))
        self.canvas.bind("<Button-5>", lambda e: self._on_button_wheel(1, e))
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        self.canvas.bind("<ButtonPress-1>", self._pan_start)
        self.canvas.bind("<B1-Motion>", self._pan_move)
        self.canvas.bind("<Double-Button-1>", lambda e: self._toggle_fit_original())
        self.bind("<Button-1>", self._on_global_click, add="+")

    def _rebuild_shortcut_map(self):
        self._shortcut_map = {}
        for action, key in self._shortcuts.items():
            if isinstance(key, str) and key:
                self._shortcut_map[key] = action

    def _on_shortcut_key(self, event):
        key_id = normalize_key_id(event)
        if not key_id:
            return None
        action = getattr(self, "_shortcut_map", {}).get(key_id)
        if action is None:
            return None
        self._run_shortcut(action)
        return "break"

    def _on_escape_main(self, event=None):
        # 설정/목록 창이 열려 있으면 메인 창의 Esc 종료를 막는다.
        if self._modal_open:
            return
        if self._file_dropdown is not None:
            self._close_file_menu()
            return
        self.destroy()

    def _on_focus_out(self, event=None):
        self._end_fast_nav()
        if (getattr(self, "_keep_topmost_windowed", False)
                and not self._is_fullscreen()
                and not getattr(self, "_suppress_topmost_drop", False)):
            try:
                self.after(0, self._maybe_drop_topmost)
            except tk.TclError:
                pass

    def _maybe_drop_topmost(self):
        # 다른 앱으로 포커스가 넘어갔을 때만 topmost를 해제한다.
        if (not getattr(self, "_keep_topmost_windowed", False)
                or self._is_fullscreen()
                or getattr(self, "_suppress_topmost_drop", False)):
            return
        if self._foreground_is_ours():
            return
        self._keep_topmost_windowed = False
        self._win_set_topmost(False)

    def _foreground_is_ours(self):
        if os.name != "nt":
            try:
                return self.focus_get() is not None
            except tk.TclError:
                return True
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return False
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(
                hwnd, ctypes.byref(pid))
            return int(pid.value) == os.getpid()
        except Exception:
            return True

    def _run_shortcut(self, action):
        if action == "width":
            self.set_fit("width")
        elif action == "fit":
            self.set_fit("fit")
        elif action == "original":
            self.set_fit("original")
        elif action == "settings":
            self.open_settings_dialog()
        elif action == "viewed":
            self.open_viewed_folders_dialog()

    def toggle_fullscreen(self):
        self._hide_tooltip()
        if self._is_fullscreen():
            self._leave_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self):
        if self._is_fullscreen():
            return
        if not self._maximized:
            try:
                self._window_geometry = self.geometry()
            except tk.TclError:
                pass
        self._keep_topmost_windowed = False
        self._fullscreen = True
        try:
            self.state("normal")
        except tk.TclError:
            pass
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # Tk 창 크기까지 모니터 전체로 맞춰야 실제로 전체화면이 된다.
        self.geometry("%dx%d+0+0" % (sw, sh))
        self._apply_chrome_mode()
        self.update_idletasks()
        self._win_set_topmost(True)
        self._win_set_rect(0, 0, sw, sh, topmost=True)

    def _leave_fullscreen(self):
        if not self._is_fullscreen():
            return
        self._fullscreen = False
        self._win_set_topmost(False)
        if self._maximized:
            x, y, w, h = self._win_work_area()
            self._win_set_rect(x, y, w, h, topmost=False)
        else:
            self._restore_window_geometry()
            self._win_set_topmost(False)
        self._apply_chrome_mode()
        # 전체화면에서 돌아올 때 다른 창(게임 등) 뒤로 밀리지 않도록
        # 창을 앞에 올리고, 다른 앱을 클릭해 포커스를 잃을 때까지 topmost 유지.
        self._keep_topmost_windowed = True
        self._win_set_topmost(True)
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass
        hwnd = self._win_hwnd()
        if hwnd:
            try:
                import ctypes
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
            except Exception:
                pass

    def _restore_window_geometry(self):
        geo = getattr(self, "_window_geometry", None)
        if not geo:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = min(sw - 80, max(800, int(sw * 0.8)))
            h = min(sh - 80, max(600, int(sh * 0.8)))
            geo = "%dx%d+%d+%d" % (w, h, max(0, (sw - w) // 2),
                                   max(0, (sh - h) // 2))
        try:
            self.geometry(geo)
        except tk.TclError:
            pass

    def _is_fullscreen(self):
        return bool(getattr(self, "_fullscreen", False))

    def _win_hwnd(self):
        if os.name != "nt":
            return None
        try:
            import ctypes
            h = self.winfo_id()
            p = ctypes.windll.user32.GetParent(h)
            return p or h
        except Exception:
            return None

    def _init_native_window(self):
        self._win_appwindow()
        if self._is_fullscreen():
            self._win_set_rect(0, 0, self.winfo_screenwidth(),
                               self.winfo_screenheight(), topmost=True)
        try:
            self.state("normal")
            self.deiconify()
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass
        hwnd = self._win_hwnd()
        if hwnd:
            try:
                import ctypes
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
            except Exception:
                pass
        try:
            self.after(400, self._ensure_visible)
        except tk.TclError:
            pass
        # 지난번에 전체화면/최대화로 껐으면 같은 상태로 시작한다.
        mode = self.settings.get("window_mode", "normal")
        if mode == "fullscreen":
            self._enter_fullscreen()
        elif mode == "maximized":
            self._window_maximize()

    def _ensure_visible(self):
        try:
            if self.state() == "iconic":
                self.state("normal")
                self.deiconify()
                self.lift()
        except tk.TclError:
            pass
        hwnd = self._win_hwnd()
        if hwnd and not self._is_fullscreen():
            try:
                import ctypes
                user32 = ctypes.windll.user32
                if user32.GetForegroundWindow() != hwnd:
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
            except Exception:
                pass

    def _win_appwindow(self):
        h = self._win_hwnd()
        if not h:
            return
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            user32 = ctypes.windll.user32
            ex = user32.GetWindowLongW(h, GWL_EXSTYLE)
            user32.SetWindowLongW(h, GWL_EXSTYLE,
                                  (ex | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW)
        except Exception:
            pass

    def _win_set_rect(self, x, y, w, h, topmost=False):
        if os.name != "nt":
            try:
                self.geometry("%dx%d+%d+%d" % (w, h, x, y))
                self.attributes("-topmost", bool(topmost))
            except tk.TclError:
                pass
            return
        hwnd = self._win_hwnd()
        if not hwnd:
            return
        try:
            import ctypes
            SWP_SHOWWINDOW = 0x0040
            HWND_TOPMOST = -1
            HWND_TOP = 0
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST if topmost else HWND_TOP,
                int(x), int(y), int(w), int(h), SWP_SHOWWINDOW)
        except Exception:
            pass

    def _win_set_topmost(self, topmost):
        if os.name != "nt":
            try:
                self.attributes("-topmost", bool(topmost))
            except tk.TclError:
                pass
            return
        hwnd = self._win_hwnd()
        if not hwnd:
            return
        try:
            import ctypes
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                hwnd, -1 if topmost else -2, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception:
            pass

    def _win_minimize(self):
        if os.name == "nt":
            hwnd = self._win_hwnd()
            if hwnd:
                try:
                    import ctypes
                    ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                    return
                except Exception:
                    pass
        try:
            self.iconify()
        except tk.TclError:
            pass

    def _win_work_area(self):
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes
                class RECT(ctypes.Structure):
                    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]
                r = RECT()
                if ctypes.windll.user32.SystemParametersInfoW(
                        0x0030, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
                    return r.left, r.top, r.right - r.left, r.bottom - r.top
            except Exception:
                pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def _chrome_button(self, parent, text, command, width=None, danger=False):
        b = tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                      highlightthickness=0, bg=CHROME_BG, fg=CHROME_FG,
                      activebackground="#c42b1c" if danger else CHROME_HOVER,
                      activeforeground="#ffffff", font=("맑은 고딕", 10),
                      padx=8, pady=0)
        if width:
            b.configure(width=width)
        hover = "#c42b1c" if danger else CHROME_HOVER
        b.bind("<Enter>", lambda e: b.configure(bg=hover))
        b.bind("<Leave>", lambda e: b.configure(bg=CHROME_BG))
        return b

    def _build_chrome(self):
        self._chrome = tk.Frame(self, bg=CHROME_BG, height=CHROME_HEIGHT)
        self._chrome.pack_propagate(False)
        self._chrome.bind("<ButtonPress-1>", self._chrome_drag_start)
        self._chrome.bind("<B1-Motion>", self._chrome_drag_move)
        self._chrome.bind("<Double-Button-1>", lambda e: self._window_maximize())

        self._file_btn = self._chrome_button(self._chrome, tr("파일 ▾"), self._show_file_menu)
        self._file_btn.pack(side="left", fill="y")

        self._settings_btn = self._chrome_button(self._chrome, tr("설정(Settings)"),
                                                 self.open_settings_dialog)
        self._settings_btn.pack(side="left", fill="y")

        right = tk.Frame(self._chrome, bg=CHROME_BG)
        right.pack(side="right", fill="y")
        self._fs_btn = self._chrome_button(right, "⛶", self.toggle_fullscreen, width=3)
        self._min_btn = self._chrome_button(right, "—", self._window_minimize, width=3)
        self._max_btn = self._chrome_button(right, "□", self._window_maximize, width=3)
        self._close_btn = self._chrome_button(right, "✕", self._window_close,
                                              width=3, danger=True)
        self._fs_btn.pack(side="left", fill="y")
        self._min_btn.pack(side="left", fill="y")
        self._max_btn.pack(side="left", fill="y")
        self._close_btn.pack(side="left", fill="y")

        def tip(btn, text_fn):
            btn.bind("<Enter>", lambda e, b=btn: self._show_tooltip(b, text_fn()),
                     add="+")
            btn.bind("<Leave>", lambda e: self._hide_tooltip(), add="+")

        tip(self._fs_btn, lambda: tr("창모드 (Alt+Enter)" if self._is_fullscreen()
                                     else "전체화면 (Alt+Enter)"))
        tip(self._min_btn, lambda: tr("최소화"))
        tip(self._max_btn, lambda: tr("이전 크기로" if (self._maximized
                                                       and not self._is_fullscreen())
                                      else "최대화"))
        tip(self._close_btn, lambda: tr("닫기"))

        self._apply_chrome_mode()

    def _retranslate_chrome(self):
        try:
            self.title(tr("달빛뷰어"))
            self._file_btn.configure(text=tr("파일 ▾"))
            self._settings_btn.configure(text=tr("설정(Settings)"))
        except tk.TclError:
            pass

    def _show_file_menu(self):
        if self._file_dropdown is not None:
            self._close_file_menu()
            return
        self._cancel_chrome_hide()
        frame = tk.Frame(self, bg="#2a2a2a", bd=1, relief="solid")

        def choose(fn):
            self._close_file_menu()
            fn()

        def add_item(label, fn):
            b = self._chrome_button(frame, label, lambda: choose(fn))
            b.configure(anchor="w", padx=10, pady=6)
            b.pack(fill="x")

        add_item(tr("파일 열기...  (O)"), self._open_dialog_or_quit)
        add_item(tr("압축파일 열기...  (ZIP/CBZ)"), self.open_archive_dialog)
        tk.Frame(frame, bg="#444444", height=1).pack(fill="x", padx=6, pady=4)
        add_item(tr("열람한 폴더 목록...  (L)"), self.open_viewed_folders_dialog)

        frame.update_idletasks()
        w = frame.winfo_reqwidth()
        h = frame.winfo_reqheight()
        x = max(0, self._file_btn.winfo_rootx() - self.winfo_rootx())
        try:
            frame.place(x=x, y=CHROME_HEIGHT, width=w, height=h)
            frame.lift()
        except tk.TclError:
            frame.destroy()
            return
        self._file_dropdown = frame

    def _set_file_association(self, enabled, parent=None):
        # 탐색기 연결을 앱 안에서 켜고 끈다. 레지스트리는 HKCU만 사용해 관리자 권한이 필요 없다.
        owner = parent or self
        if not getattr(sys, "frozen", False):
            messagebox.showinfo(
                tr("탐색기 연결"),
                tr("EXE로 실행할 때만 등록할 수 있습니다.\n\n"
                   "릴리스 ZIP에서 DalbitViewer.exe를 실행한 뒤 다시 시도하세요."),
                parent=owner)
            return
        try:
            if enabled:
                ok = register_file_association(quiet=True) == 0
                msg = ("압축파일 우클릭 메뉴에 '달빛뷰어로 열기'를 등록했습니다.")
            else:
                ok = unregister_file_association(quiet=True) == 0
                msg = ("탐색기 연결을 해제했습니다.\n기존 압축 프로그램의 연결은 그대로 유지됩니다.")
            messagebox.showinfo(tr("탐색기 연결"),
                                tr(msg) if ok else tr("작업을 완료하지 못했습니다."),
                                parent=owner)
        except tk.TclError:
            pass

    def _close_file_menu(self):
        frame = getattr(self, "_file_dropdown", None)
        self._file_dropdown = None
        if frame is not None:
            try:
                frame.destroy()
            except tk.TclError:
                pass
        self._schedule_chrome_hide()

    def _on_global_click(self, event):
        frame = self._file_dropdown
        if frame is None:
            return
        try:
            w = event.widget
            path = str(w)
            if w is frame or path.startswith(str(frame) + "."):
                return
            if w is self._file_btn or path.startswith(str(self._file_btn) + "."):
                return
        except Exception:
            pass
        self._close_file_menu()

    def _chrome_drag_start(self, event):
        if self._is_fullscreen() or self._maximized:
            self._drag_offset = None
            return
        # 창 최상단 6px는 리사이즈 영역. 이동과 동시에 걸리는 떨림을 막는다.
        if self._edge_at(event.x_root - self.winfo_rootx(),
                         event.y_root - self.winfo_rooty()):
            self._drag_offset = None
            return
        self._drag_offset = (event.x_root - self.winfo_x(),
                             event.y_root - self.winfo_y())

    def _chrome_drag_move(self, event):
        if self._is_fullscreen() or self._maximized or not self._drag_offset:
            return
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        try:
            self.geometry("+%d+%d" % (x, y))
        except tk.TclError:
            pass

    def _resize_start(self, event):
        if self._is_fullscreen() or self._maximized:
            self._resize_origin = None
            return None
        edge = getattr(event.widget, "_edge", None)
        if not edge:
            edge = self._edge_at(event.x_root - self.winfo_rootx(),
                                 event.y_root - self.winfo_rooty())
        if not edge:
            self._resize_origin = None
            return None
        self._resize_origin = (event.x_root, event.y_root,
                               self.winfo_x(), self.winfo_y(),
                               self.winfo_width(), self.winfo_height())
        self._resize_edge = edge
        # 창 크기 조절 중에는 보간 없이(NEAREST) 그려서 드래그가 끊기지 않게 한다.
        self._fast_nav = True
        return "break"

    def _resize_move(self, event):
        if self._is_fullscreen() or not getattr(self, "_resize_origin", None):
            return None
        x0, y0, wx, wy, w0, h0 = self._resize_origin
        dx = event.x_root - x0
        dy = event.y_root - y0
        edge = getattr(self, "_resize_edge", "se")
        min_w, min_h = 560, 320

        w, h = w0, h0
        nx, ny = wx, wy
        if "e" in edge:
            w = max(min_w, w0 + dx)
        if "w" in edge:
            w = max(min_w, w0 - dx)
            nx = wx + (w0 - w)
        if "s" in edge:
            h = max(min_h, h0 + dy)
        if "n" in edge:
            h = max(min_h, h0 - dy)
            ny = wy + (h0 - h)

        if (nx, ny, w, h) == (wx, wy, w0, h0):
            return "break"
        try:
            self.geometry("%dx%d+%d+%d" % (w, h, nx, ny))
        except tk.TclError:
            return "break"
        return "break"

    def _resize_end(self, event=None):
        self._resize_origin = None
        self._end_fast_nav()

    def _bg_color(self):
        return BG_COLORS.get(self.settings.get("bg_color", "black"), "#000000")

    def _edge_at(self, x, y):
        # 창 좌표로 가장자리 판정. 위젯을 깔지 않아 화면에 아무것도 그리지 않는다.
        if self._is_fullscreen() or self._maximized:
            return None
        t = 6
        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except tk.TclError:
            return None
        if w <= 1 or h <= 1:
            return None
        left = x <= t
        right = x >= w - t
        top = y <= t
        bottom = y >= h - t
        if not (left or right or top or bottom):
            return None
        vertical = "n" if top else ("s" if bottom else "")
        horizontal = "w" if left else ("e" if right else "")
        return (vertical + horizontal) or None

    def _edge_cursor(self, edge):
        if edge in ("n", "s"):
            return "size_ns"
        if edge in ("w", "e"):
            return "size_we"
        if edge in ("nw", "se"):
            return "size_nw_se"
        if edge in ("ne", "sw"):
            return "size_ne_sw"
        return ""

    def _on_edge_motion(self, event):
        if self._resize_origin is not None:
            return
        edge = self._edge_at(event.x_root - self.winfo_rootx(),
                             event.y_root - self.winfo_rooty())
        cursor = self._edge_cursor(edge) if edge else ""
        try:
            if self._edge_cursor_value != cursor:
                self.configure(cursor=cursor or "")
                self.canvas.configure(cursor=cursor or "")
                self._edge_cursor_value = cursor
        except tk.TclError:
            pass

    def _apply_chrome_mode(self):
        if not hasattr(self, "_chrome"):
            return
        self._cancel_chrome_hide()
        self._hide_tooltip()
        if self._is_fullscreen():
            try:
                self._chrome.pack_forget()
            except tk.TclError:
                pass
            try:
                self._chrome.place_forget()
            except tk.TclError:
                pass
            self._chrome_visible = False
        else:
            try:
                self._chrome.place_forget()
            except tk.TclError:
                pass
            self._chrome.pack(side="top", fill="x", before=self.canvas)
            self._chrome_visible = True
        self._sync_chrome()

    def _sync_chrome(self):
        try:
            self._fs_btn.configure(
                text="❐" if self._is_fullscreen() else "⛶")
            self._max_btn.configure(
                text="▣" if (self._maximized and not self._is_fullscreen()) else "□")
        except tk.TclError:
            pass

    def _show_tooltip(self, widget, text):
        self._hide_tooltip()
        try:
            tip = tk.Toplevel(self)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.attributes("-alpha", 1.0)
            tip.configure(bg=CHROME_BG)
            tk.Label(tip, text=text, bg=CHROME_BG, fg=CHROME_FG,
                     padx=8, pady=4, font=("맑은 고딕", 9)).pack()
            tip.update_idletasks()
            x = widget.winfo_rootx() + (widget.winfo_width() - tip.winfo_reqwidth()) // 2
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            tip.geometry("+%d+%d" % (max(0, x), y))
            self._tooltip = tip
        except tk.TclError:
            self._hide_tooltip()

    def _hide_tooltip(self):
        tip = getattr(self, "_tooltip", None)
        self._tooltip = None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass

    def _show_chrome(self):
        if not self._is_fullscreen():
            return
        self._cancel_chrome_hide()
        if not self._chrome_visible or self._chrome.winfo_manager() != "place":
            try:
                self._chrome.place(x=0, y=0, relwidth=1, height=CHROME_HEIGHT)
                self._chrome.lift()
            except tk.TclError:
                return
            self._chrome_visible = True
        self._keep_cursor_visible()

    def _hide_chrome(self):
        self._chrome_hide_after = None
        self._hide_tooltip()
        if not self._is_fullscreen() or self._file_dropdown is not None:
            return
        try:
            y = self.winfo_pointery() - self.winfo_rooty()
        except tk.TclError:
            y = CHROME_HEIGHT + 1
        if y <= CHROME_HEIGHT + 2:
            return
        try:
            self._chrome.place_forget()
        except tk.TclError:
            pass
        self._chrome_visible = False

    def _schedule_chrome_hide(self):
        if (not self._is_fullscreen() or not self._chrome_visible
                or self._file_dropdown is not None):
            return
        if self._chrome_hide_after is not None:
            return
        try:
            self._chrome_hide_after = self.after(350, self._hide_chrome)
        except tk.TclError:
            self._chrome_hide_after = None

    def _cancel_chrome_hide(self):
        if getattr(self, "_chrome_hide_after", None) is not None:
            try:
                self.after_cancel(self._chrome_hide_after)
            except Exception:
                pass
            self._chrome_hide_after = None

    def _keep_cursor_visible(self):
        try:
            if self._cursor_hide_after is not None:
                self.after_cancel(self._cursor_hide_after)
        except tk.TclError:
            pass
        self._cursor_hide_after = None
        self._show_cursor()

    def _update_chrome_visibility(self, event):
        if not self._is_fullscreen():
            return
        try:
            y = event.y_root - self.winfo_rooty()
        except tk.TclError:
            return
        if y <= 6:
            self._show_chrome()
        elif self._chrome_visible:
            if y <= CHROME_HEIGHT + 4:
                self._cancel_chrome_hide()
                self._keep_cursor_visible()
            else:
                self._schedule_chrome_hide()

    def _window_minimize(self):
        if self._is_fullscreen():
            self._leave_fullscreen()
        self._apply_chrome_mode()
        self._win_minimize()

    def _window_maximize(self):
        was_fs = self._is_fullscreen()
        if was_fs:
            self._leave_fullscreen()
        if was_fs:
            if not self._maximized:
                try:
                    self._window_geometry = self.geometry()
                except tk.TclError:
                    pass
                self._maximized = True
                x, y, w, h = self._win_work_area()
                self._win_set_rect(x, y, w, h, topmost=False)
        elif self._maximized:
            self._maximized = False
            self._restore_window_geometry()
        else:
            try:
                self._window_geometry = self.geometry()
            except tk.TclError:
                pass
            self._maximized = True
            x, y, w, h = self._win_work_area()
            self._win_set_rect(x, y, w, h, topmost=False)
        self._apply_chrome_mode()
        self._sync_chrome()
        if (getattr(self, "_keep_topmost_windowed", False)
                and not self._is_fullscreen()):
            self._win_set_topmost(True)

    def _window_close(self):
        self.destroy()

    # ---------- 하단 슬라이드바 / 설정 ----------
    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg="#222222", height=64)
        self._bottom_bar = bar
        self._slider_label = tk.Label(bar, text="", fg="white", bg="#222222",
                                      anchor="w", font=("", 10))
        self._slider_label.pack(fill="x", padx=10, pady=(6, 0))
        self._slider = tk.Scale(bar, from_=0, to=0, orient="horizontal", showvalue=0,
                                bg="#222222", fg="white", troughcolor="#444444",
                                activebackground="#666666", highlightthickness=0,
                                length=600, command=self._on_slider_drag)
        self._slider.pack(fill="x", padx=10, pady=(0, 6))
        # 트랙 클릭 시 특정 페이지로 점프 (기본 동작인 한 페이지 이동 대체)
        self._slider.bind("<Button-1>", self._on_slider_press_jump)
        self._slider.bind("<B1-Motion>", self._on_slider_drag_jump)
        self._slider.bind("<ButtonRelease-1>", self._on_slider_release)
        # 마우스를 치우면 바로 사라지게 (지연 없음)
        bar.bind("<Enter>", lambda e: self._cancel_hide_bar())
        bar.bind("<Leave>", lambda e: self._hide_bottom_bar())
        self._slider.bind("<Enter>", lambda e: self._cancel_hide_bar())
        self._slider.bind("<Leave>", lambda e: self._hide_bottom_bar())

    def _build_anim_bar(self):
        # 애니메이션 프레임 진행 바. 정지 이미지에서는 숨긴다.
        bar = tk.Frame(self, bg="#222222")
        self._anim_bar = bar
        self._anim_bar_label = tk.Label(bar, text="", fg="#dddddd", bg="#222222",
                                        anchor="w", font=("", 9))
        self._anim_bar_label.pack(fill="x", padx=10, pady=(3, 0))
        track = tk.Canvas(bar, height=4, bg="#444444", highlightthickness=0)
        self._anim_bar_track = track
        track.pack(fill="x", padx=10, pady=(2, 4))
        self._anim_bar_fill = track.create_rectangle(0, 0, 0, 4,
                                                     fill="#bbbbbb", outline="")
        track.bind("<Configure>", lambda e: self._update_anim_bar())

    def _bottom_bar_y(self):
        # 애니메이션 바가 보이면 페이지 슬라이더를 그 위로 올린다.
        return -40 if self._anim_bar_visible else -10

    def _reposition_bottom_bar(self):
        if not self._slider_visible:
            return
        try:
            self._bottom_bar.place_configure(y=self._bottom_bar_y())
        except tk.TclError:
            pass

    def _apply_slider_mode(self):
        if self.slider_mode == "always" and self.items:
            self._show_bottom_bar()
        elif self.slider_mode == "never":
            self._hide_bottom_bar()

    def _show_bottom_bar(self):
        if not self.items:
            return
        if not self._slider_visible:
            try:
                # 화면 한가운데 1/3 너비로 축소, 하단에서 10px 띄워서 표시
                self._bottom_bar.place(relx=0.5, rely=1.0, anchor="s",
                                       relwidth=0.33, height=64,
                                       y=self._bottom_bar_y())
                self._slider_visible = True
            except tk.TclError:
                return
        self._update_slider()

    def _hide_bottom_bar(self):
        if self._slider_visible:
            try:
                self._bottom_bar.place_forget()
            except tk.TclError:
                pass
            self._slider_visible = False
        self._hide_bar_after = None

    def _schedule_hide_bar(self, delay=0):
        # 마우스를 치우면 바로 사라지게: 지연 없이 즉시 숨김.
        # (이전에는 1200~1500ms 지연이 있어 느리게 느껴졌음)
        if self.slider_mode != "auto":
            return
        self._cancel_hide_bar()
        self._hide_bottom_bar()

    def _cancel_hide_bar(self):
        if self._hide_bar_after is not None:
            try:
                self.after_cancel(self._hide_bar_after)
            except tk.TclError:
                pass
            self._hide_bar_after = None

    def _show_cursor(self):
        if not self._cursor_hidden:
            return
        try:
            self.config(cursor="")
            self.canvas.config(cursor="")
        except tk.TclError:
            pass
        self._cursor_hidden = False

    def _hide_cursor_now(self):
        # 모달 창이 열려 있을 때는 숨기지 않음
        if self._modal_open:
            return
        # 페이지 이동 등 동작 시 바로 숨김
        try:
            if self._cursor_hide_after is not None:
                self.after_cancel(self._cursor_hide_after)
        except tk.TclError:
            pass
        self._cursor_hide_after = None
        if self._cursor_hidden:
            return
        try:
            self.config(cursor="none")
            self.canvas.config(cursor="none")
        except tk.TclError:
            pass
        self._cursor_hidden = True

    def _reset_cursor_timer(self):
        # 모달 창이 열려 있을 때는 숨김 예약하지 않고 커서 표시 유지
        try:
            if self._cursor_hide_after is not None:
                self.after_cancel(self._cursor_hide_after)
        except tk.TclError:
            pass
        self._cursor_hide_after = None
        self._show_cursor()
        if self._modal_open:
            return
        # 마우스 움직임 시 커서 다시 표시 + 2초 후 숨김 예약
        try:
            self._cursor_hide_after = self.after(2000, self._hide_cursor_now)
        except tk.TclError:
            self._cursor_hide_after = None

    def _on_mouse_move(self, event):
        # 움직이면 커서 다시 표시 + 2초 타이머 리셋
        self._reset_cursor_timer()
        self._update_chrome_visibility(event)
        if self.slider_mode == "never":
            return
        if self.slider_mode == "always":
            if not self._slider_visible:
                self._show_bottom_bar()
            return
        # auto: 마우스가 화면 하단 80px 안에 들어오면 표시, 벗어나면 숨김 예약
        try:
            h = self.winfo_height()
            # 어느 위젯에서 온 이벤트든 루트 기준 y로 환산
            y = event.y_root - self.winfo_rooty()
        except tk.TclError:
            return
        if h <= 1:
            return
        # event.y는 루트 기준. 하단 바 위에 있으면 숨김 예약 취소
        if self._slider_visible and y > h - 70:
            self._cancel_hide_bar()
            return
        if y > h - 80:
            self._show_bottom_bar()
            self._cancel_hide_bar()
        else:
            if self._slider_visible:
                # 마우스를 치우면 바로 사라지게 (지연 없음)
                self._hide_bottom_bar()

    def _update_slider(self):
        if not self.items:
            return
        try:
            self._slider.config(to=max(0, len(self.items) - 1))
            self._slider_updating = True
            self._slider.set(self.index)
            self._slider_updating = False
            it = self.items[self.index]
            self._slider_label.config(
                text="%d / %d  %s" % (self.index + 1, len(self.items), it["name"]))
        except tk.TclError:
            pass

    def _on_slider_drag(self, value):
        # 클릭 즉시 이동 (놓을 때까지 기다리지 않음, 미리보기 팁 없음)
        if self._slider_updating or not self.items:
            return
        try:
            idx = int(float(value))
        except ValueError:
            return
        idx = max(0, min(len(self.items) - 1, idx))
        if idx == self.index:
            return
        self.goto(idx)

    def _on_slider_release(self, event):
        # 클릭 시 이미 이동했으므로 놓을 때는 아무것도 하지 않음
        return

    def _slider_value_from_x(self, x):
        # Scale 트랙의 클릭 x좌표를 슬라이더 값으로 변환 (특정 페이지 점프용)
        if not self.items:
            return 0
        try:
            w = self._slider.winfo_width()
            try:
                sl = int(self._slider.cget("sliderlength"))
            except Exception:
                sl = 30
            try:
                bd = int(self._slider.cget("borderwidth"))
            except Exception:
                bd = 2
            start = bd + sl / 2.0
            end = w - bd - sl / 2.0
            if end <= start:
                frac = x / max(1, w)
            else:
                frac = (x - start) / (end - start)
            frac = max(0.0, min(1.0, frac))
            lo = int(self._slider.cget("from"))
            hi = int(self._slider.cget("to"))
            return int(round(lo + frac * (hi - lo)))
        except tk.TclError:
            return 0

    def _on_slider_press_jump(self, event):
        # 트랙 아무 곳이나 누르면 그 위치의 페이지로 점프 (기본 한 페이지 이동 대체)
        idx = self._slider_value_from_x(event.x)
        self._slider_updating = True
        try:
            self._slider.set(idx)
        finally:
            self._slider_updating = False
        self._on_slider_drag(str(idx))
        return "break"  # 기본 동작(한 페이지 이동) 막기

    def _on_slider_drag_jump(self, event):
        # 드래그 중에도 클릭 위치를 따라가게
        idx = self._slider_value_from_x(event.x)
        self._slider_updating = True
        try:
            self._slider.set(idx)
        finally:
            self._slider_updating = False
        self._on_slider_drag(str(idx))
        return "break"

    def open_folder_dialog(self):
        self._suppress_topmost_drop = True
        try:
            self.withdraw()
            self.update_idletasks()
            d = filedialog.askdirectory(title=tr("폴더 열기"))
        finally:
            try:
                self.deiconify()
            except tk.TclError:
                pass
            self._suppress_topmost_drop = False
        if not d:
            return
        if not self._load_path(d):
            self._show_load_error(d)

    def open_archive_dialog(self):
        self._suppress_topmost_drop = True
        try:
            self.withdraw()
            self.update_idletasks()
            p = filedialog.askopenfilename(
                title=tr("압축파일 열기 (풀지 않고 보기)"),
                filetypes=[(tr("압축파일"), "*.zip *.cbz"), (tr("모든 파일"), "*.*")])
        finally:
            try:
                self.deiconify()
            except tk.TclError:
                pass
            self._suppress_topmost_drop = False
        if not p:
            return
        if not self._load_path(p):
            self._show_load_error(p)

    def open_settings_dialog(self):
        # 전체화면 위에도 뜨도록 topmost로 띄운다. 버튼 없음, 누르면 바로 적용+저장.
        # 설정 창이 열려 있는 동안은 마우스가 항상 보이도록 커서 숨김 중단.
        self._modal_open = True
        self._show_cursor()
        try:
            if self._cursor_hide_after is not None:
                self.after_cancel(self._cursor_hide_after)
        except tk.TclError:
            pass
        self._cursor_hide_after = None
        dlg = tk.Toplevel(self)
        dlg.title(tr("설정"))
        # 고정 크기(420x360) 제거: 내용에 맞게 자동 크기 조절 (버튼 잘림 원인 제거)
        try:
            dlg.attributes("-topmost", True)
            dlg.attributes("-alpha", 1.0)
            dlg.transient(self)
            dlg.grab_set()
        except tk.TclError:
            pass
        dlg.configure(bg="#f0f0f0")

        cur = load_settings()
        # 언어: 바꾸면 즉시 저장하고 창을 새 언어로 다시 연다.
        ttk.Label(dlg, text=tr("언어")).pack(anchor="w", padx=14, pady=(14, 2))
        lang_var = tk.StringVar(value=cur.get("language") or _LANG)
        lang_frame = ttk.Frame(dlg)
        lang_frame.pack(anchor="w", padx=14)
        for label, val in [("한국어", "ko"), ("English", "en")]:
            ttk.Radiobutton(lang_frame, text=tr(label), variable=lang_var,
                            value=val, command=lambda: change_language()).pack(
                                side="left", padx=(0, 12))
        # 보간기법
        ttk.Label(dlg, text=tr("보간기법 (확대/축소 품질)")).pack(anchor="w", padx=14, pady=(10, 2))
        interp_names = [n for n, _f, _d in INTERPOLATIONS]
        interp_var = tk.StringVar(value=cur.get("interpolation", "LANCZOS"))
        interp_combo = ttk.Combobox(dlg, textvariable=interp_var, values=interp_names,
                     state="readonly", width=20)
        interp_combo.pack(anchor="w", padx=14)
        desc_var = tk.StringVar()

        def update_interp_desc(*_args):
            name = interp_var.get()
            for n, _f, d in INTERPOLATIONS:
                if n == name:
                    desc_var.set(tr(d))
                    return
            desc_var.set("")

        ttk.Label(dlg, textvariable=desc_var, foreground="#666666",
                  wraplength=340, justify="left").pack(
                      anchor="w", padx=14, pady=(2, 8))
        update_interp_desc()
        # 이미지 크기
        ttk.Label(dlg, text=tr("이미지 크기")).pack(anchor="w", padx=14, pady=(2, 2))
        fit_var = tk.StringVar(value=cur.get("fit_mode", "fit"))
        fit_frame = ttk.Frame(dlg)
        fit_frame.pack(anchor="w", padx=14)
        for label, val in [("너비 맞춤 (8)", "width"), ("화면 맞춤 (9)", "fit"),
                           ("원본 100% (0)", "original")]:
            ttk.Radiobutton(fit_frame, text=tr(label), variable=fit_var, value=val).pack(side="left", padx=(0, 10))
        ttk.Button(dlg, text=tr("단축키 설정..."),
                   command=lambda: self.open_shortcut_dialog(dlg)).pack(
                       anchor="w", padx=14, pady=(8, 0))
        # 휠 동작 (휠과 Ctrl+휠을 한 쌍으로 선택)
        ttk.Label(dlg, text=tr("마우스 휠 동작")).pack(anchor="w", padx=14, pady=(10, 2))
        wheel_var = tk.StringVar(value=cur.get("wheel_mode", "navigate"))
        wheel_frame = ttk.Frame(dlg)
        wheel_frame.pack(anchor="w", padx=14)
        ttk.Radiobutton(wheel_frame,
                        text=tr("휠 = 이동, Ctrl+휠 = 확대/축소 (기본)"),
                        variable=wheel_var, value="navigate").pack(anchor="w")
        ttk.Radiobutton(wheel_frame,
                        text=tr("휠 = 확대/축소, Ctrl+휠 = 이동"),
                        variable=wheel_var, value="zoom").pack(anchor="w")
        # 배경
        ttk.Label(dlg, text=tr("배경색")).pack(anchor="w", padx=14, pady=(10, 2))
        bg_var = tk.StringVar(value=cur.get("bg_color", "black"))
        bg_frame = ttk.Frame(dlg)
        bg_frame.pack(anchor="w", padx=14)
        for label, val in [("검정", "black"), ("어두운 회색", "darkgray"), ("흰색", "white")]:
            ttk.Radiobutton(bg_frame, text=tr(label), variable=bg_var, value=val).pack(side="left", padx=(0, 10))
        # 슬라이드바
        ttk.Label(dlg, text=tr("하단 슬라이드바")).pack(anchor="w", padx=14, pady=(10, 2))
        slider_var = tk.StringVar(value=cur.get("slider_mode", "auto"))
        slider_frame = ttk.Frame(dlg)
        slider_frame.pack(anchor="w", padx=14)
        for label, val in [("마우스 아래로 내리면 표시", "auto"), ("항상 표시", "always"), ("표시 안 함", "never")]:
            ttk.Radiobutton(slider_frame, text=tr(label), variable=slider_var,
                            value=val).pack(anchor="w")
        # 처음/끝 동작 + 다음 폴더 순서 (가로 배치)
        end_sort = ttk.Frame(dlg)
        end_sort.pack(anchor="w", fill="x", padx=14, pady=(10, 14))
        end_col = ttk.Frame(end_sort)
        end_col.pack(side="left", anchor="n")
        sort_col = ttk.Frame(end_sort)
        sort_col.pack(side="left", anchor="n", padx=(30, 0))

        ttk.Label(end_col, text=tr("처음/끝 동작")).pack(anchor="w", pady=(0, 2))
        end_var = tk.StringVar(value=cur.get("end_behavior", "loop"))
        end_frame = ttk.Frame(end_col)
        end_frame.pack(anchor="w")
        ttk.Radiobutton(end_frame, text=tr("반복 (끝에서 다시 처음으로)"), variable=end_var,
                        value="loop").pack(anchor="w")
        ttk.Radiobutton(end_frame, text=tr("멈춤 (끝에서 더 이상 이동 안 함)"), variable=end_var,
                        value="stop").pack(anchor="w")
        ttk.Radiobutton(end_frame, text=tr("다음 항목으로 이동 (폴더·압축파일)"), variable=end_var,
                        value="next_folder").pack(anchor="w")

        sort_label = ttk.Label(sort_col, text=tr("다음 항목 순서"))
        sort_label.pack(anchor="w", pady=(0, 2))
        sort_var = tk.StringVar(value=cur.get("next_folder_sort", "name_asc"))
        sort_frame = ttk.Frame(sort_col)
        sort_frame.pack(anchor="w")
        for label, val in [("이름 오름차순", "name_asc"), ("이름 내림차순", "name_desc"),
                           ("수정날짜 오름차순", "mtime_asc"), ("수정날짜 내림차순", "mtime_desc")]:
            ttk.Radiobutton(sort_frame, text=tr(label), variable=sort_var,
                            value=val).pack(anchor="w")

        # 탐색기 연결 (압축파일 우클릭 메뉴)
        assoc = ttk.Frame(dlg)
        assoc.pack(anchor="w", fill="x", padx=14, pady=(12, 14))
        assoc_label = ttk.Label(assoc, text=tr("탐색기 연결"))
        assoc_label.pack(anchor="w", pady=(0, 2))
        assoc_state = tk.StringVar()
        assoc_btns = ttk.Frame(assoc)
        assoc_btns.pack(anchor="w")
        register_btn = ttk.Button(assoc_btns, text=tr("등록"),
                                  command=lambda: set_assoc(True))
        register_btn.pack(side="left")
        unregister_btn = ttk.Button(assoc_btns, text=tr("해제"),
                                    command=lambda: set_assoc(False))
        unregister_btn.pack(side="left", padx=(6, 0))
        ttk.Label(assoc, textvariable=assoc_state, foreground="#666666",
                  wraplength=460, justify="left").pack(
            anchor="w", pady=(4, 0))

        def refresh_assoc():
            try:
                if is_file_association_registered():
                    assoc_state.set(tr("등록되어 있습니다.\n"
                                       "· 압축파일(CBZ/ZIP) 우클릭 메뉴에 '달빛뷰어로 열기' 추가\n"
                                       "· 이미지 확장자(JPG/PNG 등)를 '연결 프로그램' 목록과 기본 앱 후보에 추가\n"
                                       "기본 앱은 바뀌지 않습니다. Windows 설정 > 기본 앱에서 직접 선택하세요."))
                else:
                    assoc_state.set(tr("등록되지 않았습니다. '등록'을 누르면 다음이 추가됩니다.\n"
                                       "· 압축파일(CBZ/ZIP) 우클릭 메뉴 '달빛뷰어로 열기'\n"
                                       "· 이미지 확장자를 '연결 프로그램' 목록과 기본 앱 후보에 추가\n"
                                       "기본 앱은 바뀌지 않습니다."))
            except Exception:
                assoc_state.set("")

        def set_assoc(enabled):
            self._set_file_association(enabled, parent=dlg)
            refresh_assoc()

        def apply_now(*_args):
            new = {
                "language": lang_var.get(),
                "interpolation": interp_var.get(),
                "fit_mode": fit_var.get(),
                "wheel_mode": wheel_var.get(),
                "bg_color": bg_var.get(),
                "slider_mode": slider_var.get(),
                "end_behavior": end_var.get(),
                "next_folder_sort": sort_var.get(),
                "shortcuts": dict(self._shortcuts),
            }
            save_settings(new)
            self.settings = new
            self._save_window_state()  # 설정 저장 시 창 상태 키가 지워지지 않게 유지
            # 즉시 적용
            for i, (n, _f, _d) in enumerate(INTERPOLATIONS):
                if n == new["interpolation"]:
                    self.interp_idx = i
                    break
            self.wheel_mode = new["wheel_mode"]
            self.slider_mode = new["slider_mode"]
            self.end_behavior = new.get("end_behavior", "loop")
            self.next_folder_sort = new.get("next_folder_sort", "name_asc")
            # 이미지 크기 변경은 현재 화면에도 바로 적용
            if self.fit_mode != new["fit_mode"]:
                self.fit_mode = new["fit_mode"]
                if new["fit_mode"] == "original":
                    self.zoom = 1.0
                try:
                    self._fit_var.set(new["fit_mode"])
                except tk.TclError:
                    pass
                self._need_center = True
            bgc = BG_COLORS.get(new["bg_color"], "#000000")
            try:
                self.configure(bg=bgc)
                self.canvas.configure(bg=bgc)
                self._bottom_bar.configure(bg="#222222")
            except tk.TclError:
                pass
            update_interp_desc()
            self._apply_slider_mode()
            self._redraw()

        def change_language():
            if lang_var.get() == _LANG:
                return
            apply_now()
            set_language(lang_var.get())
            self._retranslate_chrome()
            # 열린 설정 창은 이미 만든 문자열을 바꿀 수 없으므로 새 언어로 다시 연다.
            dlg.destroy()
            self.after(0, self.open_settings_dialog)

        def sync_sort_state(*_args):
            # 다음 폴더 순서는 '다음 폴더로 이동'을 선택했을 때만 의미가 있다
            enabled = end_var.get() == "next_folder"
            for w in sort_frame.winfo_children():
                try:
                    if enabled:
                        w.state(["!disabled"])
                    else:
                        w.state(["disabled"])
                except tk.TclError:
                    pass
            try:
                if enabled:
                    sort_label.state(["!disabled"])
                else:
                    sort_label.state(["disabled"])
            except tk.TclError:
                pass

        def apply_end(*_args):
            apply_now()
            sync_sort_state()

        # 모든 컨트롤에 즉시 적용 연결 (저장/취소 버튼 없음)
        interp_combo.bind("<<ComboboxSelected>>", apply_now)
        for w in list(fit_frame.winfo_children()) + list(wheel_frame.winfo_children()) + list(bg_frame.winfo_children()) + list(slider_frame.winfo_children()):
            try:
                w.configure(command=apply_now)
            except tk.TclError:
                pass
        for w in end_frame.winfo_children():
            try:
                w.configure(command=apply_end)
            except tk.TclError:
                pass
        for w in sort_frame.winfo_children():
            try:
                w.configure(command=apply_now)
            except tk.TclError:
                pass
        sync_sort_state()
        refresh_assoc()
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        try:
            dlg.wait_window(dlg)
        finally:
            # 설정 창 닫으면 커서 자동 숨김 다시 시작
            self._modal_open = False
            self._reset_cursor_timer()

    def _save_shortcuts(self):
        data = load_settings()
        data["shortcuts"] = dict(self._shortcuts)
        save_settings(data)
        self.settings = data

    def open_shortcut_dialog(self, parent=None):
        dlg = tk.Toplevel(parent or self)
        dlg.title(tr("단축키 설정"))
        try:
            dlg.attributes("-topmost", True)
            dlg.attributes("-alpha", 1.0)
            if parent is not None:
                dlg.transient(parent)
            dlg.grab_set()
        except tk.TclError:
            pass
        dlg.configure(bg="#f0f0f0")
        dlg.withdraw()
        px = parent.winfo_rootx() if parent is not None else self.winfo_rootx()
        py = parent.winfo_rooty() if parent is not None else self.winfo_rooty()
        pw = parent.winfo_width() if parent is not None else self.winfo_width()
        ph = parent.winfo_height() if parent is not None else self.winfo_height()

        ttk.Label(dlg, text=tr("키 버튼을 누른 뒤 새 키를 누르세요. Esc는 취소입니다. (Alt는 포함되지 않습니다.)"),
                  foreground="#666666").pack(anchor="w", padx=14, pady=(12, 2))
        status_var = tk.StringVar()
        ttk.Label(dlg, textvariable=status_var, foreground="#666666").pack(
            anchor="w", padx=14, pady=(0, 4))

        body = ttk.Frame(dlg)
        body.pack(fill="both", expand=True, padx=14)
        key_buttons = {}
        capture_action = [None]

        def end_capture():
            action = capture_action[0]
            capture_action[0] = None
            if action is not None and action in key_buttons:
                key_buttons[action].configure(
                    text=format_key_id(self._shortcuts[action]))
            status_var.set("")

        def start_capture(action):
            old = capture_action[0]
            if old is not None and old != action and old in key_buttons:
                key_buttons[old].configure(
                    text=format_key_id(self._shortcuts[old]))
            capture_action[0] = action
            key_buttons[action].configure(text=tr("키 입력..."))
            status_var.set(tr("새 단축키를 누르세요. (Esc 취소)"))
            try:
                dlg.focus_force()
            except tk.TclError:
                pass

        def on_key(event):
            if capture_action[0] is None:
                if event.keysym == "Escape":
                    close()
                    return "break"
                return None
            if event.keysym == "Escape":
                end_capture()
                return "break"
            key_id = normalize_key_id(event)
            if not key_id:
                status_var.set(tr("일반 키를 누르세요."))
                return "break"
            if key_id in FIXED_SHORTCUT_KEYS:
                status_var.set(tr("%s 키는 고정 단축키입니다.") % format_key_id(key_id))
                return "break"
            action = capture_action[0]
            for other, other_key in self._shortcuts.items():
                if other != action and other_key == key_id:
                    status_var.set(tr("%s 키는 '%s'에 이미 사용 중입니다.") %
                                   (format_key_id(key_id),
                                    tr(SHORTCUT_LABELS.get(other, other))))
                    return "break"
            self._shortcuts[action] = key_id
            self._rebuild_shortcut_map()
            self._save_shortcuts()
            end_capture()
            status_var.set(tr("저장되었습니다."))
            return "break"

        for action, label, _default in SHORTCUT_ACTIONS:
            row = ttk.Frame(body)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=tr(label), width=22).pack(side="left")
            b = tk.Button(
                row, text=format_key_id(self._shortcuts[action]), width=18,
                anchor="center", relief="solid", bd=1, bg="#ffffff",
                activebackground="#e6e6e6", highlightthickness=0,
                font=("맑은 고딕", 9),
                command=lambda a=action: start_capture(a))
            b.configure(takefocus=False)
            b.pack(side="right")
            key_buttons[action] = b

        ttk.Separator(body).pack(fill="x", pady=(10, 6))
        ttk.Label(body, justify="left", foreground="#555555", text=tr(
            "기본 조작\n"
            "방향키 / WASD : 확대 시 화면 이동, 맞춤 보기에서는 이전·다음\n"
            "PageUp / PageDown, Space / Backspace : 이전·다음\n"
            "Home / End : 처음·마지막\n"
            "Alt+Enter : 전체화면\n"
            "Ctrl+O : 파일 열기\n"
            "마우스 휠 : 설정에 따라 이동/확대·축소 (기본: 이동)\n"
            "Ctrl + 마우스 휠 : 설정에 따라 확대·축소/이동 (기본: 확대·축소)\n"
            "Esc : 종료"
        )).pack(anchor="w")

        bottom = ttk.Frame(dlg)
        bottom.pack(fill="x", padx=14, pady=(8, 12))

        def reset_defaults():
            self._shortcuts = dict(SHORTCUT_DEFAULTS)
            self._rebuild_shortcut_map()
            self._save_shortcuts()
            for a, b in key_buttons.items():
                b.configure(text=format_key_id(self._shortcuts[a]))
            status_var.set(tr("기본값으로 복원했습니다."))

        def close():
            try:
                dlg.grab_release()
            except tk.TclError:
                pass
            dlg.destroy()
            if parent is not None:
                try:
                    parent.grab_set()
                except tk.TclError:
                    pass

        ttk.Button(bottom, text=tr("기본값"), command=reset_defaults).pack(side="left")
        ttk.Button(bottom, text=tr("닫기"), command=close).pack(side="right")
        dlg.update_idletasks()
        w = min(dlg.winfo_reqwidth(), self.winfo_screenwidth() - 80)
        h = min(dlg.winfo_reqheight(), self.winfo_screenheight() - 80)
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        dlg.geometry("%dx%d+%d+%d" % (w, h, x, y))
        dlg.minsize(min(400, w), min(300, h))
        dlg.deiconify()
        dlg.bind("<KeyPress>", on_key)
        dlg.protocol("WM_DELETE_WINDOW", close)
        dlg.wait_window(dlg)

    def open_viewed_folders_dialog(self):
        # 열람한 목록: 폴더와 압축파일을 선택해 휴지통으로 보내거나 목록에서만 제거한다.
        self._modal_open = True
        self._show_cursor()
        try:
            if self._cursor_hide_after is not None:
                self.after_cancel(self._cursor_hide_after)
        except tk.TclError:
            pass
        self._cursor_hide_after = None
        try:
            dlg = tk.Toplevel(self)
            dlg.title(tr("열람한 목록"))
            try:
                dlg.attributes("-topmost", True)
                dlg.attributes("-alpha", 1.0)
                dlg.transient(self)
                dlg.grab_set()
            except tk.TclError:
                pass
            dlg.configure(bg="#f0f0f0")
            w = min(900, self.winfo_screenwidth() - 80)
            h = min(560, self.winfo_screenheight() - 80)
            x = max(0, self.winfo_rootx() + (self.winfo_width() - w) // 2)
            y = max(0, self.winfo_rooty() + (self.winfo_height() - h) // 2)
            dlg.geometry("%dx%d+%d+%d" % (w, h, x, y))
            dlg.minsize(720, 360)

            paths = []
            header_var = tk.StringVar()
            status_var = tk.StringVar()
            ttk.Label(dlg, textvariable=header_var).pack(anchor="w", padx=12, pady=(12, 2))
            ttk.Label(dlg, text=tr("항목을 체크한 뒤 아래 버튼을 누르세요. 휴지통 이동은 실제 삭제, 목록 제거는 이 목록에서만 숨깁니다."),
                      foreground="#666666").pack(anchor="w", padx=12, pady=(0, 6))

            top = ttk.Frame(dlg)
            top.pack(fill="x", padx=12)
            select_all_var = tk.BooleanVar(value=False)
            select_all_cb = tk.Checkbutton(
                top, text=tr("전체 선택"), variable=select_all_var,
                bg="#f0f0f0", activebackground="#f0f0f0",
                font=("맑은 고딕", 9), anchor="w", command=lambda: toggle_all())
            select_all_cb.pack(side="left")
            ttk.Label(top, textvariable=status_var, foreground="#666666").pack(side="right")

            list_frame = ttk.Frame(dlg)
            list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 0))
            list_frame.rowconfigure(0, weight=1)
            list_frame.columnconfigure(0, weight=1)
            canvas = tk.Canvas(list_frame, bg="#f0f0f0", highlightthickness=0)
            ysb = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            xsb = ttk.Scrollbar(list_frame, orient="horizontal", command=canvas.xview)
            inner = tk.Frame(canvas, bg="#f0f0f0")
            canvas.create_window((0, 0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            ysb.grid(row=0, column=1, sticky="ns")
            xsb.grid(row=1, column=0, sticky="ew")

            vars = {}
            delete_btn = None
            remove_btn = None

            def checked():
                return [p for p, v in vars.items() if v.get()]

            def sync_state(*_args):
                total = len(vars)
                n = len(checked())
                select_all_var.set(total > 0 and n == total)
                try:
                    select_all_cb.configure(state="normal" if total else "disabled")
                except tk.TclError:
                    pass
                for b in (delete_btn, remove_btn):
                    if b is not None:
                        try:
                            b.configure(state="normal" if n else "disabled")
                        except tk.TclError:
                            pass
                if total:
                    status_var.set(tr("체크 %d개 / 전체 %d개") % (n, total))
                else:
                    status_var.set(tr("기록된 항목이 없습니다. 끝까지 본 뒤 다음으로 넘어가면 추가됩니다."))

            def toggle_all():
                value = select_all_var.get()
                for v in vars.values():
                    v.set(value)
                sync_state()

            def on_wheel(event):
                try:
                    canvas.yview_scroll(int(-event.delta / 120), "units")
                except tk.TclError:
                    pass
                return "break"

            def rebuild():
                nonlocal paths
                paths = load_viewed_folders()
                for w in inner.winfo_children():
                    w.destroy()
                vars.clear()
                for p in paths:
                    v = tk.BooleanVar(value=False)
                    cb = tk.Checkbutton(
                        inner, text=p, variable=v, anchor="w", justify="left",
                        bg="#f0f0f0", activebackground="#f0f0f0",
                        font=("맑은 고딕", 9), command=sync_state)
                    cb.pack(anchor="w", fill="x", padx=4, pady=1)
                    cb.bind("<MouseWheel>", on_wheel)
                    vars[p] = v
                header_var.set(tr("끝까지 본 항목 %d개") % len(paths))
                inner.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.xview_moveto(0)
                canvas.yview_moveto(0)
                select_all_var.set(False)
                sync_state()

            def remove_checked():
                chosen = checked()
                if not chosen:
                    return
                keys = {os.path.normcase(p) for p in chosen}
                save_viewed_folders([p for p in paths if os.path.normcase(p) not in keys])
                rebuild()
                status_var.set(tr("%d개를 목록에서 제거했습니다. (디스크는 그대로)") % len(chosen))

            def delete_checked():
                chosen = checked()
                if not chosen:
                    return
                targets = drop_nested_paths(chosen)
                current_hit = any(self._current_view_is_under(p) for p in targets)
                shown = "\n".join(targets[:6])
                if len(targets) > 6:
                    shown += tr("\n... 외 %d개") % (len(targets) - 6)
                extra = (tr("\n\n현재 보고 있는 항목이 포함되어 있어 화면이 비워집니다.")
                         if current_hit else "")
                msg = (tr("%d개 항목을 휴지통으로 보냅니다.\n"
                          "폴더는 하위 파일도 함께 이동합니다.\n\n%s%s\n\n계속할까요?") %
                       (len(targets), shown, extra))
                if not messagebox.askyesno(tr("휴지통으로 이동"), msg, parent=dlg):
                    return
                deleted = []
                errors = []
                for p in targets:
                    reason = deletion_block_reason(p)
                    if reason:
                        errors.append("%s — %s" % (p, reason))
                        continue
                    ok, err = move_to_recycle_bin(p, owner=dlg.winfo_id())
                    if ok:
                        deleted.append(p)
                    else:
                        log_error("recycle failed: %r : %s" % (p, err))
                        errors.append("%s — %s" % (p, err))
                if deleted:
                    prune_viewed_folders(deleted)
                    if any(self._current_view_is_under(p) for p in deleted):
                        self._clear_view()
                rebuild()
                msg = (tr("%d개를 휴지통으로 보냈습니다.") % len(deleted)
                       if deleted else tr("휴지통으로 보낸 항목이 없습니다."))
                if errors:
                    msg += tr(" %d개 실패.") % len(errors)
                status_var.set(msg)
                if errors:
                    messagebox.showwarning(
                        tr("일부 폴더를 이동하지 못했습니다"),
                        "\n".join(errors[:10]) + ("\n..." if len(errors) > 10 else ""),
                        parent=dlg)

            btns = ttk.Frame(dlg)
            btns.pack(fill="x", padx=12, pady=(8, 12))
            delete_btn = ttk.Button(btns, text=tr("체크한 항목을 휴지통으로 이동"),
                                    command=delete_checked, state="disabled")
            delete_btn.pack(side="left")
            remove_btn = ttk.Button(btns, text=tr("체크한 항목을 목록에서만 제거"),
                                    command=remove_checked, state="disabled")
            remove_btn.pack(side="left", padx=(6, 0))
            ttk.Button(btns, text=tr("닫기"), command=dlg.destroy).pack(side="right")

            dlg.bind("<Escape>", lambda e: dlg.destroy())
            rebuild()
            dlg.focus_set()
            dlg.wait_window(dlg)
        finally:
            self._modal_open = False
            self._reset_cursor_timer()

    def _current_view_is_under(self, folder):
        cur = getattr(self, "_current_dir", None)
        if not cur:
            return False
        return _path_is_under(cur, folder)

    def _clear_view(self):
        # 현재 보던 폴더가 삭제됐을 때 화면/캐시/이동 상태를 비운다.
        self.items = []
        self.index = -1
        self._current_dir = None
        self._nav_root = None
        self._last_error = None
        self._cache.clear()
        self._disp_size = (0, 0)
        self._slider_target = None
        self.zoom = 1.0
        self._clear_edge_armed()
        self._stop_animation()
        self._hide_bottom_bar()
        try:
            self.canvas.delete("all")
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
        except tk.TclError:
            pass
        self._photo = None
        try:
            self._draw_welcome()
        except tk.TclError:
            pass

    # ---------- 열기 ----------
    def _open_dialog_or_quit(self):
        # 전체화면 위에 파일 대화상자가 가려지지 않도록 잠시 창을 숨긴다.
        self._suppress_topmost_drop = True
        try:
            self.withdraw()
            self.update_idletasks()
            p = filedialog.askopenfilename(
                title=tr("이미지 열기"),
                filetypes=[(tr("이미지"), "*.bmp *.jpg *.jpeg *.png *.gif *.webp *.tiff *.tif *.avif *.ico *.ppm"),
                           (tr("압축파일"), "*.zip *.cbz"),
                           (tr("모든 파일"), "*.*")])
        finally:
            try:
                self.deiconify()
            except tk.TclError:
                pass
            self._suppress_topmost_drop = False
        if not p:
            # 시작 화면(아이콘)을 유지한다. 설정/연결 등록을 하려고 앱만 열 수 있어야 한다.
            if not self.items:
                self._draw_welcome()
            return
        if not self._load_path(p):
            self._show_load_error(p)
            self._open_dialog_or_quit()

    def _show_load_error(self, target):
        msg = self._last_error or tr("이미지를 열 수 없습니다.")
        log_error("load failed: %r : %s" % (target, msg))
        # 정상 시청 중에는 UI를 띄우지 않지만, 로딩 실패는 검은 화면만으로는
        # 원인을 알 수 없으므로 이 경우에만 오류 창을 띄운다.
        try:
            self._suppress_topmost_drop = True
            messagebox.showerror(
                tr("이미지를 열 수 없습니다"),
                tr("%s\n\n%s\n\n지원: JPG/PNG/GIF/WebP/TIFF/BMP/AVIF 등\n"
                   "HEIC/HEIF, CLIP, 최신 RAW는 이 빌드에서 지원하지 않습니다.\n"
                   "자세한 원인은 viewer_error.log를 확인하세요.") % (target, msg))
        except tk.TclError:
            pass
        finally:
            self._suppress_topmost_drop = False

    def _load_path(self, target, from_adjacent=False):
        # from_adjacent=True: 다음/이전 폴더 이동으로 온 경우. 이동 범위(_nav_root)를 바꾸지 않음.
        # from_adjacent=False: 직접 연 경우(대화상자/탐색기/명령줄). 이동 범위를 새로 정함.
        self._last_error = None
        # 새 목록을 열 때는 기본 맞춤 모드로 되돌린다.
        self.fit_mode = self.settings.get("fit_mode", "fit")
        p = Path(target)
        if not p.exists():
            self._last_error = tr("파일이 존재하지 않습니다.")
            log_error("not exists: %r" % (target,))
            return False
        if p.is_dir():
            try:
                files = [str(f) for f in p.iterdir()
                         if f.is_file() and f.suffix.lower() in IMG_EXTS]
            except OSError as e:
                self._last_error = "%s: %s" % (p.name, e)
                log_error("list failed: %r : %s" % (target, e))
                return False
            files.sort(key=lambda x: natural_key(Path(x).name))
            if not files:
                self._last_error = tr("폴더 안에 표시할 이미지가 없습니다.")
                return False
            self.items = [{"name": Path(f).name, "path": f, "arc": None, "arc_name": None}
                          for f in files]
            # 첫 장만 확인 (속도: 시작 시 5장까지 읽던 것을 1장으로 줄임)
            first_ok = None
            for i in range(min(1, len(self.items))):
                if self._load_pil(i) is not None:
                    first_ok = i
                    break
            if first_ok is None:
                self.items = []
                return False
            self._current_dir = str(p.resolve())
            if not from_adjacent:
                # 직접 연 경우에만 이동 범위 재설정. 다음 폴더 이동 중에는 범위 유지.
                self._nav_root = str(p.parent.resolve())
            self._reset_view()
            self.index = first_ok
            if not from_adjacent:
                self._redraw()
            return True
        elif p.suffix.lower() in ARCHIVE_EXTS:
            try:
                with zipfile.ZipFile(p) as z:
                    names = [n for n in z.namelist()
                             if Path(n).suffix.lower() in IMG_EXTS and not n.endswith("/")]
                names.sort(key=natural_key)
                if not names:
                    self._last_error = tr("압축파일 안에 표시할 이미지가 없습니다.")
                    return False
                self.items = [{"name": Path(n).name, "path": None, "arc": str(p), "arc_name": n}
                              for n in names]
            except Exception as e:
                self._last_error = tr("압축파일 열기 오류: %s") % e
                log_error("archive failed: %r : %s" % (target, e))
                return False
            first_ok = None
            for i in range(min(1, len(self.items))):
                if self._load_pil(i) is not None:
                    first_ok = i
                    break
            if first_ok is None:
                self.items = []
                return False
            # 압축파일 자체를 현재 항목으로 둔다. 목록에도 파일 경로가 기록된다.
            self._current_dir = str(p.resolve())
            if not from_adjacent:
                self._nav_root = str(p.parent.resolve())
            self._reset_view()
            self.index = first_ok
            if not from_adjacent:
                self._redraw()
            return True
        elif p.suffix.lower() in IMG_EXTS:
            # 같은 폴더의 이미지들을 함께 불러와서 방향키로 이동 가능
            folder = p.parent
            try:
                files = [str(f) for f in folder.iterdir()
                         if f.is_file() and f.suffix.lower() in IMG_EXTS]
            except OSError as e:
                self._last_error = "%s: %s" % (folder.name, e)
                log_error("list failed: %r : %s" % (target, e))
                return False
            files.sort(key=lambda x: natural_key(Path(x).name))
            self.items = [{"name": Path(f).name, "path": f, "arc": None, "arc_name": None}
                          for f in files]
            start = next((i for i, it in enumerate(self.items)
                          if it["path"] == str(p)), 0)
            # 클릭한 이미지 자체가 열리는지 확인. 안 열리면 실패 처리.
            if self._load_pil(start) is None:
                self.items = []
                return False
            self._current_dir = str(folder.resolve())
            if not from_adjacent:
                self._nav_root = str(folder.parent.resolve())
            self._reset_view()
            self.index = start
            if not from_adjacent:
                self._redraw()
            return True
        else:
            self._last_error = tr("지원하지 않는 파일 형식입니다: %s") % p.suffix
            log_error("unsupported ext: %r" % (target,))
            return False

    def _reset_view(self):
        self._cache.clear()
        self._stop_animation()
        self.zoom = 1.0
        # 줌 상태는 이미지마다 초기화하고, 맞춤 모드는 유지한다.
        # 새 폴더를 열 때는 _load_path에서 기본 맞춤으로 다시 설정한다.
        if self.fit_mode == "zoom":
            self.fit_mode = self.settings.get("fit_mode", "fit")
        self._slider_target = None
        self._need_center = True
        self._clear_edge_armed()
        try:
            if self.fit_mode in ("fit", "width", "original"):
                self._fit_var.set(self.fit_mode)
        except tk.TclError:
            pass

    # ---------- 이미지 로딩 / 표시 ----------
    def _load_pil(self, idx):
        if idx in self._cache:
            return self._cache[idx]
        it = self.items[idx]
        try:
            if it["arc"]:
                with zipfile.ZipFile(it["arc"]) as z:
                    data = z.read(it["arc_name"])
                im = Image.open(io.BytesIO(data))
            else:
                im = Image.open(it["path"])
            im.load()
            if getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1:
                # 애니메이션 원본은 그대로 캐시에 둔다.
                # exif_transpose/convert는 첫 프레임만 남기므로 적용하지 않는다.
                try:
                    im.seek(0)
                except Exception:
                    pass
            else:
                im = ImageOps.exif_transpose(im)
                if im.mode not in ("RGB", "RGBA", "L"):
                    im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            if len(self._cache) > 10:
                # 전체 비우는 대신 가장 오래된 것 1개만 삭제 (메모리·히트율 균형)
                del self._cache[next(iter(self._cache))]
            self._cache[idx] = im
            return im
        except Exception as e:
            self._last_error = "%s: %s" % (it["name"], e)
            return None

    def _redraw(self):
        self._cancel_scheduled_redraw()
        self._stop_animation()
        if not self.items or self.index < 0:
            self._draw_welcome()
            return
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        cw = self.canvas.winfo_width() or self.winfo_screenwidth()
        ch = self.canvas.winfo_height() or self.winfo_screenheight()
        if cw <= 1 or ch <= 1:
            return
        im = self._load_pil(self.index)
        if im is None:
            log_error("render failed: %s" % (self._last_error,))
            return
        animated = bool(getattr(im, "is_animated", False) and
                        getattr(im, "n_frames", 1) > 1)
        if animated:
            try:
                im.seek(0)
            except Exception:
                animated = False
        # 프레임은 RGBA로 변환해 그린다. 원본(im)은 캐시에서 애니메이션 상태를 유지한다.
        frame = im.convert("RGBA") if animated else im
        if self.fit_mode == "fit":
            scale = min(cw / frame.width, ch / frame.height)
        elif self.fit_mode == "width":
            scale = cw / frame.width
        elif self.fit_mode == "original":
            scale = 1.0
        else:  # zoom
            scale = self.zoom
        scale = max(0.01, min(scale, 50))
        nw = max(1, int(frame.width * scale))
        nh = max(1, int(frame.height * scale))
        # 보간기법이 실제로 적용되는 지점: Pillow resize의 resample 인자
        # 키를 누르고 있는 동안은 보간 없이(NEAREST) 빠르게 그린다.
        if self._fast_nav:
            filt = Image.NEAREST
        else:
            filt = INTERPOLATIONS[self.interp_idx][1]
        disp = frame.resize((nw, nh), filt)
        self._disp_size = (disp.width, disp.height)
        try:
            self._photo = ImageTk.PhotoImage(disp, master=self.canvas)
            self.canvas.delete("all")
            # 가운데 정렬. 확대되어 화면보다 크면 스크롤 영역으로 드래그 이동 가능
            x = max(cw // 2, disp.width // 2)
            y = max(ch // 2, disp.height // 2)
            self._canvas_image_id = self.canvas.create_image(x, y, image=self._photo,
                                                             anchor="center")
            self.canvas.config(scrollregion=(0, 0, max(cw, disp.width), max(ch, disp.height)))
        except tk.TclError:
            return
        # 새 이미지/맞춤 변경 시에는 가운데로, 줌 시에는 현재 위치 유지
        if self._need_center:
            self._need_center = False
            self._center_view()
        # 슬라이드바 위치/라벨 동기화
        self._update_slider()
        # 키를 꾹 누르는 동안 이벤트에 밀려 캔버스가 늦게 그려지는 것을 방지
        try:
            self.canvas.update_idletasks()
        except tk.TclError:
            pass
        if animated and not self._fast_nav:
            self._anim_total = im.n_frames
            self._anim_plays = animation_play_count(im)
            self._anim_done = False
            self._start_animation(im)
            self._show_anim_bar()

    # ---------- 애니메이션 재생 ----------
    def _stop_animation(self, hide_bar=True):
        if getattr(self, "_anim_after", None) is not None:
            try:
                self.after_cancel(self._anim_after)
            except Exception:
                pass
        self._anim_after = None
        self._anim_im = None
        if hide_bar:
            self._anim_done = False
            self._hide_anim_bar()

    def _start_animation(self, im):
        self._stop_animation(hide_bar=False)
        if self._fast_nav:
            return
        self._anim_im = im
        self._anim_frame = 0
        self._anim_loops_done = 0
        self._anim_done = False
        self._schedule_anim_tick()

    def _finish_animation(self):
        # 1회/지정 횟수 재생이 끝난 상태. 바는 마지막 프레임에서 멈춰 둔다.
        self._anim_done = True
        self._update_anim_bar()
        self._stop_animation(hide_bar=False)

    def _schedule_anim_tick(self):
        im = self._anim_im
        if im is None:
            return
        try:
            dur = im.info.get("duration") or 100
            delay = max(20, int(dur))
        except Exception:
            delay = 100
        try:
            self._anim_after = self.after(delay, self._anim_tick)
        except tk.TclError:
            self._anim_after = None

    def _anim_tick(self):
        self._anim_after = None
        im = self._anim_im
        if im is None:
            return
        try:
            nxt = self._anim_frame + 1
            if nxt >= im.n_frames:
                if self._anim_plays == 0:  # 무한 반복
                    nxt = 0
                else:
                    self._anim_loops_done += 1
                    if self._anim_loops_done >= self._anim_plays:
                        self._finish_animation()
                        return
                    nxt = 0
            im.seek(nxt)
            self._anim_frame = nxt
            dw, dh = self._disp_size
            if dw <= 0 or dh <= 0 or self._canvas_image_id is None:
                self._stop_animation()
                return
            frame = im.convert("RGBA")
            if (frame.width, frame.height) != (dw, dh):
                frame = frame.resize((dw, dh), INTERPOLATIONS[self.interp_idx][1])
            self._photo = ImageTk.PhotoImage(frame, master=self.canvas)
            self.canvas.itemconfigure(self._canvas_image_id, image=self._photo)
            self._update_anim_bar()
            self._schedule_anim_tick()
        except Exception as e:
            log_error("animation failed: %s" % e)
            self._stop_animation()

    # ---------- 애니메이션 프레임 바 ----------
    def _show_anim_bar(self):
        if getattr(self, "_anim_bar", None) is None:
            return
        if not self._anim_bar_visible:
            try:
                self._anim_bar.place(relx=0.5, rely=1.0, anchor="s",
                                     relwidth=0.33, height=30, y=-6)
            except tk.TclError:
                return
            self._anim_bar_visible = True
            self._reposition_bottom_bar()
        self._update_anim_bar()

    def _hide_anim_bar(self):
        if not getattr(self, "_anim_bar_visible", False):
            return
        try:
            self._anim_bar.place_forget()
        except tk.TclError:
            pass
        self._anim_bar_visible = False
        self._reposition_bottom_bar()

    def _update_anim_bar(self):
        if not getattr(self, "_anim_bar_visible", False):
            return
        try:
            total = max(1, self._anim_total)
            w = self._anim_bar_track.winfo_width()
            if w > 1:
                frac = 1.0 if self._anim_done else min(self._anim_frame + 1, total) / total
                self._anim_bar_track.coords(self._anim_bar_fill, 0, 0,
                                            max(1, int(w * frac)), 4)
            self._anim_bar_label.config(text=self._anim_bar_text())
        except tk.TclError:
            pass

    def _anim_bar_text(self):
        total = max(1, self._anim_total)
        frame = min(self._anim_frame + 1, total)
        if self._anim_done:
            return tr("재생 완료 · %d회") % self._anim_plays
        if self._anim_plays == 0:
            return tr("%d/%d · 무한 반복") % (frame, total)
        if self._anim_plays == 1:
            return tr("%d/%d · 1회 재생") % (frame, total)
        return tr("%d/%d · %d/%d회") % (
            frame, total, min(self._anim_loops_done + 1, self._anim_plays),
            self._anim_plays)

    def _center_view(self):
        # 스크롤 가능한 경우 뷰를 가운데로 (새 이미지/맞춤 변경 시)
        try:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            dw, dh = self._disp_size
            if cw <= 1 or ch <= 1 or dw <= 0 or dh <= 0:
                return
            sr_w = max(cw, dw)
            sr_h = max(ch, dh)
            if sr_w > cw:
                self.canvas.xview_moveto((sr_w - cw) / (2.0 * sr_w))
            else:
                self.canvas.xview_moveto(0)
            if sr_h > ch:
                self.canvas.yview_moveto((sr_h - ch) / (2.0 * sr_h))
            else:
                self.canvas.yview_moveto(0)
        except tk.TclError:
            pass

    def _clear_edge_armed(self):
        self._edge_armed = {}
        self._edge_released = {}

    def _on_pan_key_release(self, dx, dy):
        # 키를 뗀 것을 기록: 끝에 닿아 대기 중이던 방향은 다음 누름에서 이동 허용
        key = (dx, dy)
        if key in self._edge_armed:
            self._edge_released[key] = True
        self._end_fast_nav()

    def _pan_or_navigate(self, dx, dy):
        # 방향키/WASD: 확대 상태면 패닝, 끝에서 키를 뗐다가 다시 눌러야 이전/다음
        if not self.items:
            return
        # 스크롤이 불가능한 상태(맞춤 보기)면 바로 이전/다음 (홀드 반복 이동 허용)
        try:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            dw, dh = self._disp_size
        except tk.TclError:
            return
        scrollable_x = dw > cw + 1
        scrollable_y = dh > ch + 1
        if dx != 0 and not scrollable_x:
            self._fast_nav = True
            self.next() if dx > 0 else self.prev()
            return
        if dy != 0 and not scrollable_y:
            self._fast_nav = True
            self.next() if dy > 0 else self.prev()
            return
        if dx == 0 and dy == 0:
            return
        # 스크롤 시도 전 위치 기록
        try:
            x0 = self.canvas.xview()[0]
            y0 = self.canvas.yview()[0]
            if dx != 0:
                self.canvas.xview_scroll(dx, "units")
            if dy != 0:
                self.canvas.yview_scroll(dy, "units")
            x1 = self.canvas.xview()[0]
            y1 = self.canvas.yview()[0]
        except tk.TclError:
            return
        # 움직였으면 끝 대기 상태 해제 (위치가 바뀜)
        moved = False
        if dx != 0 and abs(x1 - x0) > 1e-9:
            moved = True
        if dy != 0 and abs(y1 - y0) > 1e-9:
            moved = True
        if moved:
            self._clear_edge_armed()
            return
        # 움직이지 않았으면 이미 끝에 닿은 것.
        # 첫 번째 도달에서는 이동하지 않고 대기만 하고,
        # 키를 뗐다가 다시 누른 경우에만 이전/다음으로 이동한다.
        # (키를 계속 누른 채 반복 입력되는 경우 이동하지 않음)
        key = (dx, dy)
        if self._edge_armed.get(key) and self._edge_released.get(key):
            self._clear_edge_armed()
            self._fast_nav = True
            if dx > 0 or dy > 0:
                self.next()
            else:
                self.prev()
        else:
            self._edge_armed[key] = True
            self._edge_released[key] = False

    def _key_navigate(self, fn):
        # 키를 누르고 있는 동안은 보간 없이(NEAREST) 그리도록 표시
        self._fast_nav = True
        fn()

    def _end_fast_nav(self):
        # 키를 떼면 설정된 보간기법으로 최종 화면을 다시 그린다.
        if not self._fast_nav:
            return
        self._fast_nav = False
        self._schedule_redraw()

    # ---------- 이동 / 보기 ----------
    def goto(self, idx):
        if not self.items:
            return
        self.index = max(0, min(len(self.items) - 1, idx))
        self._reset_view()
        self._need_center = True
        self._schedule_redraw()
        self._hide_cursor_now()

    def _schedule_redraw(self):
        # 키 반복 이벤트가 쏟아질 때 매번 로딩하면 화면이 멈춘 것처럼 보인다.
        # 그리기는 한 번만 예약하고, 실행 시점의 최신 index로 그린다.
        if self._render_after is not None:
            return
        try:
            self._render_after = self.after(1, self._run_scheduled_redraw)
        except tk.TclError:
            self._render_after = None

    def _run_scheduled_redraw(self):
        self._render_after = None
        self._redraw()

    def _cancel_scheduled_redraw(self):
        if getattr(self, "_render_after", None) is not None:
            try:
                self.after_cancel(self._render_after)
            except Exception:
                pass
            self._render_after = None

    # ---------- 다음/이전 폴더 이동 ----------
    def _sibling_folders(self):
        # 이동 범위(_nav_root) 안에서 현재 항목과 같은 종류만 넘긴다.
        if not self._current_dir:
            return []
        root = getattr(self, "_nav_root", None) or Path(self._current_dir).parent
        return nav_siblings(root, getattr(self, "next_folder_sort", "name_asc"),
                            kind=nav_kind(self._current_dir))


    def _show_folder_toast(self, folder_path, direction):
        # 폴더/압축파일 이동 시 오른쪽 아래 구석에 작게 2초간 뜨는 팝업 안내
        name = Path(folder_path).name
        if len(name) > 30:
            name = name[:27] + "..."
        label = tr("다음: " if direction > 0 else "이전: ") + name
        self._show_toast_text(label)

    def _show_toast_text(self, label):
        # 오른쪽 아래 구석에 작게 2초간 뜨는 팝업 안내 (임의 문구용)
        try:
            # 같은 문구가 이미 떠 있으면 새 창을 만들지 않고 시간만 연장
            if self._toast is not None and self._toast_label == label:
                if self._toast_after is not None:
                    try:
                        self.after_cancel(self._toast_after)
                    except Exception:
                        pass
                self._toast_after = self.after(2000, self._hide_folder_toast)
                return
            self._hide_folder_toast()
            toast = tk.Toplevel(self)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.configure(bg="#1a1a1a")
            # 포커스를 빼앗지 않음
            try:
                toast.attributes("-toolwindow", True)
            except Exception:
                pass
            lbl = tk.Label(toast, text=label, bg="#1a1a1a", fg="#ffffff",
                           font=("맑은 고딕", 11), padx=14, pady=8)
            lbl.pack()
            toast.update_idletasks()
            w = toast.winfo_reqwidth()
            h = toast.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            toast.geometry("+%d+%d" % (sw - w - 20, sh - h - 20))
            self._toast = toast
            self._toast_label = label
            self._toast_after = self.after(2000, self._hide_folder_toast)
        except Exception:
            pass

    def _hide_folder_toast(self):
        try:
            if self._toast_after is not None:
                try:
                    self.after_cancel(self._toast_after)
                except Exception:
                    pass
                self._toast_after = None
            if self._toast is not None:
                try:
                    self._toast.destroy()
                except Exception:
                    pass
                self._toast = None
            self._toast_label = None
        except Exception:
            pass

    def _go_to_adjacent_folder(self, direction):
        # direction: +1 다음 항목 / -1 이전 항목. 폴더와 압축파일을 같은 순서로 넘긴다.
        siblings = self._sibling_folders()
        if not siblings or not self._current_dir:
            return False
        try:
            cur_resolved = str(Path(self._current_dir).resolve())
        except Exception:
            return False
        if cur_resolved not in siblings:
            return False
        idx = siblings.index(cur_resolved)
        leaving = cur_resolved
        step = 1 if direction > 0 else -1
        j = idx + step
        while 0 <= j < len(siblings):
            target = siblings[j]
            # 이동 범위(_nav_root) 밖으로는 절대 안 나감. 범위를 다 보면 여기서 멈춤.
            if self._load_path(target, from_adjacent=True):
                # 끝까지 본 항목만 목록에 남긴다. 다음 항목 로드가 성공한 뒤 기록.
                remember_viewed_folder(leaving)
                # 다음 폴더로 이동했으면 첫 이미지부터 (이전 폴더는 마지막 이미지부터)
                if direction < 0:
                    self.goto(len(self.items) - 1)
                else:
                    self._schedule_redraw()
                # 구석에 작게 팝업 안내
                self._show_folder_toast(target, direction)
                return True
            # 빈 폴더 / 열기 실패면 건너뛰고 다음 이웃으로
            j += step
        # 더 이상 이동할 곳이 없음 (범위 끝)
        if direction > 0:
            # 마지막 항목을 끝까지 본 뒤 다음을 누른 경우에도 기록
            remember_viewed_folder(self._current_dir)
            self._show_toast_text(tr("마지막 항목입니다"))
        else:
            self._show_toast_text(tr("첫 번째 항목입니다"))
        return False

    def prev(self):
        if self.items:
            if self.index > 0:
                self.goto(self.index - 1)
                return
            # 처음에서 이전
            if self.end_behavior == "loop":
                self.goto(len(self.items) - 1)
            elif self.end_behavior == "next_folder":
                self._go_to_adjacent_folder(-1)
            # stop: 아무것도 안 함

    def next(self):
        if self.items:
            if self.index < len(self.items) - 1:
                self.goto(self.index + 1)
                return
            # 끝에서 다음
            if self.end_behavior == "loop":
                self.goto(0)
            elif self.end_behavior == "next_folder":
                self._go_to_adjacent_folder(1)
            # stop: 아무것도 안 함

    def set_fit(self, mode):
        self.fit_mode = mode
        if mode == "original":
            self.zoom = 1.0
        try:
            if mode in ("fit", "width", "original"):
                self._fit_var.set(mode)
        except tk.TclError:
            pass
        self._need_center = True
        self._redraw()
        self._hide_cursor_now()

    def _toggle_fit_original(self):
        self.set_fit("original" if self.fit_mode == "fit" else "fit")

    # ---------- 줌 / 팬 ----------
    def _on_wheel(self, e):
        # wheel_mode에 따라 휠/Ctrl+휠 역할을 바꾼다.
        ctrl = bool(e.state & 0x0004)
        if self.wheel_mode == "zoom":
            # 휠=줌, Ctrl+휠=이동
            if ctrl:
                if e.delta > 0:
                    self.prev()
                elif e.delta < 0:
                    self.next()
            else:
                self._zoom_step(1.15 if e.delta > 0 else 1 / 1.15)
        else:
            # navigate (기본): 휠=이동, Ctrl+휠=줌
            if ctrl:
                self._zoom_step(1.15 if e.delta > 0 else 1 / 1.15)
            else:
                if e.delta > 0:
                    self.prev()
                elif e.delta < 0:
                    self.next()

    def _on_button_wheel(self, direction, e):
        # Linux Button-4/5
        if getattr(self, "wheel_mode", "navigate") == "zoom":
            self._zoom_step(1.15 if direction < 0 else 1 / 1.15)
        else:
            if direction < 0:
                self.prev()
            else:
                self.next()

    def _on_ctrl_wheel(self, e):
        if getattr(self, "wheel_mode", "navigate") == "zoom":
            if e.delta > 0:
                self.prev()
            elif e.delta < 0:
                self.next()
        else:
            self._zoom_step(1.15 if e.delta > 0 else 1 / 1.15)

    def _zoom_step(self, factor):
        self.fit_mode = "zoom"
        self.zoom = max(0.05, min(self.zoom * factor, 20.0))
        self._clear_edge_armed()
        self._redraw()
        self._hide_cursor_now()

    def _pan_start(self, e):
        self._drag = (e.x, e.y)
        self.canvas.scan_mark(e.x, e.y)

    def _pan_move(self, e):
        if self._drag:
            self.canvas.scan_dragto(e.x, e.y, gain=1)
            # 드래그로 위치가 바뀌면 끝 대기 해제
            self._clear_edge_armed()


# ---------- 탐색기 파일 연결 (Windows) ----------
# 탐색기에서 이미지 더블클릭 시 이 프로그램으로 열리게 하려면,
# EXE를 윈도우에 이미지 뷰어로 등록해야 한다.
#   DalbitViewer.exe --register    등록
#   DalbitViewer.exe --unregister  해제
# install.bat이 이 과정을 한 번에 수행한다.
# HKCU(현재 사용자)만 건드려서 관리자 권한이 필요 없으며,
# 기존 연결의 기본값을 덮지 않고 OpenWith 목록/기본 앱 후보에만 추가한다.
PROG_ID = "DalbitViewer.Image"
APP_REG_NAME = "DalbitViewer"
ASSOC_EXTS = [".bmp", ".jpg", ".jpeg", ".jfif", ".jpe", ".png", ".gif", ".webp",
              ".tiff", ".tif", ".avif", ".ico", ".ppm", ".pgm", ".pnm",
              ".jxl", ".dds", ".tga", ".cbz", ".zip"]
# 압축파일은 우클릭 메뉴에 "달빛뷰어로 열기"를 직접 추가한다(ARCHIVE_EXTS).
# .zip은 기본 앱을 빼앗지 않고, 기존 압축 프로그램 연결을 그대로 둔다.


def print_usage():
    print("달빛뷰어 (UI 없음, 전체화면 전용) v%s" % VERSION)
    print("")
    print("사용법:")
    print("  python main.py [이미지/폴더/압축파일 경로]")
    print("  DalbitViewer.exe [이미지/폴더/압축파일 경로]")
    print("  DalbitViewer.exe --register    탐색기 파일 연결 등록 (Windows)")
    print("  DalbitViewer.exe --unregister  탐색기 파일 연결 해제 (Windows)")
    print("  DalbitViewer.exe --version     버전 확인")
    print("  DalbitViewer.exe --help        이 도움말")
    print("")
    print("탐색기 연결은 install.bat을 더블클릭하면 한 번에 처리됩니다.")


def is_file_association_registered():
    # 압축파일 우클릭 메뉴가 현재 사용자에게 등록돼 있는지 확인한다.
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Classes\SystemFileAssociations\%s\shell\DalbitViewer"
                % sorted(ARCHIVE_EXTS)[0]):
            return True
    except OSError:
        return False


def register_file_association(quiet=False):
    def say(msg):
        if not quiet:
            print(msg)

    if sys.platform != "win32":
        say(tr("파일 연결 등록은 Windows에서만 지원합니다."))
        return 1
    if not getattr(sys, "frozen", False):
        say(tr("파일 연결 등록은 EXE로 빌드한 뒤에 실행하세요."))
        say(tr("먼저 EXE를 만든 뒤 그 파일에서 실행하세요."))
        return 1
    import winreg
    exe = sys.executable
    command = '"%s" "%%1"' % exe

    def reg_set(path, name, value, reg_type=winreg.REG_SZ):
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.SetValueEx(key, name, 0, reg_type, value)
        finally:
            winreg.CloseKey(key)

    try:
        # ProgId: 이 프로그램으로 이미지 여는 방법을 정의
        reg_set(r"Software\Classes\%s" % PROG_ID, "", "달빛뷰어 이미지")
        reg_set(r"Software\Classes\%s" % PROG_ID, "FriendlyTypeName",
                "달빛뷰어 이미지")
        reg_set(r"Software\Classes\%s\DefaultIcon" % PROG_ID, "", '"%s",0' % exe)
        reg_set(r"Software\Classes\%s\shell\open" % PROG_ID, "FriendlyAppName",
                "달빛뷰어")
        reg_set(r"Software\Classes\%s\shell\open\command" % PROG_ID, "", command)
        # Open With 목록에 나타나게 + 기본 앱 후보로 등록
        reg_set(r"Software\Classes\Applications\DalbitViewer.exe", "",
                "달빛뷰어")
        reg_set(r"Software\Classes\Applications\DalbitViewer.exe", "FriendlyAppName",
                "달빛뷰어")
        reg_set(r"Software\Classes\Applications\DalbitViewer.exe\shell\open\command",
                "", command)
        for ext in ASSOC_EXTS:
            reg_set(r"Software\Classes\%s\OpenWithProgids" % ext, PROG_ID, "")
            reg_set(r"Software\Classes\Applications\DalbitViewer.exe\SupportedTypes",
                    ext, "")
        # 우클릭 메뉴에 "달빛뷰어로 열기"를 직접 추가한다.
        # 기본 앱을 바꾸지 않으므로 압축 프로그램 연결을 빼앗지 않는다.
        for ext in ARCHIVE_EXTS:
            open_cmd = r"Software\Classes\SystemFileAssociations\%s\shell\DalbitViewer" % ext
            reg_set(open_cmd, "", "달빛뷰어로 열기")
            reg_set(open_cmd, "Icon", '"%s",0' % exe)
            reg_set(open_cmd + r"\command", "", command)
        # 설정 > 기본 앱에 나타나게 하는 Capabilities 등록
        reg_set(r"Software\DalbitViewer\Capabilities", "ApplicationName",
                "달빛뷰어")
        reg_set(r"Software\DalbitViewer\Capabilities", "ApplicationDescription",
                "UI 없는 전체화면 이미지 뷰어")
        for ext in ASSOC_EXTS:
            reg_set(r"Software\DalbitViewer\Capabilities\FileAssociations",
                    ext, PROG_ID)
        reg_set(r"Software\RegisteredApplications", APP_REG_NAME,
                r"Software\DalbitViewer\Capabilities")
    except OSError as e:
        say(tr("등록 실패: %s") % e)
        return 1
    say(tr("등록 완료: %s") % exe)
    say(tr("연결된 확장자: %s") % " ".join(ASSOC_EXTS))
    say(tr("압축파일은 우클릭 메뉴에서 '달빛뷰어로 열기'로 열 수 있습니다."))
    say(tr("기본 앱으로 지정하려면 Windows 설정 > 기본 앱에서 한 번 선택하세요."))
    return 0


def unregister_file_association(quiet=False):
    def say(msg):
        if not quiet:
            print(msg)

    if sys.platform != "win32":
        say(tr("파일 연결 해제는 Windows에서만 지원합니다."))
        return 1
    import winreg

    def reg_delete_tree(path):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                 winreg.KEY_READ | winreg.KEY_WRITE)
        except FileNotFoundError:
            return
        try:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                except OSError:
                    break
                reg_delete_tree(path + "\\" + sub)
                # 하위 키를 지웠으면 같은 인덱스를 다시 읽어야 함
            winreg.CloseKey(key)
        except OSError:
            pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except OSError:
            pass

    def reg_delete_value(path, name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, name)
            finally:
                winreg.CloseKey(key)
        except OSError:
            pass

    reg_delete_tree(r"Software\Classes\%s" % PROG_ID)
    reg_delete_tree(r"Software\Classes\Applications\DalbitViewer.exe")
    reg_delete_tree(r"Software\DalbitViewer")
    # 구버전(BandiViewStyleViewer) 잔재 정리: 이전 이름으로 등록된 키가 있으면 함께 제거
    reg_delete_tree(r"Software\Classes\BandiViewStyleViewer.Image")
    reg_delete_tree(r"Software\Classes\Applications\BandiViewStyleViewer.exe")
    reg_delete_tree(r"Software\BandiViewStyleViewer")
    reg_delete_value(r"Software\RegisteredApplications", APP_REG_NAME)
    for ext in ASSOC_EXTS:
        reg_delete_value(r"Software\Classes\%s\OpenWithProgids" % ext, PROG_ID)
    for ext in ARCHIVE_EXTS:
        reg_delete_tree(r"Software\Classes\SystemFileAssociations\%s\shell\DalbitViewer" % ext)
    say(tr("파일 연결 해제 완료."))
    return 0


if __name__ == "__main__":
    _arg = sys.argv[1] if len(sys.argv) > 1 else None
    if _arg in ("--help", "-h", "/?", "help"):
        print_usage()
        sys.exit(0)
    if _arg in ("--version", "/version", "-v"):
        print(VERSION)
        sys.exit(0)
    if _arg in ("--register", "/register"):
        sys.exit(register_file_association())
    if _arg in ("--unregister", "/unregister"):
        sys.exit(unregister_file_association())
    try:
        app = Viewer()
        app.mainloop()
    except tk.TclError:
        pass
