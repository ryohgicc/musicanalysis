import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),browser=await chromium.launch();
try{
 for(const viewport of [{width:1440,height:960},{width:390,height:844}]){
  const p=await browser.newPage({viewport,acceptDownloads:true}),errors=[],requests=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
  await p.goto(pathToFileURL(path.join(root,'.test-output/complete.html')).href+'#era-2');
  await p.waitForFunction(()=>scrollStudy.current===3);await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const baseline=await p.evaluate(()=>({y:scrollY,index:scrollStudy.current,reading:scrollStudy.reading,hash:location.hash}));
  await p.locator('#export-image').click();await p.locator('#start-export').click();
  assert.ok(await p.locator('#export-image').isDisabled());
  await p.waitForFunction(()=>!document.querySelector('#start-export').disabled,null,{timeout:90000});
  assert.match(await p.locator('#export-status').innerText(),/已生成/);assert.ok(await p.locator('#export-result').isVisible());
  const parts=await p.locator('#export-parts .export-part a[download]').evaluateAll(links=>links.map(a=>a.href));assert.ok(parts.length>1,'Full report must split at chapter boundaries instead of shrinking');
  const dimensions=[];
  for(const [i,url] of parts.entries()){
   const pixels=await p.evaluate(async url=>{const image=new Image();image.src=url;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);const data=ctx.getImageData(0,0,Math.min(100,canvas.width),Math.min(100,canvas.height)).data;return {width:canvas.width,height:canvas.height,top:[...ctx.getImageData(0,0,1,1).data],bottom:[...ctx.getImageData(0,canvas.height-2,1,1).data]};},url);
   assert.equal(pixels.width,2160);assert.ok(pixels.height<=15000&&pixels.height>1000);dimensions.push(pixels);
   if(i===0)assert.deepEqual(pixels.top.slice(0,3),[247,245,239]);
   if(i===parts.length-1)assert.deepEqual(pixels.bottom.slice(0,3),[51,87,255],'Final scene must be included');
  }
  assert.ok(dimensions.reduce((sum,p)=>sum+p.height,0)>30000,'2x export must retain all scene pixels');
  const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#download-image').click()]);const file=path.join(root,`.test-output/export-${viewport.width}.png`);await download.saveAs(file);const bytes=await fs.readFile(file);assert.equal(bytes.subarray(1,4).toString(),'PNG');assert.ok(bytes.length>100000);
  const fullURL=await p.locator('#open-image').getAttribute('href');assert.ok(fullURL.startsWith('blob:'));
  await p.locator('#close-export').click();assert.deepEqual(await p.evaluate(()=>({y:scrollY,index:scrollStudy.current,reading:scrollStudy.reading,hash:location.hash})),baseline,'Export must preserve page state');assert.equal(await p.locator('iframe').count(),0);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  // Failure leaves the report usable, with a retryable message and no stale result.
  await p.evaluate(()=>{window.originalCapture=html2canvas;window.html2canvas=async()=>{throw Error('Synthetic capture failure');}});
  await p.locator('#export-image').click();await p.locator('#start-export').click();await p.waitForFunction(()=>!document.querySelector('#start-export').disabled);assert.match(await p.locator('#export-status').innerText(),/Synthetic capture failure/);assert.ok(await p.locator('#export-result').isHidden());assert.equal(await p.locator('iframe').count(),0);
  await p.evaluate(()=>window.html2canvas=window.originalCapture);
  if(viewport.width===1440){
   await p.locator('#export-quality').selectOption('3');await p.locator('#start-export').click();await p.waitForFunction(()=>!document.querySelector('#start-export').disabled,null,{timeout:120000});
   assert.match(await p.locator('#export-status').innerText(),/已生成/);assert.equal(await p.locator('#export-preview img').evaluate(async img=>{await img.decode();return img.naturalWidth;}),3240);
   assert.ok(await p.locator('#export-parts .export-part').count()>parts.length);
   await p.locator('#export-quality').selectOption('fit');await p.locator('#start-export').click();await p.waitForFunction(()=>!document.querySelector('#start-export').disabled,null,{timeout:90000});
   assert.equal(await p.locator('#export-parts .export-part').count(),0);assert.match(await p.locator('#export-size').textContent(),/1 张整图/);
  }
  await p.locator('#close-export').click();
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);await p.close();
 }
 console.log('Screenshot export passed: desktop/mobile PNG pixels, all scenes including final, download/preview, offline engine/covers, preserved scroll/mode, cleanup and retryable failure.');
}finally{await browser.close();}
