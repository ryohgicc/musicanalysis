import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';

const html=await readFile(new URL('../docs/apple-motion-report/index.html',import.meta.url));
let server;
let address=process.env.MOTION_DEMO_URL;
if(!address){
  server=createServer((req,res)=>{res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(html);});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  address=`http://127.0.0.1:${server.address().port}/`;
}
const browser=await chromium.launch({headless:true});
try{
  const page=await browser.newPage({viewport:{width:1440,height:960}});
  const errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==new URL(address).origin)external.push(r.url());});
  const response=await page.goto(address+'#preference-groove');
  assert.equal(response.status(),200);
  assert.deepEqual(await response.body(),html);
  await page.waitForFunction(()=>scrollStudy.current===14);
  const data=await page.locator('#report-data').textContent().then(JSON.parse);
  assert.equal(data.playlist.tracks.length,799);
  assert.equal(await page.locator('.panel').count(),24);
  assert.equal(await page.locator('.era').count(),9);
  assert.equal(await page.locator('.insight').count(),6);
  assert.equal(await page.locator('.rec-card').count(),12);
  assert.equal(await page.locator('.dock,#progress,#dots').count(),0);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  assert.ok(await page.locator('#preference-groove .proof-thumb img').count()===3);
  assert.equal(await page.locator('.rec-art img').count(),12);
  assert.equal(await page.locator('.stage-track .stage-thumb img').count(),27);
  assert.equal(data.artworkNotes['474'].kind,'artist');
  assert.equal(await page.locator('[data-track="474"] .art-note').textContent(),'艺人图');
  assert.match(await page.locator('[data-track="474"] img').getAttribute('alt'),/原条目无专辑封面/);
  assert.equal(data.recommendationArtwork['9'].title,'My Jinji (Audiotree Live)');
  for(const [i,r] of data.recommendations.entries())assert.equal(await page.locator(`#recommendation-${i} .rec-art img`).getAttribute('alt'),`${r.artist}《${r.title}》封面`);
  assert.ok(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.src.startsWith('data:image/'))));
  for(const [i,stage] of data.stages.entries()){
    const body=await page.locator(`#era-${i+1}`).textContent();
    assert.ok(body.includes(stage.body));
    for(const id of stage.ids){
      assert.ok(body.includes('#'+id));
      const row=page.locator(`#era-${i+1} [data-track="${id}"]`);
      assert.equal(await row.locator('img').getAttribute('src'),data.covers[id]);
      assert.equal(await row.locator('h3 a').getAttribute('href'),data.playlist.tracks.find(t=>t.index===id).sourceUrl);
    }
    assert.equal(await page.locator(`#era-${i+1} [data-detail^="stage:"]`).count(),0);
  }
  async function go(i){
    await page.evaluate(i=>scrollTo(0,scrollStudy.starts[i]+scrollStudy.step*.2),i);
    await page.waitForFunction(i=>scrollStudy.current===i,i);
  }
  for(const viewport of [{width:1440,height:960},{width:1280,height:720},{width:1024,height:768},{width:390,height:844},{width:375,height:667},{width:320,height:740}]){
    await page.setViewportSize(viewport);await page.waitForTimeout(100);
    for(let i=0;i<24;i++){
      await go(i);
      const travel=await page.evaluate(i=>scrollStudy.overflows[i],i);
      if(travel){await page.evaluate(i=>scrollTo(0,scrollStudy.starts[i]+scrollStudy.overflows[i]+scrollStudy.step*.3),i);await page.waitForTimeout(30);}
      const box=await page.locator('.panel-inner').nth(i).boundingBox();
      assert.ok(box.y+box.height<=viewport.height+2,`Unreadable scene ${i} at ${viewport.width}px`);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      if(i>=2&&i<=10){
        const thumbnails=await page.locator('.panel').nth(i).locator('.stage-track').evaluateAll(rows=>rows.every(row=>{
          const image=row.querySelector('img'),art=image.getBoundingClientRect(),text=row.querySelector('h3').getBoundingClientRect(),bounds=row.getBoundingClientRect();
          return image.complete&&image.naturalWidth>0&&art.width>=40&&Math.abs(art.width-art.height)<1&&text.left>=art.right&&art.left>=bounds.left&&art.right<=bounds.right;
        }));
        assert.ok(thumbnails,`Stage ${i} thumbnails must fit beside the song text at ${viewport.width}px`);
        const recordFits=await page.locator('.panel').nth(i).evaluate(el=>{
          const image=el.querySelector('.record-cover img'),cover=el.querySelector('.record-cover').getBoundingClientRect(),evidence=el.querySelector('.stage-evidence').getBoundingClientRect(),style=getComputedStyle(image);
          return Math.abs(parseFloat(style.width)-parseFloat(style.height))<1&&cover.bottom<=evidence.top;
        });
        assert.ok(recordFits,`Stage ${i} record must stay square and clear of the evidence at ${viewport.width}px`);
      }
    }
  }
  for(const viewport of [{width:1920,height:1080},{width:1440,height:960},{width:1280,height:720}]){
    await page.setViewportSize(viewport);await page.waitForTimeout(100);
    for(let i=2;i<=10;i++){
      await page.evaluate(i=>scrollTo(0,scrollStudy.starts[i]),i);
      await page.waitForFunction(i=>scrollStudy.current===i,i);
      const layout=await page.locator('.panel').nth(i).evaluate(el=>{
        const rect=selector=>el.querySelector(selector).getBoundingClientRect();
        const css=getComputedStyle(el),available=innerHeight-parseFloat(css.paddingTop)-parseFloat(css.paddingBottom);
        return {available,content:rect('.panel-inner').height,copy:rect('.era-copy').height,art:rect('.stage-art').height,evidenceBottom:rect('.stage-evidence').bottom};
      });
      assert.ok(layout.content>=layout.available*.95,`Stage ${i} must use the desktop height`);
      assert.ok(layout.copy>=layout.available*.95&&layout.art>=layout.available*.95);
      assert.ok(layout.evidenceBottom>=viewport.height*.85,`Stage ${i} evidence must extend down the page`);
    }
  }
  await page.setViewportSize({width:1440,height:960});await page.waitForTimeout(100);
  await go(14);await page.locator('#preference-groove [data-detail]').click();
  assert.equal(await page.locator('dialog .proof-thumb img').count(),3);
  await page.keyboard.press('Escape');
  await go(20);await page.locator('#recommendation-9 [data-detail]').click();
  assert.equal(await page.locator('dialog .rec-detail-art img').count(),1);
  assert.ok((await page.locator('dialog .rec-detail-art').innerText()).includes('Audiotree Live'));
  assert.equal(await page.locator('dialog .art-source a').getAttribute('href'),data.recommendationArtwork['9'].source);
  await page.keyboard.press('Escape');
  await go(19);const like=page.locator('#discover [data-feedback="like"]').first();await like.click();
  assert.equal(await like.getAttribute('aria-pressed'),'true');
  await page.reload();await go(19);assert.equal(await like.getAttribute('aria-pressed'),'true');
  await go(22);await page.locator('#library-search').fill('no-matching-motion-track');assert.match(await page.locator('#library-rows').innerText(),/没有找到/);
  await page.locator('#mode').click();assert.equal(await page.locator('[inert]').count(),0);
  await page.locator('#mode').click();await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>scrollStudy.reading);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('Motion demo passed: published HTML, embedded covers, inline stories, 24 scenes across six sizes, no bottom dock, detail covers, feedback, search and reduced motion.');
}finally{
  await browser.close();
  if(server)await new Promise(resolve=>server.close(resolve));
}
