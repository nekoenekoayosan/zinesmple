// 公開前に実物素材と抜粋の存在を確認。privateのPDFは一切読まない。
import {existsSync, readFileSync, readdirSync} from 'node:fs';
import {resolve, relative} from 'node:path';
import {cards} from '../config.js';
const root=resolve('public');
function checkImage(image) {
  if (typeof image !== 'string' || !image.startsWith('/assets/')) throw Error('公開素材は /assets/ 配下で指定してください');
  const path=resolve(root,image.slice(1));
  if (relative(root,path).startsWith('..') || !existsSync(path)) throw Error(`公開素材がありません: public${image}`);
}
for (const card of cards) checkImage(card.image);
const manifestPath=resolve(root,'assets/sample/manifest.json');
if(!existsSync(manifestPath)) throw Error('試し読み画像がありません。MacでPDFを変換し、public/assets/sample/ をGitHubへpushしてください。');
const pages=JSON.parse(readFileSync(manifestPath,'utf8'));
if(!pages.length||pages[0].label!=='表紙'||pages.at(-1).label!=='裏表紙')throw Error('公開用の表紙・裏表紙を確認してください');
for(const page of pages) if(page.type!=='gap')checkImage(page.image);
function walk(path){for(const entry of readdirSync(path,{withFileTypes:true})){const p=resolve(path,entry.name);if(entry.isDirectory())walk(p);else if(entry.name.toLowerCase().endsWith('.pdf'))throw Error(`公開先にPDFを置かないでください: ${p}`);}}
walk(root);
console.log('公開用カード・試し読み画像・PDF非公開を確認しました。');
