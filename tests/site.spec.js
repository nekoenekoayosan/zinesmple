import {test,expect} from '@playwright/test';
for(const width of [320,390,1440])test(`表示幅 ${width}px`,async({page})=>{await page.setViewportSize({width,height:900});await page.goto('/');await expect(page.locator('h1')).toContainText('おまじない');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();});
test('試し読み・拡大・持ち歩き・PNG保存',async({page})=>{const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');await expect(page.locator('#prev')).toBeDisabled();await page.locator('#next').click();await expect(page.locator('#pageLabel')).toHaveText('3–4ページ');await expect(page.locator('.watermark').first()).toHaveText('SAMPLE');await page.locator('#zoom').click();await expect(page.locator('#zoomDialog')).toBeVisible();await expect(page.locator('#zoomContent img')).toBeVisible();await page.locator('#closeZoom').click();for(let i=0;i<8&&await page.locator('#pageLabel').textContent()!=='続きは冊子で';i++){await page.waitForTimeout(850);await page.locator('#next').click();await page.waitForTimeout(850);}await expect(page.locator('#pageLabel')).toHaveText('続きは冊子で');await page.locator('[data-scene=wallet]').click();await page.locator('#toggleCard').click();await expect(page.locator('#objectStage')).toHaveClass(/is-wallet is-out/);await page.locator('[data-bg="1"]').click();await page.locator('#angle').fill('20');await page.waitForFunction(()=>{const c=document.querySelector('canvas');return c.getContext('2d').getImageData(450,800,1,1).data[3]>0;});const downloadPromise=page.waitForEvent('download');await page.locator('#save').click();const d=await downloadPromise;expect(d.suggestedFilename()).toBe('futari-no-omajinai-story.png');await expect(page.locator('#saveStatus')).toContainText('保存しました');expect(errors).toEqual([]);await page.screenshot({path:`/tmp/zine-${test.info().project.name}.png`,fullPage:true});});
test('スワイプ・写真アップロード・リセット',async({page})=>{await page.goto('/');await page.evaluate(()=>{const target=document.querySelector('#flipBook .stf__block');const rect=target.getBoundingClientRect();for(const [type,x,y] of [['touchstart',300,200],['touchend',100,205]]){const touch=new Touch({identifier:1,target,clientX:rect.left+x,clientY:rect.top+100+y*.05});target.dispatchEvent(new TouchEvent(type,{changedTouches:[touch],bubbles:true}));}});await expect(page.locator('#pageLabel')).toHaveText('3–4ページ');await page.locator('#upload').setInputFiles('public/assets/cafe.svg');await page.locator('#posX').fill('80');await page.locator('#scale').fill('90');await page.locator('#reset').click();await expect(page.locator('#posX')).toHaveValue('50');await expect(page.locator('#scale')).toHaveValue('72');await page.waitForFunction(()=>document.querySelector('#photoCanvas').getContext('2d').getImageData(450,800,1,1).data[3]>0);const pending=page.waitForEvent('download');await page.locator('#save').click();const d=await pending;const stream=await d.createReadStream();const chunks=[];for await(const chunk of stream)chunks.push(chunk);const bytes=Buffer.concat(chunks);expect(bytes.readUInt32BE(16)).toBe(900);expect(bytes.readUInt32BE(20)).toBe(1600);});
test('最初に大きな試し読み・紙の端のドラッグ',async({page})=>{
 await page.goto('/');
 await expect(page.locator('main > section').first()).toHaveAttribute('id','read');
 await page.waitForTimeout(850);
 const stage=await page.locator('#pageStage').boundingBox();
 const leaf=await page.locator('.book-leaf').first().boundingBox();
 expect(leaf.height).toBeGreaterThan(300);
 expect(leaf.y+leaf.height).toBeLessThanOrEqual(stage.y+stage.height+1);
 await page.mouse.move(leaf.x+leaf.width-6,leaf.y+leaf.height-12);
 await page.mouse.down();
 await page.mouse.move(leaf.x-leaf.width*.5,leaf.y+leaf.height*.5,{steps:20});
 await page.mouse.up();
 await expect(page.locator('#pageLabel')).toHaveText('3–4ページ');
});
test('15ページ単独表示・省略案内・裏表紙',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.route('**/assets/sample/manifest.json',route=>route.fulfill({json:[
  {type:'cover',label:'表紙',image:'/assets/cover.svg'},
  ...[2,4,6].map(n=>({type:'spread',label:`${n}–${n+1}ページ`,image:'/assets/spread.svg'})),
  {type:'gap',label:'続きは冊子で'},
  {type:'page',label:'15ページ',image:'/assets/back.svg'},
  {type:'cover',label:'裏表紙',image:'/assets/back.svg'}
 ]}));
 await page.goto('/');
 await expect(page.locator('#pageCount')).toHaveText('01 / 07');
 let sawGap=false;
 for(let i=0;i<12;i++){
  const label=await page.locator('#pageLabel').textContent();
  if(label==='続きは冊子で')sawGap=true;
  if(label==='15ページ')break;
  await page.locator('#next').click();
  await page.waitForTimeout(100);
 }
 expect(sawGap).toBeTruthy();
 await expect(page.locator('#pageLabel')).toHaveText('15ページ');
 await page.locator('#zoom').click();
 await expect(page.locator('#zoomContent .paper.page img')).toHaveAttribute('alt','15ページ');
 await expect(page.locator('#zoomContent .watermark')).toHaveText('SAMPLE');
 await page.locator('#closeZoom').click();
 for(let i=0;i<3&&await page.locator('#pageLabel').textContent()!=='裏表紙';i++){
  await page.locator('#next').click();await page.waitForTimeout(100);
 }
 await expect(page.locator('#pageLabel')).toHaveText('裏表紙');
 await expect(page.locator('#next')).toBeDisabled();
});
test('PDF15–16を同じ見開きにし、PDF1の裏表紙は単独',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 const pages=[
  {type:'cover',label:'表紙',image:'/assets/cover.svg'},
  {type:'spread',label:'3–4ページ',image:'/assets/spread.svg'},
  {type:'spread',label:'5–6ページ',image:'/assets/spread.svg'},
  {type:'page',label:'7ページ',image:'/assets/back.svg'},
  {type:'gap',label:'続きは冊子で'},
  {type:'spread',label:'15–16ページ',image:'/assets/spread.svg'},
  {type:'cover',label:'裏表紙',image:'/assets/back.svg'}
 ];
 await page.route('**/assets/sample/manifest.json',route=>route.fulfill({json:pages}));
 await page.goto('/');await expect(page.locator('#pageCount')).toHaveText('01 / 07');
 for(let i=0;i<12&&await page.locator('#pageLabel').textContent()!=='15–16ページ';i++){
  await page.locator('#next').click();await page.waitForTimeout(100);
 }
 await expect(page.locator('#pageLabel')).toHaveText('15–16ページ');
 const left=page.locator('.book-leaf.leaf-left').filter({has:page.locator('img[alt="15–16ページ"]')});
 const right=page.locator('.book-leaf.leaf-right').filter({has:page.locator('img[alt="15–16ページ"]')});
 if(test.info().project.name==='desktop'){
  await expect(left).toBeVisible();await expect(right).toBeVisible();
  const a=await left.boundingBox(),b=await right.boundingBox();
  expect(Math.abs(a.y-b.y)).toBeLessThan(1);expect(Math.abs(a.x+a.width-b.x)).toBeLessThan(1);
 }
 await page.locator('#zoom').click();await expect(page.locator('#zoomContent .paper.spread')).toBeVisible();
 await page.locator('#closeZoom').click();
 for(let i=0;i<3&&await page.locator('#pageLabel').textContent()!=='裏表紙';i++){
  await page.locator('#next').click();await page.waitForTimeout(100);
 }
 await expect(page.locator('#pageLabel')).toHaveText('裏表紙');
 await expect(page.locator('#next')).toBeDisabled();
 await expect(page.locator('.book-leaf').last().locator('.paper.cover')).toBeVisible();
});
