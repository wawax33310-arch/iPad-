/**
 * Rendu image par image de scene.html vers une vidéo H.264 (1080x1920, 60 fps).
 *
 *   node src/render.js [--fps 60] [--out out/zenvy-video.mp4] [--audio out/zenvy-audio.wav]
 *
 * Chaque image est produite en appelant window.renderFrame(t) dans Chromium,
 * puis envoyée directement dans ffmpeg via un pipe (pas de fichiers temporaires).
 */

const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FFMPEG = process.env.FFMPEG_BIN ||
  '/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2';

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

const FPS      = parseInt(arg('fps', '60'), 10);
const WIDTH    = 1080;
const HEIGHT   = 1920;
const OUT      = path.resolve(arg('out', 'out/zenvy-kinetic-20s.mp4'));
const AUDIO    = path.resolve(arg('audio', 'out/zenvy-audio.wav'));
const SCENE    = 'file://' + path.resolve(__dirname, 'scene.html');

(async () => {
  const hasAudio = fs.existsSync(AUDIO);
  if (!hasAudio) console.warn('! Piste audio absente (' + AUDIO + ') — vidéo muette.');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });

  const browser = await chromium.launch({
    args: ['--hide-scrollbars', '--force-device-scale-factor=1', '--disable-lcd-text']
  });
  const page = await browser.newPage({
    viewport: { width: WIDTH, height: HEIGHT },
    deviceScaleFactor: 1
  });

  await page.goto(SCENE, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });

  const duration = await page.evaluate(() => window.SCENE_DURATION);
  const total = Math.round(duration * FPS);

  const args = [
    '-y',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', 'pipe:0'
  ];
  if (hasAudio) args.push('-i', AUDIO);
  args.push(
    '-map', '0:v:0',
    ...(hasAudio ? ['-map', '1:a:0'] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
    '-profile:v', 'high', '-level', '4.2',
    '-pix_fmt', 'yuv420p',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
    '-r', String(FPS),
    '-g', String(FPS * 2),
    ...(hasAudio ? ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2'] : []),
    '-shortest',
    '-movflags', '+faststart',
    OUT
  );

  const ff = spawn(FFMPEG, args, { stdio: ['pipe', 'inherit', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', d => { ffErr += d.toString(); });
  const done = new Promise((resolve, reject) => {
    ff.on('close', code => code === 0 ? resolve() : reject(new Error(ffErr.slice(-4000))));
  });

  const write = buf => new Promise((resolve, reject) => {
    if (ff.stdin.write(buf)) resolve();
    else ff.stdin.once('drain', resolve);
    ff.stdin.once('error', reject);
  });

  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    const t = i / FPS;
    await page.evaluate(tt => window.renderFrame(tt), t);
    const buf = await page.screenshot({ type: 'png', animations: 'disabled' });
    await write(buf);
    if (i % 60 === 0 || i === total - 1) {
      const pct = ((i + 1) / total * 100).toFixed(1);
      const el = ((Date.now() - t0) / 1000).toFixed(0);
      process.stdout.write(`\r  image ${i + 1}/${total} (${pct}%) — ${el}s écoulées   `);
    }
  }
  process.stdout.write('\n');

  ff.stdin.end();
  await done;
  await browser.close();

  const size = (fs.statSync(OUT).size / 1e6).toFixed(2);
  console.log(`✔ ${OUT} — ${total} images @ ${FPS} fps, ${size} Mo`);
})().catch(err => { console.error(err); process.exit(1); });
