import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const url=file=>pathToFileURL(path.join(root,'.test-output',file)).href;
const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1440,height:900},acceptDownloads:true});
const page=await context.newPage();let errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
await page.emulateMedia({reducedMotion:'reduce'});await page.goto(url('report.html'));
assert.equal(await page.locator('.wordmark').count(),1);
assert.equal(await page.locator('.float-album img').count(),4);
assert.equal(await page.locator('.era-cover img').count(),3);
assert.equal(await page.locator('.insight-proof-song img').count(),0);
assert.equal(await page.locator('.insight-proof-number').count(),2);
assert.ok(await page.locator('img').evaluateAll(imgs=>imgs.length>0&&imgs.every(i=>i.complete&&i.naturalWidth>0&&i.src.startsWith('data:image/'))),'default CLI must produce decoded offline cover images');
// Preserve the original report's design across different playlist contents.
const design=JSON.parse(await fs.readFile(path.join(root,'tests/design-baseline.json'),'utf8'));
for (const {viewport,styles} of design.viewports) {
  await page.setViewportSize(viewport);
  const actual=await page.evaluate(styles=>Object.fromEntries(Object.entries(styles).map(([selector,expected])=>{
    const computed=getComputedStyle(document.querySelector(selector));
    return [selector,Object.fromEntries(Object.keys(expected).map(property=>[property,computed[property]]))];
  })),styles);
  assert.deepEqual(actual,styles,`Original design differs at ${viewport.width}px`);
}
await page.setViewportSize({width:1440,height:900});
const templateContract=()=>({
  styles:document.querySelector('style').textContent,
  script:document.querySelector('script:last-of-type').textContent,
  sections:[...document.querySelectorAll('.report-main>section')].map(e=>({id:e.id,classes:e.className})),
  navigation:[...document.querySelectorAll('.header-nav a')].map(e=>e.getAttribute('href')),
  identity:(()=>{const d=JSON.parse(document.querySelector('#report-data').textContent);return [d.templateId,d.templateVersion,d.templateHash];})()
});
const originalTemplate=await page.evaluate(templateContract);
assert.equal(await page.locator('#track-map rect').count(),18);assert.equal(await page.locator('.era').count(),3);
for(const i of [1,2,3,1]){await page.locator(`#era-${i}`).evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));await page.waitForFunction(n=>document.querySelector('.era-link[aria-current="step"]').dataset.era===String(n-1),i);assert.ok(Math.abs((await page.locator('.journey-nav').boundingBox()).y)<2);}
await page.locator('.era-link').last().click();assert.equal(await page.evaluate(()=>location.hash),'#era-3');
await page.locator('.era-link').last().press('ArrowLeft');assert.equal(await page.evaluate(()=>location.hash),'#era-2');
await page.locator('.taste-preview').first().click();assert.equal(await page.evaluate(()=>location.hash),'#insight-1');
const before=await page.locator('.bar-value').allTextContents();await page.locator('[data-count-mode="family"]').click();const after=await page.locator('.bar-value').allTextContents();assert.notDeepEqual(before,after);
await page.locator('[data-tier="相邻风格"]').click();assert.equal(await page.locator('.rec-card').count(),0);
await page.locator('.insight-rec-link').first().click();assert.equal(await page.evaluate(()=>location.hash),'#recommendation-0');assert.equal(await page.locator('.rec-card').count(),1);assert.equal(await page.locator('[data-tier="全部"]').getAttribute('aria-pressed'),'true');
await page.getByRole('button',{name:'喜欢：Test Recommendation',exact:true}).click();await page.reload();assert.equal(await page.getByRole('button',{name:'喜欢：Test Recommendation',exact:true}).getAttribute('aria-pressed'),'true');
const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-feedback').click()]);const downloadPath=path.join(root,'.test-output/feedback.json');await download.saveAs(downloadPath);assert.equal(JSON.parse(await fs.readFile(downloadPath,'utf8')).recommendations[0].feedback,'喜欢');
assert.equal(await page.locator('#library-rows tr').count(),12);await page.locator('#page-next').click();assert.equal(await page.locator('#library-rows tr').count(),6);
await page.locator('#library-search').fill('Synthetic 18');assert.equal(await page.locator('#library-rows tr').count(),1);await page.locator('#library-search').fill('no-matching-test');assert.match(await page.locator('#library-rows').innerText(),/没有匹配/);await page.locator('#library-search').fill('');await page.locator('#library-order').selectOption('reverse');assert.equal(await page.locator('#library-rows td').first().innerText(),'18');
for(const v of [{width:1024,height:768},{width:390,height:844},{width:320,height:740}]){await page.setViewportSize(v);await page.locator('#era-3').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));await page.waitForFunction(()=>document.querySelector('.era-link[aria-current="step"]').dataset.era==='2');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));const rect=await page.locator('.era-link').last().boundingBox();assert.ok(rect.x>=0&&rect.x+rect.width<=v.width);}
await page.setViewportSize({width:1440,height:900});await page.goto(url('different.html'));
assert.equal(await page.locator('.era').count(),2);
assert.match(await page.locator('#report-title').innerText(),/另一份/);
assert.deepEqual(await page.evaluate(templateContract),originalTemplate,'New playlist must use the identical design and section structure');
assert.ok(await page.locator('.insight-direction').isVisible());assert.ok(await page.locator('.insight-listen-question').isVisible());
await page.goto(url('unknown.html'));assert.equal(await page.locator('#journey').isVisible(),true);assert.equal(await page.locator('.era').count(),0);
assert.equal(await page.locator('#journey-nav-link').isVisible(),true);assert.equal(await page.locator('#hero-start').getAttribute('href'),'#journey');
assert.match(await page.locator('#track-map-wrap').innerText(),/尚未确认/);
assert.deepEqual(await page.evaluate(templateContract),originalTemplate);
await page.goto(url('first.html'));assert.match(await page.locator('#era-1 .era-meta').innerText(),/1—6/);
await page.goto(url('hostile.html'));assert.equal(await page.evaluate(()=>window.pwned),undefined);assert.match(await page.locator('#report-title').innerText(),/onerror/);assert.equal(await page.locator('a[href^="javascript:"]').count(),0);
assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);console.log('Browser passed: 3 chronology modes, sticky scrolling, jumps, chart, recommendations, persisted/exported feedback, library search/sort/pagination, 4 viewports, hostile strings, default CLI artwork embedding, original design at 4 viewports, preference recommendation links and offline loading.');await browser.close();
