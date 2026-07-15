import { chromium } from "playwright-core";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import { createServer } from "node:http";
import { createReadStream, existsSync } from "node:fs";
import { mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";

const rootDir = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const reportRoot = path.resolve(process.env.RENDER_REPORT_DIR || path.join(rootDir, "public", "reports", "diff-report"));
const baselineDir = path.resolve(process.env.RENDER_REPORT_BASELINE_DIR || path.join(rootDir, ".report-build", "baseline"));
const candidateDir = path.resolve(process.env.RENDER_REPORT_CANDIDATE_DIR || path.join(rootDir, ".report-build", "candidate"));
const host = process.env.RENDER_REPORT_HOST || "127.0.0.1";
const basePort = Number(process.env.RENDER_REPORT_BASELINE_PORT || 4314);
const candPort = Number(process.env.RENDER_REPORT_CANDIDATE_PORT || 4315);
const maxPages = Number(process.env.RENDER_REPORT_MAX_PAGES || 30);
const threshold = Number(process.env.RENDER_REPORT_DIFF_THRESHOLD || 0.1);
const ratioWarn = Number(process.env.RENDER_REPORT_DIFF_RATIO_THRESHOLD || 0.001);

const shotsDir = path.join(reportRoot, "screenshots");
const diffsDir = path.join(reportRoot, "diffs");

const chromePath = resolveChromePath();

const viewports = [
  { name: "desktop", width: 1440, height: 1200 },
  { name: "mobile", width: 390, height: 844 },
];

await mkdir(reportRoot, { recursive: true });
await rm(shotsDir, { recursive: true, force: true });
await rm(diffsDir, { recursive: true, force: true });
await mkdir(shotsDir, { recursive: true });
await mkdir(diffsDir, { recursive: true });

const baselineServer = await startStaticServer(baselineDir, host, basePort);
const candidateServer = await startStaticServer(candidateDir, host, candPort);

try {
  const pages = await discoverPages(candidateDir, maxPages);
  const browser = await chromium.launch({
    headless: true,
    executablePath: chromePath,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });

  const results = [];

  for (const pagePath of pages) {
    for (const vp of viewports) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();

      const baseUrl = `http://${host}:${basePort}${pagePath}`;
      const candUrl = `http://${host}:${candPort}${pagePath}`;

      const baseShot = path.join(shotsDir, `baseline-${vp.name}-${slugify(pagePath)}.png`);
      const candShot = path.join(shotsDir, `candidate-${vp.name}-${slugify(pagePath)}.png`);
      const diffShot = path.join(diffsDir, `diff-${vp.name}-${slugify(pagePath)}.png`);

      await page.goto(baseUrl, { waitUntil: "networkidle" });
      await page.screenshot({ path: baseShot, fullPage: true });
      await page.goto(candUrl, { waitUntil: "networkidle" });
      await page.screenshot({ path: candShot, fullPage: true });

      const diff = await compareImages(baseShot, candShot, diffShot, threshold);
      const diffRatio = diff.totalPixels === 0 ? 0 : diff.diffPixels / diff.totalPixels;

      results.push({
        page: pagePath,
        viewport: vp.name,
        diffPixels: diff.diffPixels,
        totalPixels: diff.totalPixels,
        diffRatio,
        warn: diffRatio > ratioWarn,
        baseline: path.relative(reportRoot, baseShot),
        candidate: path.relative(reportRoot, candShot),
        diff: path.relative(reportRoot, diffShot),
      });

      await context.close();
    }
  }

  await browser.close();
  await writeReport(results);
  console.log(`render-report: wrote ${path.join(reportRoot, "index.html")}`);
} finally {
  await stopStaticServer(baselineServer);
  await stopStaticServer(candidateServer);
}

