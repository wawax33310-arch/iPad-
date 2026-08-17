/**
 * Aperçu : exporte quelques images clés de scene.html en PNG (contrôle visuel).
 *   node src/preview.js 0.9 2.0 5.5 8.5 11.5 14.6 16.2 16.4 17.5 19.5
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const times = process.argv.slice(2).map(Number);
const outDir = path.resolve('out/preview');

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({
    args: ['--hide-scrollbars', '--force-device-scale-factor=1', '--disable-lcd-text']
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'), { waitUntil: 'load' });
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });

  for (const t of times) {
    await page.evaluate(tt => window.renderFrame(tt), t);
    const file = path.join(outDir, `t${t.toFixed(2)}.png`);
    await page.screenshot({ path: file, animations: 'disabled' });
    console.log('→', file);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
