// assets/js/header-overlay.js

function clamp01(value) {
  return Math.max(0, Math.min(1, value));
}

function setHeaderOverlayProgress(value) {
  document.documentElement.style.setProperty(
    "--header-overlay-progress",
    String(clamp01(value))
  );
}

function readCssNumber(style, name, fallback) {
  const raw = style.getPropertyValue(name).trim();
  if (!raw) return fallback;
  const n = Number.parseFloat(raw); // "240px" でも 240 になる
  return Number.isFinite(n) ? n : fallback;
}

function computeZoneProgress(headerBottom, zoneRect, rangeMaxPx) {
  const zoneBottom = zoneRect.bottom;
  const zoneHeight = Math.max(1, zoneRect.height);
  const range = Math.min(zoneHeight, rangeMaxPx);

  const raw = 1 - (zoneBottom - headerBottom) / range;
  return clamp01(raw);
}

export function initHeaderOverlay() {
  const header = document.getElementById("site-header");
  if (!header) return;
  if (!header.hasAttribute("data-header-overlay")) return;

  const zones = Array.from(document.querySelectorAll("[data-header-overlay-zone]"));

  // zone が無いページは何もしない（= bg-primaryの通常表示）
  if (zones.length === 0) return;

  const headerStyle = window.getComputedStyle(header);

  // px前提（必要なら "240px" でもOK）
  const rangeMaxPx = readCssNumber(headerStyle, "--header-overlay-range-max", 240);
  const rootMarginPx = readCssNumber(headerStyle, "--header-overlay-root-margin", rangeMaxPx);

  const activeZones = new Set();
  let observerReady = false;

  let ticking = false;

  const computeProgressFromList = (zoneList) => {
    const headerBottom = header.getBoundingClientRect().bottom;

    let progress = 0;
    for (const zone of zoneList) {
      const rect = zone.getBoundingClientRect();
      const p = computeZoneProgress(headerBottom, rect, rangeMaxPx);
      if (p > progress) progress = p;
      if (progress >= 1) break;
    }
    return progress;
  };

  const update = () => {
    ticking = false;

    // ちらつき対策：Observerがreadyになるまでは全zonesで同期計算
    if (!observerReady) {
      setHeaderOverlayProgress(computeProgressFromList(zones));
      return;
    }

    // 近傍にactiveが無ければ overlay区間外 → 不透明(=1)
    if (activeZones.size === 0) {
      setHeaderOverlayProgress(1);
      return;
    }

    setHeaderOverlayProgress(computeProgressFromList(activeZones));
  };

  const requestUpdate = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  };

  // scroll だけ（resize は付けない）
  window.addEventListener("scroll", requestUpdate, { passive: true });

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) activeZones.add(entry.target);
        else activeZones.delete(entry.target);
      }
      observerReady = true;
      requestUpdate();
    },
    {
      root: null,
      rootMargin: `${rootMarginPx}px 0px ${rootMarginPx}px 0px`,
      threshold: 0,
    }
  );

  for (const zone of zones) observer.observe(zone);

  // 初期安定化（同期→次フレーム）
  update();
  window.requestAnimationFrame(() => requestUpdate());
}