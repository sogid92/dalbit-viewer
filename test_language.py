import unittest

import main


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        main.set_language("ko")

    def test_english_translation(self):
        main.set_language("en")
        self.assertEqual(main.tr("설정"), "Settings")
        self.assertEqual(main.tr("파일 ▾"), "File ▾")
        self.assertEqual(main.tr("알 수 없는 문구"), "알 수 없는 문구")

    def test_korean_passthrough(self):
        main.set_language("ko")
        self.assertEqual(main.tr("설정"), "설정")

    def test_invalid_language_falls_back_to_korean(self):
        main.set_language("fr")
        self.assertEqual(main.tr("설정"), "설정")

    def test_system_language_is_supported(self):
        self.assertIn(main.detect_system_language(), ("ko", "en"))

    def test_ui_strings_are_translated(self):
        main.set_language("en")
        untranslated = [k for k in main.TRANSLATIONS if main.tr(k) == k]
        self.assertEqual(untranslated, [])


if __name__ == "__main__":
    unittest.main()
