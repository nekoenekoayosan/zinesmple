import json
import tempfile
import unittest
from pathlib import Path
import fitz
from export_sample import export_sample


class ExportTest(unittest.TestCase):
    def fixture(self, root, single, order=None):
        (root/'private').mkdir(exist_ok=True)
        with fitz.open() as doc:
            for numbers in ([[n] for n in (order or range(1,17))] if single else [[16,1]]+[[n,n+1] for n in range(2,16,2)]):
                page = doc.new_page(width=128*len(numbers),height=182)
                for side,n in enumerate(numbers):
                    page.draw_rect(fitz.Rect(side*128,0,(side+1)*128,182), fill=(n/20,.2,.3), color=None)
                    page.insert_text((side*128+20,90),str(n),fontsize=24)
            doc.save(root/'private/book.pdf')

    def test_both_formats_and_order(self):
        for single in (True,False):
            with self.subTest(single=single), tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                self.fixture(root,single)
                config={'source':'private/book.pdf','layout':'auto','page_pairs':[[6,7],[2,3]],'dpi':72}
                count,layout=export_sample(config,root)
                self.assertEqual(count,4)
                self.assertEqual(layout,'single' if single else 'printer_spreads')
                out=root/'public/assets/sample'
                manifest=json.loads((out/'manifest.json').read_text())
                self.assertEqual([p['label'] for p in manifest],['表紙','続きは冊子で','6–7ページ','続きは冊子で','2–3ページ','続きは冊子で','裏表紙'])
                for filename,nums in [('cover.png',[1]),('back.png',[16]),('spread-6-7.png',[6,7]),('spread-2-3.png',[2,3])]:
                    pix=fitz.Pixmap(out/filename)
                    self.assertEqual((pix.width,pix.height),(128*len(nums),182))
                    for i,n in enumerate(nums):
                        self.assertLessEqual(abs(pix.pixel(i*128+2,2)[0]-int(n/20*255)),1)
                self.assertEqual(len(list(out.glob('*.png'))),4)
                self.assertFalse(list((root/'public').rglob('*.pdf')))
                # Re-export must remove previously public excerpts.
                config['page_pairs']=[]
                export_sample(config,root)
                self.assertFalse((out/'spread-6-7.png').exists())

    def test_back_first_and_private_pages(self):
        order = [16]+list(range(1,16))
        for single in (True, False):
            with self.subTest(single=single), tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                self.fixture(root,single,order)
                config={'source':'private/book.pdf', 'pdf_page_order':order,
                        'visible_pages':[2,3,4,5,6,7,15], 'dpi':72}
                count,_=export_sample(config,root)
                out=root/'public/assets/sample'
                manifest=json.loads((out/'manifest.json').read_text())
                self.assertEqual(count,6)
                self.assertEqual([p['label'] for p in manifest],
                    ['表紙','2–3ページ','4–5ページ','6–7ページ','続きは冊子で','15ページ','裏表紙'])
                for filename,nums in [('cover.png',[1]),('back.png',[16]),
                        ('spread-2-3.png',[2,3]),('spread-4-5.png',[4,5]),
                        ('spread-6-7.png',[6,7]),('page-15.png',[15])]:
                    pix=fitz.Pixmap(out/filename)
                    self.assertEqual((pix.width,pix.height),(128*len(nums),182))
                    for i,n in enumerate(nums):
                        self.assertLessEqual(abs(pix.pixel(i*128+2,2)[0]-int(n/20*255)),1)
                self.assertEqual(len(list(out.glob('*.png'))),6)
                self.assertFalse(list((root/'public').rglob('*.pdf')))
                # 15ページだけに切り出すため、同じ印刷見開きの14ページも出力しない。
                self.assertFalse((out/'spread-14-15.png').exists())

    def test_legacy_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.fixture(root,False)
            export_sample({'source':'private/book.pdf','spreads':[2,4],'dpi':72},root)
            self.assertTrue((root/'public/assets/sample/spread-6-7.png').exists())


if __name__=='__main__': unittest.main()
