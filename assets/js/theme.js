// assets/js/theme.js
export function initThemeMenu() {
  const storageKey = "appearance";

  const root = document.documentElement;
  const menu = document.getElementById("theme-menu-dropdown");
  const buttons = Array.from(document.querySelectorAll("button[data-theme-option]"));
  const lockedMode = (root.getAttribute("data-theme-lock") || "").toLowerCase();
  const hasLockedMode = lockedMode === "light" || lockedMode === "dark";

  const getsystemTheme = () => {
    const preferDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    return preferDark ? "dark" : "light";
  };

  const syncDropdownThemes = (theme) => {
    const menus = document.querySelectorAll("[data-light-theme-unless-dark-pref]");
    for (const el of menus) {
      if (theme === "dark") {
        el.removeAttribute("data-bs-theme");
      } else {
        el.setAttribute("data-bs-theme", "light");
      }
    }
  };

  const apply = (mode) => {
    const normalizedMode = typeof mode === "string" ? mode.toLowerCase() : "";
    const normalized = (normalizedMode === "system" || normalizedMode === "light" || normalizedMode === "dark") ? normalizedMode : "system";
    const theme = (normalized === "system") ? getsystemTheme() : normalized;

    root.setAttribute("data-bs-theme", theme);
    root.style.colorScheme = theme;
    root.setAttribute("data-theme-mode", normalized);
    syncDropdownThemes(theme);

    try { localStorage.setItem(storageKey, normalized); } catch (e) {}

    // 選択状態の見た目（Bootstrap標準の active を付ける）
    for (const b of buttons) {
      const opt = b.getAttribute("data-theme-option");
      b.classList.toggle("active", opt === normalized);
      b.setAttribute("aria-pressed", opt === normalized ? "true" : "false");
    }
  };

  if (hasLockedMode) {
    root.setAttribute("data-theme-lock", lockedMode);
    apply(lockedMode);
    try { localStorage.removeItem(storageKey); } catch (e) {}
    return;
  }

  if (!menu || buttons.length === 0) {
    apply(root.getAttribute("data-theme-mode") || "system");
    return;
  }

  // クリック
  for (const b of buttons) {
    b.addEventListener("click", () => {
      apply(b.getAttribute("data-theme-option"));
    });
  }

  // 初期同期（inline scriptが既に設定済みでも、active表示を揃える）
  let stored = null;
  try { stored = localStorage.getItem(storageKey); } catch (e) {}
  apply(stored || root.getAttribute("data-theme-mode") || "system");

  // system 選択中だけ OS 変更に追従
  const mql = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  if (mql && typeof mql.addEventListener === "function") {
    mql.addEventListener("change", () => {
      const mode = root.getAttribute("data-theme-mode") || "system";
      if (mode === "system") apply("system");
    });
  }
}
