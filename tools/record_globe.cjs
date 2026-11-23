// Records one 48 s turn of the Hello World globe from the-thing.dev, a PNG per step, straight off its canvas.
// Playwright's clock is frozen and stepped, so every frame is exact and the loop closes.
//   PW=<path to playwright> OUT=<dir> N=96 node tools/record_globe.cjs   (then tools/hello_world.sh <dir>)
const { chromium } = require(process.env.PW);
const fs = require('fs');
(async () => {
  const b = await chromium.launch({ channel: 'chrome' });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, colorScheme: 'dark', timezoneId: 'Asia/Baghdad', locale: 'en-US' });
  const p = await ctx.newPage();
  await p.clock.install();
  await p.goto('https://the-thing.dev/#hello-world', { waitUntil: 'domcontentloaded' });
  await p.clock.runFor(3000);
  // past the power-on intro
  for (const k of ['Escape', 'Enter']) { await p.keyboard.press(k); await p.clock.runFor(1500); }
  const skip = p.getByRole('button', { name: /skip intro/i });
  if (await skip.count()) { await skip.first().click().catch(() => {}); await p.clock.runFor(1500); }
  await p.locator('.hw-run').scrollIntoViewIfNeeded();
  await p.locator('.hw-run').click();
  for (let t = 0; t < 20; t++) { await p.waitForTimeout(400); await p.clock.runFor(1000); }  // load, type, boot, spin up, settle
  const N = +process.env.N, STEP = 48000 / N;
  for (let i = 0; i < N; i++) {
    const url = await p.locator('canvas.hw-globe').evaluate(c => c.toDataURL('image/png'));
    fs.writeFileSync(`${process.env.OUT}/f${String(i).padStart(3, '0')}.png`, Buffer.from(url.split(',')[1], 'base64'));
    await p.clock.runFor(STEP);
  }
  const stage = await p.locator('.hw-stage').evaluate(e => getComputedStyle(e).backgroundColor);
  console.log('frames', N, 'stage bg', stage);
  await b.close();
})();
