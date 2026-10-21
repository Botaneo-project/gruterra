import csv,io,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from ui_table_copy import attach,selected_text
from ui_palette import THEME_CLAIR,THEME_SOMBRE
from i18n import utiliser_langue,traduire_courant as t


class RowCopyTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.addCleanup(self.root.destroy)
        self.table=ttk.Treeview(self.root,columns=('date','value','_id'),show='headings')
        self.table.heading('date',text='Date / heure');self.table.heading('value',text='Humidité (%)')
        self.table.heading('_id',text='hidden')
        self.a=self.table.insert('','end',values=('20/10/2026 21:53:29','0','PRIVATE-ID-A'))
        self.b=self.table.insert('','end',values=('20/10/2026 21:54:00','16','PRIVATE-ID-B'))
        self.table.pack();self.root.update()
    def test_copies_visible_columns_and_zero_in_display_order(self):
        self.table.move(self.b,'',0);self.table.selection_set((self.a,self.b))
        result=selected_text(self.table,('date','value'))
        self.assertNotIn('PRIVATE-ID',result)
        rows=list(csv.reader(io.StringIO(result),delimiter='\t'))
        self.assertEqual(rows[0],['Date / heure','Humidité (%)'])
        self.assertEqual(rows[1][1],'16');self.assertEqual(rows[2][1],'0')
    def test_right_click_preserves_multiple_selection_or_selects_new_row(self):
        controls=attach(self.table,('date','value'),THEME_SOMBRE)
        self.table.selection_set((self.a,self.b));box=self.table.bbox(self.b)
        with patch.object(controls['menu'],'tk_popup'):
            controls['popup'](SimpleNamespace(y=box[1]+box[3]//2,x_root=10,y_root=10))
            self.assertEqual(set(self.table.selection()),{self.a,self.b})
            self.table.selection_set(self.a)
            controls['popup'](SimpleNamespace(y=box[1]+box[3]//2,x_root=10,y_root=10))
            self.assertEqual(self.table.selection(),(self.b,))
    def test_clipboard_and_labels_in_both_languages_and_themes(self):
        for lang in ('fr','en'):
            with utiliser_langue(lang):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    controls=attach(self.table,('date','value'),palette)
                    self.assertEqual(controls['menu'].entrycget(0,'label'),t('table_copy_selected_one'))
                    self.table.selection_set((self.a,self.b));controls['copy']()
                    self.assertEqual(len(self.root.clipboard_get().strip().splitlines()),3)
    def test_empty_selection_does_not_erase_clipboard(self):
        controls=attach(self.table,('date','value'),THEME_CLAIR)
        self.root.clipboard_clear();self.root.clipboard_append('keep')
        controls['copy']();self.assertEqual(self.root.clipboard_get(),'keep')
