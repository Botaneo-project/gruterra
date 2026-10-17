from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import ui_palette as p
from vue_historique import THEME_CLAIR, THEME_SOMBRE

class PaletteTests(unittest.TestCase):
    def test_history_uses_every_main_palette_value(self):
        for base, history in [(p.THEME_CLAIR, THEME_CLAIR), (p.THEME_SOMBRE, THEME_SOMBRE)]:
            for key, value in base.items():
                self.assertEqual(history[key], value)
            self.assertEqual(history['GRID'], base['BORDER'])
    def test_selection_text_for_both_themes(self):
        self.assertEqual(p.readable_text(p.THEME_CLAIR['GREEN']), '#FFFFFF')
        self.assertEqual(p.readable_text(p.THEME_SOMBRE['GREEN']), '#000000')
        self.assertEqual(p.readable_text('#FFFFFF'), '#000000')
        self.assertEqual(p.readable_text('#000000'), '#FFFFFF')

if __name__ == '__main__':
    unittest.main()
