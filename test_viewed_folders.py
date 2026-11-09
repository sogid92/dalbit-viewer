"""열람한 폴더 목록의 순수 로직 테스트: python -m unittest test_viewed_folders -v"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main


class ViewedFoldersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dalbit-viewed-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.json_path = self.tmp / "viewed_folders.json"
        patcher = mock.patch.object(main, "viewed_folders_path", return_value=self.json_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_remember_dedupes_and_moves_to_front(self):
        a = self.tmp / "a"
        b = self.tmp / "b"
        a.mkdir()
        b.mkdir()
        main.remember_viewed_folder(a)
        main.remember_viewed_folder(b)
        main.remember_viewed_folder(a)
        self.assertEqual(main.load_viewed_folders(), [str(a.resolve()), str(b.resolve())])

    def test_prune_removes_deleted_and_descendants(self):
        a = self.tmp / "a"
        b = a / "b"
        c = self.tmp / "c"
        b.mkdir(parents=True)
        c.mkdir()
        main.save_viewed_folders([str(a), str(b), str(c)])
        main.prune_viewed_folders([str(a)])
        self.assertEqual(main.load_viewed_folders(), [str(c)])

    def test_drop_nested_keeps_ancestor(self):
        a = self.tmp / "a"
        b = a / "b"
        c = self.tmp / "c"
        b.mkdir(parents=True)
        c.mkdir()
        kept = main.drop_nested_paths([str(b), str(a), str(c)])
        self.assertEqual(kept, [str(a), str(c)])

    def test_deletion_guard_blocks_system_paths(self):
        self.assertTrue(main.deletion_block_reason(Path.home()))
        self.assertTrue(main.deletion_block_reason(Path(Path.home().anchor)))
        self.assertTrue(main.deletion_block_reason(Path(main.__file__).resolve().parent))
        if os.name == "nt":
            self.assertTrue(main.deletion_block_reason(Path(tempfile.gettempdir())))

    def test_deletion_guard_allows_normal_folder(self):
        allowed = Path(tempfile.mkdtemp(prefix="dalbit-guard-ok-", dir=str(Path.home())))
        self.addCleanup(shutil.rmtree, allowed, True)
        self.assertIsNone(main.deletion_block_reason(allowed))


if __name__ == "__main__":
    unittest.main()
