import ast,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))

class DashboardCallbackTests(unittest.TestCase):
    def test_plant_button_imports_its_palette_dependency(self):
        path=Path(__file__).resolve().parents[1]/'_app/interface.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        callback=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='ouvrir_suivi_connecte')
        from meteo_nappes import PALETTE
        messages=Mock()
        scope={**PALETTE,'root':object(),'plante_id':1,'messagebox':messages,'t':lambda k:k}
        # No meteo_nappes global: the home screen imports it in a different scope.
        exec(compile(ast.Module(body=[callback],type_ignores=[]),str(path),'exec'),scope)
        with patch('home_assistant_dashboard.open_window') as opening:
            scope['ouvrir_suivi_connecte']()
        opening.assert_called_once_with(scope['root'],PALETTE,plant_id=1)
        messages.showerror.assert_not_called()

if __name__=='__main__':unittest.main()
