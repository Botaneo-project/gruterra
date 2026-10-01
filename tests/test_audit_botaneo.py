import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "audit_botaneo.py"


def charger_audit():
    spec = importlib.util.spec_from_file_location("audit_botaneo_module_test", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestAuditBotaneo(unittest.TestCase):
    def test_executer_retourne_vrai_sur_commande_ok(self):
        audit = charger_audit()
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            ok = audit.executer("commande ok", [sys.executable, "-c", "pass"])
        self.assertTrue(ok)
        self.assertIn("OK : commande ok", sortie.getvalue())

    def test_executer_retourne_faux_sur_commande_en_echec(self):
        audit = charger_audit()
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            ok = audit.executer("commande ko", [sys.executable, "-c", "raise SystemExit(3)"])
        self.assertFalse(ok)
        self.assertIn("ECHEC : commande ko", sortie.getvalue())

    def test_afficher_status_git_accepte_git_absent(self):
        audit = charger_audit()
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            audit.afficher_status_git(None)
        self.assertEqual(sortie.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
