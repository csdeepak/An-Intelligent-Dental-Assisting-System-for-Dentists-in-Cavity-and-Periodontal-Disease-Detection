// Render the composition with headless Chrome over the DevTools protocol — no npm packages:
// Node's built-in WebSocket talks to Chrome, frames are piped straight into ffmpeg.
//
//   node render.mjs stills <outDir> <t1> <t2> ...     PNG stills at those times (seconds)
//   node render.mjs video <out.mp4> [fromSec] [toSec] silent H.264 at 30 fps
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, existsSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PAGE = pathToFileURL(join(HERE, "site", "index.html")).href + "?capture=1";
const FPS = 30;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function launch() {
  const prof = join(HERE, "chrome-profile");
  if (existsSync(prof)) rmSync(prof, { recursive: true, force: true });
  mkdirSync(prof, { recursive: true });
  const proc = spawn(CHROME, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${prof}`, "--no-first-run",
    "--no-default-browser-check", "--hide-scrollbars", "--mute-audio", "--force-device-scale-factor=1", "--window-size=1920,1080",
    "--allow-file-access-from-files", "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows", "--font-render-hinting=none", "about:blank"], { stdio: "ignore" });
  const portFile = join(prof, "DevToolsActivePort");
  for (let i = 0; i < 200 && !existsSync(portFile); i++) await sleep(100);
  const [port, path] = readFileSync(portFile, "utf8").trim().split("\n");
  const ws = new WebSocket(`ws://127.0.0.1:${port}${path}`);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(), listeners = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
    else listeners.forEach(f => f(m));
  };
  const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
    const mid = ++id; pending.set(mid, { res, rej }); ws.send(JSON.stringify({ id: mid, method, params, sessionId }));
  });
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  const s = (m, p) => send(m, p, sessionId);
  const logs = [];
  listeners.push(m => {
    if (m.method === "Runtime.consoleAPICalled") logs.push(`[console.${m.params.type}] ` + m.params.args.map(a => a.value ?? a.description).join(" "));
    if (m.method === "Runtime.exceptionThrown") logs.push("[exception] " + JSON.stringify(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  });
  await s("Page.enable"); await s("Runtime.enable");
  await s("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  const loaded = new Promise(r => listeners.push(m => { if (m.method === "Page.loadEventFired") r(); }));
  await s("Page.navigate", { url: PAGE });
  await loaded;
  const ev = async expr => {
    const r = await s("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`page exception: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
    return r.result.value;
  };
  await ev("window.ready");
  const missing = await ev("window.__missingCues");
  if (missing && missing.length) logs.push("[missing cues] " + missing.join(", "));
  return { proc, ws, s, ev, logs, total: await ev("window.TOTAL") };
}

async function frame(ctx, t, format = "jpeg") {
  await ctx.ev(`window.renderAt(${t}); new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))`);
  const shot = await ctx.s("Page.captureScreenshot", format === "png" ? { format: "png" } : { format: "jpeg", quality: 93, optimizeForSpeed: true });
  return Buffer.from(shot.data, "base64");
}

const [mode, out, ...rest] = process.argv.slice(2);
const ctx = await launch();
try {
  if (mode === "stills") {
    mkdirSync(out, { recursive: true });
    for (const t of rest.map(Number)) writeFileSync(join(out, `t${t.toFixed(2).padStart(7, "0")}.png`), await frame(ctx, t, "png"));
    console.log(`stills -> ${out}`);
  } else if (mode === "video") {
    const from = rest[0] ? Number(rest[0]) : 0, to = rest[1] ? Number(rest[1]) : ctx.total;
    const n = Math.round((to - from) * FPS);
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", resolve(out)], { stdio: ["pipe", "inherit", "inherit"] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const buf = await frame(ctx, from + i / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if (i % 300 === 0) { const el = (Date.now() - t0) / 1000; console.log(`frame ${i}/${n}  ${(i / Math.max(el, 0.001)).toFixed(1)} fps  eta ${((n - i) / Math.max(i / el, 0.001) / 60).toFixed(1)} min`); }
    }
    ff.stdin.end();
    await new Promise(r => ff.on("close", r));
    console.log(`video -> ${out}  (${n} frames, ${((Date.now() - t0) / 60000).toFixed(1)} min)`);
  }
  if (ctx.logs.length) console.log(ctx.logs.join("\n"));
} finally {
  ctx.ws.close(); ctx.proc.kill();
}
