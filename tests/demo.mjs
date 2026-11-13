import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';

const html=await readFile(new URL('../docs/index.html',import.meta.url));
let server;
let address=process.env.DEMO_URL;
if(!address){
  server=createServer((req,res)=>{
    if(req.url==='/' || req.url==='/index.html'){
      res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(html);
    }else{res.writeHead(404);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  address=`http://127.0.0.1:${server.address().port}/`;
}
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage();const errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()) && new URL(r.url()).origin!==new URL(address).origin)external.push(r.url());});
  await page.emulateMedia({reducedMotion:'reduce'});
  const response=await page.goto(address+'#era-2');
  assert.equal(response.status(),200);
  assert.deepEqual(await response.body(),html,'Published demo must match the selected HTML exactly');
  const data=await page.locator('#report-data').textContent().then(JSON.parse);
  assert.equal(data.playlist.tracks.length,799);
  assert.equal(await page.locator('.era').count(),9);
  assert.equal(await page.locator('.taste-preview').count(),6);
  assert.equal(await page.locator('.rec-card').count(),12);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  assert.ok(await page.locator('img').count()>=13);
  assert.ok(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.src.startsWith('data:image/'))));
  await page.waitForFunction(()=>document.querySelector('.era-link[aria-current="step"]').dataset.era==='1');
  await page.locator('.era-link').last().click();
  await page.waitForFunction(()=>location.hash==='#era-9');
  await page.locator('[data-tier="探索"]').click();
  assert.equal(await page.locator('.rec-card').count(),2);
  await page.locator('[data-tier="all"]').click();
  const like=page.locator('.rec-card [data-feedback="like"]').first();
  await like.click();
  assert.equal(await like.getAttribute('aria-pressed'),'true');
  await page.reload();
  assert.equal(await page.locator('.rec-card [data-feedback="like"]').first().getAttribute('aria-pressed'),'true');
  await page.locator('#library-search').fill(data.playlist.tracks[0].title);
  assert.ok(await page.locator('#library-rows tr').count()>0);
  await page.locator('#library-search').fill('no-such-track-demo-check');
  assert.match(await page.locator('#library-rows').innerText(),/没有/);
  for(const viewport of [{width:1440,height:900},{width:390,height:844},{width:320,height:740}]){
    await page.setViewportSize(viewport);
    await page.locator('#era-2').evaluate(el=>el.scrollIntoView({behavior:'instant'}));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow at ${viewport.width}px`);
  }
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('Demo passed: exact HTML, 799 tracks, 9 chapters, 6 insights, 12 recommendations, embedded images, #era-2, filters, local feedback, search and desktop/mobile layouts.');
}finally{
  await browser.close();
  if(server)await new Promise(resolve=>server.close(resolve));
}
