import { PageFlip } from 'page-flip';

// PDFの公開見開きは画像を差し替えず、表示時だけ左右の紙面に分ける。
export function createReader(initialPages) {
  const $ = s => document.querySelector(s);
  let pages = initialPages, leaves = [], book;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function paper(p) {
    if (p.type === 'gap') return '<div class="gap"><span>✦</span><h3>続きは冊子で</h3><p>この間のページは省略しています</p></div>';
    return `<div class="paper ${p.type}"><img src="${p.image}" alt="${p.label}">${['spread', 'page'].includes(p.type) ? '<span class="watermark">SAMPLE</span>' : ''}${p.provisional ? '<span class="placeholder">仮素材</span>' : ''}</div>`;
  }
  function centerCover(index) {
    if (!book) return;
    const single = book.getOrientation() === 'portrait';
    const shift = single ? 0 : book.getBoundsRect().pageWidth / 2 * (index === 0 ? -1 : index >= leaves.length - 1 ? 1 : 0);
    $('#flipBook').style.setProperty('--cover-shift', `${shift}px`);
  }
  function update(index) {
    centerCover(index);
    const source = leaves[index]?.source ?? 0;
    $('#pageLabel').textContent = pages[source].label;
    $('#pageCount').textContent = `${String(source + 1).padStart(2, '0')} / ${String(pages.length).padStart(2, '0')}`;
    $('#prev').disabled = index === 0;
    $('#next').disabled = index >= leaves.length - 1;
    $('#zoom').disabled = pages[source].type === 'gap';
    $('#readerProgress').value = source + 1;
    $('#readerProgress').max = pages.length;
  }
  function load(nextPages) {
    pages = nextPages;
    leaves = pages.flatMap((p, source) => p.type === 'spread'
      ? [{...p, source, half: 'left'}, {...p, source, half: 'right'}]
      : ['gap', 'page'].includes(p.type) ? [{...p, source}, {...p, source, quiet: true}] : [{...p, source}]);
    if (leaves.length % 2) leaves.splice(leaves.length - 1, 0, {type: 'gap', label: '余白', source: pages.length - 2, quiet: true});
    if (book) book.destroy();
    $('#pageStage').innerHTML = '<div id="flipBook"></div>';
    $('#flipBook').innerHTML = leaves.map(p => `<div class="book-leaf ${p.half ? 'leaf-' + p.half : ''}" aria-label="${p.label}">${p.quiet ? '<div class="quiet-page"><span>✦</span></div>' : paper(p)}<span class="leaf-edge"></span></div>`).join('');
    book = new PageFlip($('#flipBook'), {
      width: 384, height: 546, size: 'stretch', minWidth: 280, maxWidth: 550,
      minHeight: 185, maxHeight: 782, showCover: true, usePortrait: true,
      autoSize: false, drawShadow: true, maxShadowOpacity: .28,
      flippingTime: reduced ? 1 : 750, mobileScrollSupport: true,
      swipeDistance: 35, showPageCorners: !reduced, useMouseEvents: true,
    });
    book.on('flip', e => update(e.data));
    book.on('changeOrientation', () => requestAnimationFrame(() => centerCover(book.getCurrentPageIndex())));
    book.loadFromHTML(document.querySelectorAll('#flipBook .book-leaf'));
    update(0);
  }
  $('#prev').onclick = () => book.flipPrev('top');
  $('#next').onclick = () => book.flipNext('bottom');
  $('.reader').onkeydown = e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      e.key === 'ArrowRight' ? book.flipNext('bottom') : book.flipPrev('top');
    }
  };
  $('#zoom').onclick = () => {
    const source = leaves[book.getCurrentPageIndex()]?.source ?? 0;
    $('#zoomContent').innerHTML = paper(pages[source]);
    $('#zoomDialog').showModal();
  };
  $('#closeZoom').onclick = () => $('#zoomDialog').close();
  window.addEventListener('resize', () => requestAnimationFrame(() => centerCover(book.getCurrentPageIndex())));
  load(pages);
  return { load };
}
