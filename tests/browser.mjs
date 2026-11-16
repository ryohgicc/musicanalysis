import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const url=file=>pathToFileURL(path.join(root,'.test-output',file)).href;
const browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1440,height:960},acceptDownloads:true});
const page=await context.newPage(),errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
const settle=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
async function load(file,hash=''){await page.goto(url(file)+hash);await page.waitForFunction(()=>window.scrollStudy?.current>=0);await settle();}
async function go(id,offset=0){await page.evaluate(({id,offset})=>{const i=scrollStudy.panels.findIndex(p=>p.id===id);if(i<0)throw Error('Missing scene '+id);scrollTo(0,scrollStudy.starts[i]+offset);},{id,offset});await settle();}
const contract=()=>({style:document.querySelector('style').textContent,script:document.querySelector('script:last-of-type').textContent,nav:[...document.querySelectorAll('.topnav a')].map(a=>a.getAttribute('href')),identity:(()=>{const d=JSON.parse(document.querySelector('#report-data').textContent);return [d.templateId,d.templateVersion,d.templateHash];})()});
try{
 await load('report.html');const template=await page.evaluate(contract);
 assert.match(await page.locator('#source-line').innerText(),/预览.*未完成/);
 const design=JSON.parse(await fs.readFile(path.join(root,'tests/design-baseline.json'),'utf8'));
 for(const {viewport,styles} of design.viewports){
  await page.setViewportSize(viewport);await settle();
  const actual=await page.evaluate(styles=>Object.fromEntries(Object.entries(styles).map(([sel,props])=>[sel,Object.fromEntries(Object.keys(props).map(prop=>[prop,getComputedStyle(document.querySelector(sel))[prop]]))])),styles);
  assert.deepEqual(actual,styles,`Fullscreen design changed at ${viewport.width}px`);
 }
 await page.setViewportSize({width:1440,height:960});await settle();
 assert.equal(await page.locator('.era').count(),3);assert.equal(await page.locator('.stage-thumb img').count(),6);
 assert.equal(await page.locator('.insight .proof-thumb img').count(),2);assert.equal(await page.locator('.rec-art img').count(),1);
 assert.match(await page.locator('#era-1 .art-note').first().textContent(),/艺人图.*原条目无专辑封面/);
 assert.equal(await page.locator('#era-1 .art-note a').first().getAttribute('href'),'https://y.qq.com/n/ryqq/singerDetail/synthetic');
 assert.match(await page.locator('[data-track="13"] img').getAttribute('alt'),/艺人图片/);
 assert.equal(await page.locator('.dot-map rect').count(),18);
 assert.match(await page.locator('.dot-map').getAttribute('aria-label'),/第 18 首较早/);
 assert.equal(await page.locator('.viewport').evaluate(e=>getComputedStyle(e).position),'sticky');
 assert.equal(await page.locator('.dock,#progress,#dots').count(),0);
 // The first 60 pixels must change the incoming scene; no scroll dead zone.
 await go('era-1');assert.equal(await page.evaluate(()=>scrollStudy.overflows[2]),0);
 const incomingY=()=>page.locator('#era-2').evaluate(e=>new DOMMatrixReadOnly(getComputedStyle(e).transform).m42);
 const y0=await incomingY();await go('era-1',60);const y60=await incomingY();await go('era-1',120);const y120=await incomingY();
 assert.ok(y60<y0-40&&y120<y60-40,`Early scrolling must advance the scene: ${y0}, ${y60}, ${y120}`);
 assert.equal(await page.locator('.panel:not([inert])').count(),1);
 await go('era-1');await page.mouse.move(700,500);const wheelStart=await page.evaluate(()=>scrollY);await page.mouse.wheel(0,80);await page.waitForTimeout(100);assert.ok(await page.evaluate(y=>scrollY>y,wheelStart));
 await page.keyboard.press('Home');await page.waitForFunction(()=>scrollStudy.current===0);await page.waitForTimeout(400);
 await page.keyboard.press('PageDown');await page.waitForFunction(()=>scrollStudy.current===1);await page.waitForTimeout(400);
 await go('journey');await page.locator('.phase-links a').last().click();await page.waitForFunction(()=>scrollStudy.current===4);await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>location.hash),'#era-3');
 await go('preferences');await page.locator('.thread-card').first().click();await page.waitForFunction(()=>document.querySelector('.panel:not([inert])')?.id==='preference-insight-1');await page.waitForTimeout(400);
 await page.locator('#preference-insight-1 [data-detail]').click();assert.match(await page.locator('#detail-body').innerText(),/Compare melody/);
 assert.equal(await page.locator('#detail-body .proof-thumb img').count(),2);
 await page.locator('#detail-body [data-detail="rec:0"]').click();assert.match(await page.locator('#detail-body').textContent(),/Synthetic fixture/);
 assert.equal(await page.locator('#detail-body .art-source a').getAttribute('href'),'https://music.apple.com/album/fixture');await page.keyboard.press('Escape');
 await go('statistics');const before=await page.locator('.bar-num').allTextContents();await page.locator('[data-count="family"]').click();assert.notDeepEqual(await page.locator('.bar-num').allTextContents(),before);
 await page.locator('[data-detail="stats"]').click();assert.match(await page.locator('#detail-body').innerText(),/条 → 暂合并/);assert.ok(!(await page.locator('#detail-body').textContent()).includes('78 条'));await page.keyboard.press('Escape');
 await go('discover-explore');const like=page.getByRole('button',{name:'喜欢：Test Recommendation',exact:true});await like.click();await page.reload();await settle();await go('discover-explore');assert.equal(await like.getAttribute('aria-pressed'),'true');
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#discover-explore .export-feedback').click()]);const saved=path.join(root,'.test-output/feedback.json');await download.saveAs(saved);const feedback=JSON.parse(await fs.readFile(saved));assert.equal(feedback.recommendations[0].feedback,'喜欢');assert.ok(feedback.playlistHash);
 await go('library');assert.equal(await page.locator('#library-rows tr').count(),6);assert.equal(await page.locator('#library-rows td').first().innerText(),'18');await page.locator('#page-next').click();assert.equal(await page.locator('#library-rows td').first().innerText(),'12');
 await page.locator('#library-search').fill('Synthetic 18');assert.equal(await page.locator('#library-rows tr').count(),1);await page.locator('#library-search').fill('no-such-track');assert.match(await page.locator('#library-rows').innerText(),/没有找到/);await page.locator('#library-search').fill('');await page.locator('#library-order').selectOption('new');assert.equal(await page.locator('#library-rows td').first().innerText(),'1');
 for(const file of ['different.html','unknown.html','complete.html','external.html','first.html','hostile.html']){
  await load(file);assert.deepEqual(await page.evaluate(contract),template,'Only playlist content may change the template');
  assert.equal(await page.evaluate(()=>window.pwned),undefined);assert.equal(await page.locator('a[href^="javascript:"],a[href="#"]').count(),0);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));assert.ok(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.src.startsWith('data:image/'))));
  if(file==='different.html')assert.match(await page.locator('#report-title').innerText(),/另一份/);
  if(file==='unknown.html'){assert.equal(await page.locator('.era').count(),0);assert.match(await page.locator('#journey').textContent(),/尚未确认/);await go('library');assert.deepEqual(await page.locator('#library-order option').allTextContents(),['歌单原序','原序倒排']);}
  if(file==='first.html'){assert.match(await page.locator('#era-1 .range').textContent(),/#1 → #6/);await go('library');assert.equal(await page.locator('#library-rows td').first().innerText(),'1');}
  if(file==='external.html'){assert.equal(await page.locator('a[href*="qq.com"]').count(),0);await go('library');assert.equal(await page.locator('#library-rows a[href^="https://music.163.com/"]').count(),6);}
 }
 await load('complete.html');const d=JSON.parse(await page.locator('#report-data').textContent());
 assert.equal(d.templateVersion,'0.6.0');assert.equal(await page.locator('.panel').count(),24);
 assert.equal(await page.locator('.era').count(),9);assert.equal(await page.locator('.thread-card').count(),6);assert.equal(await page.locator('.insight').count(),6);
 assert.equal(await page.locator('.stage-thumb img').count(),27);assert.equal(await page.locator('.insight .proof-thumb img').count(),18);assert.equal(await page.locator('.rec-art img').count(),12);
 assert.equal(await page.locator('#discover .rec-card').count(),6);assert.equal(await page.locator('#discover-adjacent .rec-card').count(),4);assert.equal(await page.locator('#discover-explore .rec-card').count(),2);
 assert.match(await page.locator('#journey').textContent(),/不代表收藏时间/);assert.match(await page.locator('#era-1').textContent(),/不代表收藏时间/);assert.ok(!(await page.locator('#source-line').textContent()).includes('预览'));
 for(let i=0;i<9;i++){const text=await page.locator(`#era-${i+1}`).textContent();assert.ok(text.includes(d.report.stages[i].body)&&text.includes(d.report.stages[i].insight));}
 for(const v of [{width:1920,height:1080},{width:1440,height:960},{width:1280,height:720},{width:1024,height:768},{width:390,height:844},{width:320,height:740}]){
  await page.setViewportSize(v);await page.waitForTimeout(80);
  const scenes=await page.evaluate(()=>scrollStudy.panels);
  for(let i=0;i<scenes.length;i++){
   const travel=await page.evaluate(i=>scrollStudy.overflows[i],i);await go(scenes[i].id,travel);
   const box=await page.locator('.panel-inner').nth(i).boundingBox();assert.ok(box.y+box.height<=v.height+3,`Scene ${i} bottom clipped at ${v.width}: ${JSON.stringify(box)}`);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Horizontal overflow ${i} at ${v.width}`);
   if(i===2&&travel>0){await go(scenes[i].id);const top=await page.locator('#era-1 .panel-inner').boundingBox();await go(scenes[i].id,60);const moved=await page.locator('#era-1 .panel-inner').boundingBox();assert.ok(moved.y<top.y-40,'Overflowing content must move with the very first scroll');}
  }
 }
 await page.setViewportSize({width:1440,height:960});await page.waitForTimeout(80);await go('era-1');await page.screenshot({path:path.join(root,'.test-output/fullscreen-desktop.png')});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(80);await go('era-1');await page.screenshot({path:path.join(root,'.test-output/fullscreen-mobile.png')});
 await page.locator('#menu-trigger').click();assert.equal(await page.locator('#menu-trigger').getAttribute('aria-expanded'),'true');
 await page.locator('#menu a[href="#era-2"]').click();await page.waitForFunction(()=>scrollStudy.current===3);await page.waitForTimeout(400);assert.ok(await page.locator('#menu').isHidden());
 await page.locator('#mode').click();assert.ok(await page.evaluate(()=>scrollStudy.reading));assert.equal(await page.locator('[inert]').count(),0);assert.equal(await page.locator('.panel[aria-hidden=true]').count(),0);
 await page.locator('#mode').click();assert.equal(await page.locator('.panel:not([inert])').count(),1);
 // A long final scene has no following scene to supply scroll range.
 await load('last-long.html');await page.setViewportSize({width:320,height:740});await page.waitForTimeout(80);
 const last=await page.evaluate(()=>scrollStudy.panels.length-1),overflow=await page.evaluate(i=>scrollStudy.overflows[i],last);assert.ok(overflow>100);
 await page.evaluate(i=>scrollTo(0,scrollStudy.starts[i]+scrollStudy.overflows[i]),last);await settle();
 const lastBox=await page.locator('#end .panel-inner').boundingBox();assert.ok(lastBox.y+lastBox.height<=743,'Last scene content must scroll fully into view');
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>scrollStudy.reading);
 await page.emulateMedia({media:'print'});assert.ok(await page.locator('.panel-inner').evaluateAll(els=>els.every(el=>getComputedStyle(el).transform==='none')));
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 console.log('Passed: official fullscreen template, first-scroll response, long content/last scene, six sizes, 24 scenes, 9/6/12 contract, three order modes, offline covers, platform links, hostile data, keyboard/navigation, statistics, details, persisted/exported feedback, library, reading/reduced-motion/print.');
}finally{await browser.close();}
