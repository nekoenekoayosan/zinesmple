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
    # 公開番号はPDF内の位置ではなく、冊子のノンブル（表紙1・裏表紙16）。
    pdf_groups = config.get('pdf_groups')
    pdf_mode = pdf_groups is not None
    cover_number = config.get('cover_pdf_page', 2) if pdf_mode else 1
    back_number = config.get('back_pdf_page', 1) if pdf_mode else 16
    visible = config.get('visible_pages')
    if pdf_mode:
        if not isinstance(pdf_groups, list) or not all(
            isinstance(g, list) and len(g) in (1,2)
            and all(type(n) is int and 1 <= n <= 16 for n in g)
            and (len(g) == 1 or g[1] == g[0]+1) for g in pdf_groups
        ):
            raise ValueError('pdf_groups は [[3,4],[5,6],[7],[15,16]] のようにPDFのページ番号で指定します。')
        all_numbers = [cover_number, back_number]+[n for g in pdf_groups for n in g]
        if not all(type(n) is int and 1 <= n <= 16 for n in all_numbers) or len(set(all_numbers)) != len(all_numbers):
            raise ValueError('表紙・裏表紙・本文のPDFページ番号は重複せず1〜16で指定してください。')
        groups = pdf_groups
    elif visible is not None:
        if not isinstance(visible, list) or not all(type(n) is int and 2 <= n <= 15 for n in visible) or len(set(visible)) != len(visible):
            raise ValueError('visible_pages は重複のない本文ページ番号2〜15の配列です。')
        groups = []
        i = 0
        while i < len(visible):
            n = visible[i]
            if n % 2 == 0 and i+1 < len(visible) and visible[i+1] == n+1:
                groups.append([n,n+1])
                i += 2
            else:
                groups.append([n])
                i += 1
    else:
        # 以前のpage_pairs / spreads設定も使えます。
        groups = config.get('page_pairs')
        if groups is None:
            groups = [[2*n-2, 2*n-1] for n in config.get('spreads', [2, 4])]
        if not isinstance(groups, list) or not all(
            isinstance(pair, list) and len(pair) == 2
            and all(type(n) is int for n in pair)
            and 2 <= pair[0] <= 14 and pair[0] % 2 == 0 and pair[1] == pair[0]+1
            for pair in groups
        ) or len({tuple(p) for p in groups}) != len(groups):
            raise ValueError('page_pairs は [[2,3],[6,7]] のように、本文の見開きを重複なく指定してください。')
    output = public / 'assets/sample'
    manifest = []
    with fitz.open(source) as doc:
        layout = config.get('layout', 'auto')
        if layout == 'auto':
            layout = {16: 'single', 8: 'printer_spreads'}.get(len(doc))
        if layout not in ('single', 'printer_spreads') or len(doc) != (16 if layout == 'single' else 8):
            raise ValueError(f'PDFは{len(doc)}ページです。16ページの単ページ版または8ページの印刷見開き版に対応しています。')
        if pdf_mode and layout != 'single':
            raise ValueError('pdf_groups は16ページの単ページPDF用です。印刷見開き版にはvisible_pagesを使ってください。')
        order = list(range(1,17)) if pdf_mode else config.get('pdf_page_order', list(range(1,17)))
        if layout == 'single' and (not isinstance(order, list) or len(order) != 16 or not all(type(n) is int for n in order) or sorted(order) != list(range(1,17))):
            raise ValueError('pdf_page_order はPDFの先頭から順に、冊子番号1〜16を一度ずつ指定してください。')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
            tmp = Path(tmp)

            def clip_for(number):
                if layout == 'single':
                    index, side = order.index(number), None
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
                        if kind in ('spread', 'page'):
                            for y in (.28, .68):
                                page.insert_text((x+width*.12, height*y), 'SAMPLE',
                                                 fontsize=width*.19, color=(.88,.38,.57), fill_opacity=.28)
                        x += width
                    page.get_pixmap(dpi=config.get('dpi',160), alpha=False).save(tmp / filename)
                manifest.append({'type':kind, 'image':f'/assets/sample/{filename}', 'label':label, 'provisional':False})

            export([cover_number], 'cover.png', '表紙', 'cover')
            previous = cover_number
            for numbers in groups:
                first, last = numbers[0], numbers[-1]
                if first != previous+1:
                    manifest.append({'type':'gap', 'label':'続きは冊子で'})
                if len(numbers) == 2:
                    export(numbers, f'spread-{first}-{last}.png', f'{first}–{last}ページ', 'spread')
                else:
                    export(numbers, f'page-{first}.png', f'{first}ページ', 'page')
                previous = last
            if previous != (16 if pdf_mode else 15):
                manifest.append({'type':'gap', 'label':'続きは冊子で'})
            export([back_number], 'back.png', '裏表紙', 'cover')
            (tmp / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            if output.exists(): shutil.rmtree(output)
            shutil.copytree(tmp, output)
    return len(groups)+2, layout


if __name__ == '__main__':
    try:
        config = json.loads((ROOT / 'scripts/sample-selection.json').read_text(encoding='utf-8'))
        count, layout = export_sample(config)
        print(f'{"16ページ単ページ版" if layout == "single" else "8ページ印刷見開き版"}として読み込みました。')
        print(f'公開用画像 {count} 枚を書き出しました。元PDFはコピーしていません。')
    except (ValueError, OSError, fitz.FileDataError) as error:
        raise SystemExit(str(error))
