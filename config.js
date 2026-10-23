import {assetUrl} from './asset-url.js';
// 商品・公開素材の設定はここにまとめます。完全版PDFは public に置かないでください。
export const product = { title: 'ふたりのおまじない', price: 500, priceNote: '予定価格', copies: 30, dmUrl: null };
export const cards = [{ id: 'one', name: 'おまじないカード 01', image: '/assets/card-01.png', provisional: false }];
// export_sample.py が生成する /assets/sample/manifest.json があれば優先して読み込みます。
export const samplePages = [
 {type:'cover', image:'/assets/cover.svg', label:'表紙', provisional:true},
 {type:'spread', image:'/assets/spread.svg', label:'本文の仮レイアウト', provisional:true},
 {type:'gap', label:'続きは冊子で'},
 {type:'cover', image:'/assets/back.svg', label:'裏表紙', provisional:true}
];
export const backgrounds = [
 {name:'午後の公園', image:'/assets/park.svg', provisional:true},
 {name:'喫茶のテーブル', image:'/assets/cafe.svg', provisional:true}
];
// 自作イラスト。許可済みの透過PNG等への差し替えも可能。
export const hand = { image: '/assets/hand.svg', provisional: true };
export const booklet = { cover: '/assets/cover.svg', provisional: true };

// 公開先のサブディレクトリは自動反映。素材設定は /assets/... のままでOK。
for (const entry of [...cards, ...samplePages, ...backgrounds]) {
  if (entry.image) entry.image = assetUrl(entry.image);
}
hand.image = assetUrl(hand.image);
booklet.cover = assetUrl(booklet.cover);
