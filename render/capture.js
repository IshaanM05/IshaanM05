// Captures deterministic frames of scene.html (a Three.js scene) via headless
// Chrome, for later assembly into a looping animated WebP with assemble.py.
// Self-hosts the scene over a local HTTP server (ES module imports are
// blocked under file:// by CORS), so this only needs `node capture.js`.
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { networkInterfaces } = require('os');

const NUM_FRAMES = 60;
const PORT = 8199;
const OUT_DIR = path.join(__dirname, 'frames');

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json' };

function startServer() {
  const server = http.createServer((req, res) => {
    const filePath = path.join(__dirname, decodeURIComponent(req.url.split('?')[0]));
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('not found'); return; }
      const ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });
  return new Promise((resolve) => server.listen(PORT, () => resolve(server)));
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const server = await startServer();

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  page.on('pageerror', (err) => console.error('PAGE ERROR:', err.message));

  await page.setViewport({ width: 900, height: 360 });
  await page.goto(`http://localhost:${PORT}/scene.html`);
  await page.waitForFunction('window.__ready === true', { timeout: 15000 });

  for (let i = 0; i < NUM_FRAMES; i++) {
    const t = i / NUM_FRAMES;
    await page.evaluate((t) => window.renderFrame(t), t);
    const dataUrl = await page.evaluate(() => document.getElementById('c').toDataURL('image/png'));
    const base64 = dataUrl.replace(/^data:image\/png;base64,/, '');
    fs.writeFileSync(path.join(OUT_DIR, `frame_${String(i).padStart(3, '0')}.png`), base64, 'base64');
    process.stdout.write(`\rcaptured ${i + 1}/${NUM_FRAMES}`);
  }
  console.log('\ndone');

  await browser.close();
  server.close();
})().catch((e) => {
  console.error('FATAL:', e);
  process.exit(1);
});