async function discoverPages(publicDir, limit) {
  const pages = [];
  const queue = [publicDir];
  while (queue.length > 0) {
    const dir = queue.pop();
    const entries = await readdir(dir, { withFileTypes: true });
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) {
        queue.push(full);
        continue;
      }
      if (e.name !== "index.html") continue;
      const rel = path.relative(publicDir, full).replace(/\/index\.html$/, "");
      const route = `/${rel.replace(/\\/g, "/")}`.replace(/\/+/g, "/");
      pages.push(route === "/" ? "/" : `${route}/`.replace(/\/+/g, "/"));
    }
  }
  pages.sort();
  return pages.slice(0, limit);
}

function slugify(route) {
  return route.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "root";
}

async function compareImages(pathA, pathB, outPath, thresholdValue) {
  const imgA = PNG.sync.read(await readFile(pathA));
  const imgB = PNG.sync.read(await readFile(pathB));
  const width = Math.max(imgA.width, imgB.width);
  const height = Math.max(imgA.height, imgB.height);

  const normA = new PNG({ width, height });
  const normB = new PNG({ width, height });
  PNG.bitblt(imgA, normA, 0, 0, imgA.width, imgA.height, 0, 0);
  PNG.bitblt(imgB, normB, 0, 0, imgB.width, imgB.height, 0, 0);

  const diff = new PNG({ width, height });
  const diffPixels = pixelmatch(normA.data, normB.data, diff.data, width, height, { threshold: thresholdValue });
  await writeFile(outPath, PNG.sync.write(diff));

  return { diffPixels, totalPixels: width * height };
}

async function writeReport(results) {
  const failedCount = results.filter((r) => r.warn).length;
  const rows = results.map((r) => `<tr><td>${escapeHtml(r.page)}</td><td>${r.viewport}</td><td>${(r.diffRatio * 100).toFixed(4)}%</td><td>${r.warn ? "WARN" : "OK"}</td><td><a href="${r.baseline}">baseline</a></td><td><a href="${r.candidate}">candidate</a></td><td><a href="${r.diff}">diff</a></td></tr>`).join("\n");
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Diff Report</title></head><body><h1>Diff Report</h1><p>Generated: ${new Date().toISOString()}</p><p>WARN rows: ${failedCount}/${results.length}</p><table border="1" cellspacing="0" cellpadding="6"><thead><tr><th>Page</th><th>Viewport</th><th>Diff Ratio</th><th>Status</th><th>Baseline</th><th>Candidate</th><th>Diff</th></tr></thead><tbody>${rows}</tbody></table></body></html>`;
  await writeFile(path.join(reportRoot, "index.html"), html, "utf8");
  await writeFile(path.join(reportRoot, "report.json"), JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2), "utf8");
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

async function startStaticServer(publicDir, bindHost, bindPort) {
  if (!existsSync(publicDir)) throw new Error(`Missing directory: ${publicDir}`);
  const server = createServer(async (req, res) => {
    try {
      let pathname = new URL(req.url || "/", `http://${bindHost}:${bindPort}`).pathname;
      let filePath = path.resolve(publicDir, `.${pathname}`);
      if (!filePath.startsWith(publicDir)) throw new Error("Forbidden");

      let info = await stat(filePath).catch(() => null);
      if (info && info.isDirectory()) {
        filePath = path.join(filePath, "index.html");
        info = await stat(filePath).catch(() => null);
      }

      if (!info || !info.isFile()) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }

      res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      createReadStream(filePath).pipe(res);
    } catch (e) {
      res.writeHead(500);
      res.end(String(e));
    }
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(bindPort, bindHost, () => resolve());
  });
  return server;
}

async function stopStaticServer(server) {
  await new Promise((resolve) => server.close(() => resolve()));
}

function resolveChromePath() {
  const explicit = process.env.CHROME_PATH;
  if (explicit && existsSync(explicit)) return explicit;

  const candidates = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ];

  for (const c of candidates) {
    if (existsSync(c)) return c;
  }

  throw new Error(
    "Chrome/Chromium executable not found. Set CHROME_PATH to a valid browser binary.",
  );
}
