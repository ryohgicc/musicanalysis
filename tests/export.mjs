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
  const pixels=await p.locator('#export-preview img').evaluate(async image=>{await image.decode();const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;let dark=0;for(let i=0;i<data.length;i+=4)if(data[i]<100&&data[i+1]<100&&data[i+2]<100)dark++;return {width:canvas.width,height:canvas.height,dark,top:[...ctx.getImageData(0,0,1,1).data],bottom:[...ctx.getImageData(0,canvas.height-2,1,1).data]};});
  assert.ok(pixels.width>=700&&pixels.height>10000);assert.ok(pixels.dark>10000,'PNG must contain rendered text');assert.deepEqual(pixels.top.slice(0,3),[247,245,239]);assert.deepEqual(pixels.bottom.slice(0,3),[51,87,255],'Final scene must be included');
  const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#download-image').click()]);const file=path.join(root,`.test-output/export-${viewport.width}.png`);await download.saveAs(file);const bytes=await fs.readFile(file);assert.equal(bytes.subarray(1,4).toString(),'PNG');assert.ok(bytes.length>100000);
  const fullURL=await p.locator('#open-image').getAttribute('href');assert.ok(fullURL.startsWith('blob:'));
  await p.locator('#close-export').click();assert.deepEqual(await p.evaluate(()=>({y:scrollY,index:scrollStudy.current,reading:scrollStudy.reading,hash:location.hash})),baseline,'Export must preserve page state');assert.equal(await p.locator('iframe').count(),0);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  // Failure leaves the report usable, with a retryable message and no stale result.
  await p.evaluate(()=>{window.originalCapture=html2canvas;window.html2canvas=async()=>{throw Error('Synthetic capture failure');}});
  await p.locator('#export-image').click();await p.locator('#start-export').click();await p.waitForFunction(()=>!document.querySelector('#start-export').disabled);assert.match(await p.locator('#export-status').innerText(),/Synthetic capture failure/);assert.ok(await p.locator('#export-result').isHidden());assert.equal(await p.locator('iframe').count(),0);
  await p.evaluate(()=>window.html2canvas=window.originalCapture);await p.locator('#close-export').click();
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);await p.close();
 }
 console.log('Screenshot export passed: desktop/mobile PNG pixels, all scenes including final, download/preview, offline engine/covers, preserved scroll/mode, cleanup and retryable failure.');
}finally{await browser.close();}
