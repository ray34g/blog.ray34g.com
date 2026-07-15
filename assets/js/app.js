// assets/js/app.js
import { initObfuscatedLink } from "./obfuscate-link.js";
import { initImageZoom } from "./image-zoom.js";

export function initApp() {
  initObfuscatedLink();
  initImageZoom();
}
