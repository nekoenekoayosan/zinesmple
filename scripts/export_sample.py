"""印刷見開きPDFから、選択された公開画像だけを生成する。完全版PDFは配信しない。"""
import json
import shutil
import tempfile
from pathlib import Path
import fitz
ROOT = Path(__file__).resolve().parent.parent
config = json.loads((ROOT / 'scripts/sample-selection.json').read_text())
source = (ROOT / config['source']).resolve()
public = (ROOT / 'public').resolve()
if source.is_relative_to(public):
    raise SystemExit('完全版PDFは public の外、private/ に置いてください。')
spreads = config['spreads']
if not all(isinstance(n, int) and 2 <= n <= 8 for n in spreads) or len(set(spreads)) != len(spreads):
    raise SystemExit('spreads は重複のないPDFページ番号2〜8の配列です。')
doc = fitz.open(source)
if len(doc) != 8:
    raise SystemExit('この設定は8ページの印刷見開きPDF用です。')
output = public / 'assets/sample'
output.parent.mkdir(parents=True, exist_ok=True)
manifest = []
with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
    tmp = Path(tmp)
    def export(index, filename, label, kind, half=None):
        page = doc[index]
        rect = fitz.Rect(page.rect)
        if half == 'right': rect.x0 = (rect.x0 + rect.x1) / 2
        if half == 'left': rect.x1 = (rect.x0 + rect.x1) / 2
        # 公開用に別文書へクリップ。透かしも画像そのものへ焼き込む。
        out = fitz.open()
        p = out.new_page(width=rect.width, height=rect.height)
        p.show_pdf_page(p.rect, doc, index, clip=rect)
        if kind == 'spread':
            for y in (.28, .68):
                p.insert_text((p.rect.width*.12,p.rect.height*y), 'SAMPLE',
                              fontsize=p.rect.width*.13, color=(.88,.38,.57), fill_opacity=.28)
        p.get_pixmap(dpi=config.get('dpi',160), alpha=False).save(tmp / filename)
        out.close()
        manifest.append({'type':kind,'image':f'/assets/sample/{filename}','label':label,'provisional':False})
    export(0,'cover.png','表紙','cover','right')
    previous = 1
    for n in spreads:
        first = 2*n-2
        if first != previous+1:
            manifest.append({'type':'gap','label':'続きは冊子で'})
        export(n-1,f'spread-{n}.png',f'{first}–{first+1}ページ','spread')
        previous = first+1
    if previous != 15:
        manifest.append({'type':'gap','label':'続きは冊子で'})
    export(0,'back.png','裏表紙','cover','left')
    (tmp / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    # 古い公開ページを残さず、今回の抜粋だけを置く。
    if output.exists(): shutil.rmtree(output)
    shutil.copytree(tmp,output)
print(f'公開用画像 {len(spreads)+2} 枚を書き出しました。元PDFはコピーしていません。')
