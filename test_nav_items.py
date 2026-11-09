"""폴더/압축파일 순서 이동 로직 테스트: python -m unittest test_nav_items -v"""
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import main


class NavItemsTest(unittest.TestCase):
    def setUp(self):
        # 삭제 안전 검사가 LOCALAPPDATA 아래를 막으므로 홈 아래에 만든다.
        self.tmp = Path(tempfile.mkdtemp(prefix="dalbit-nav-test-", dir=str(Path.home())))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        page = self.tmp / "p.png"
        page.write_bytes(b"x")
        (self.tmp / "a").mkdir()
        (self.tmp / "c").mkdir()
        for name, stamp in (("b.cbz", 1000), ("d.cbz", 2000)):
            with zipfile.ZipFile(self.tmp / name, "w") as z:
                z.write(page, "1.png")
            os.utime(self.tmp / name, (stamp, stamp))

    def names(self, mode):
        return [Path(p).name for p in main.nav_siblings(self.tmp, mode)]

    def test_mixes_folders_and_archives(self):
        self.assertEqual(self.names("name_asc"), ["a", "b.cbz", "c", "d.cbz"])

    def test_name_desc(self):
        self.assertEqual(self.names("name_desc"), ["d.cbz", "c", "b.cbz", "a"])

    def test_mtime_sorts_archives_by_date(self):
        self.assertEqual(self.names("mtime_asc")[:2], ["b.cbz", "d.cbz"])

    def test_ignores_other_files(self):
        (self.tmp / "notes.txt").write_text("x", encoding="utf-8")
        self.assertNotIn("notes.txt", self.names("name_asc"))

    def test_archive_is_deletable(self):
        self.assertIsNone(main.deletion_block_reason(self.tmp / "b.cbz"))

    def test_other_file_is_not_deletable(self):
        notes = self.tmp / "notes.txt"
        notes.write_text("x", encoding="utf-8")
        self.assertIsNotNone(main.deletion_block_reason(notes))

    def test_missing_path_is_blocked(self):
        self.assertIsNotNone(main.deletion_block_reason(self.tmp / "nope.cbz"))

    def test_archive_inside_selected_folder_is_dropped(self):
        kept = main.drop_nested_paths([str(self.tmp / "b.cbz"), str(self.tmp)])
        self.assertEqual(kept, [str(self.tmp.resolve())])

    def test_sibling_archives_both_kept(self):
        kept = main.drop_nested_paths([str(self.tmp / "b.cbz"), str(self.tmp / "d.cbz")])
        self.assertEqual(len(kept), 2)


if __name__ == "__main__":
    unittest.main()
