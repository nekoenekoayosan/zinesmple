"""16ページ単ページ版／8ページ印刷見開き版から公開用抜粋だけを生成。"""
import json
import shutil
import tempfile
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parent.parent


def export_sample(config, root=ROOT):
    source = (root / config['source']).resolve()
    public = (root / 'public').resolve()
    if source.is_relative_to(public):
        raise ValueError('完全版PDFは public の外、private/ に置いてください。')
    # page_pairs は冊子のページ番号。旧設定のspreadsも引き続き対応。
    pairs = config.get('page_pairs')
    if pairs is None:
        pairs = [[2*n-2, 2*n-1] for n in config.get('spreads', [2, 4])]
    if not isinstance(pairs, list) or not all(
        isinstance(pair, list) and len(pair) == 2
        and all(type(n) is int for n in pair)
        and 2 <= pair[0] <= 14 and pair[0] % 2 == 0 and pair[1] == pair[0]+1
        for pair in pairs
    ) or len({tuple(p) for p in pairs}) != len(pairs):
        raise ValueError('page_pairs は [[2,3],[6,7]] のように、本文の見開きを重複なく指定してください。')
    output = public / 'assets/sample'
    manifest = []
    with fitz.open(source) as doc:
        layout = config.get('layout', 'auto')
        if layout == 'auto':
            layout = {16: 'single', 8: 'printer_spreads'}.get(len(doc))
        if layout not in ('single', 'printer_spreads') or len(doc) != (16 if layout == 'single' else 8):
            raise ValueError(f'PDFは{len(doc)}ページです。16ページの単ページ版（1〜16の順）または8ページの印刷見開き版に対応しています。')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
            tmp = Path(tmp)

            def clip_for(number):
                if layout == 'single':
                    index, side = number-1, None
                elif number in (1, 16):
                    index, side = 0, 'right' if number == 1 else 'left'
                else:
                    index, side = number//2, 'left' if number % 2 == 0 else 'right'
                rect = fitz.Rect(doc[index].rect)
                mid = (rect.x0 + rect.x1) / 2
                if side == 'right': rect.x0 = mid
                if side == 'left': rect.x1 = mid
                return index, rect

            def export(numbers, filename, label, kind):
                clips = [clip_for(n) for n in numbers]
                height = max(rect.height for _, rect in clips)
                widths = [rect.width * height / rect.height for _, rect in clips]
                with fitz.open() as out:
                    page = out.new_page(width=sum(widths), height=height)
                    x = 0
                    for (index, rect), width in zip(clips, widths):
                        target = fitz.Rect(x, 0, x+width, height)
                        page.show_pdf_page(target, doc, index, clip=rect)
                        if kind == 'spread':
                            for y in (.28, .68):
                                page.insert_text((x+width*.12, height*y), 'SAMPLE',
                                                 fontsize=width*.19, color=(.88,.38,.57), fill_opacity=.28)
                        x += width
                    page.get_pixmap(dpi=config.get('dpi',160), alpha=False).save(tmp / filename)
                manifest.append({'type':kind, 'image':f'/assets/sample/{filename}', 'label':label, 'provisional':False})

            export([1], 'cover.png', '表紙', 'cover')
            previous = 1
            for first, last in pairs:
                if first != previous+1:
                    manifest.append({'type':'gap', 'label':'続きは冊子で'})
                export([first,last], f'spread-{first}-{last}.png', f'{first}–{last}ページ', 'spread')
                previous = last
            if previous != 15:
                manifest.append({'type':'gap', 'label':'続きは冊子で'})
            export([16], 'back.png', '裏表紙', 'cover')
            (tmp / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            if output.exists(): shutil.rmtree(output)
            shutil.copytree(tmp, output)
    return len(pairs)+2, layout


if __name__ == '__main__':
    try:
        config = json.loads((ROOT / 'scripts/sample-selection.json').read_text(encoding='utf-8'))
        count, layout = export_sample(config)
        print(f'{"16ページ単ページ版" if layout == "single" else "8ページ印刷見開き版"}として読み込みました。')
        print(f'公開用画像 {count} 枚を書き出しました。元PDFはコピーしていません。')
    except (ValueError, OSError, fitz.FileDataError) as error:
        raise SystemExit(str(error))
