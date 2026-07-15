// assets/js/search-modal.js
export function initSearchModal() {
  const modalEl = document.getElementById("searchModal");
  if (!modalEl || !window.bootstrap) return;

  const inputEl = document.getElementById("search-input");
  const triggers = Array.from(
    document.querySelectorAll([
        ".search-button",
        '[data-bs-toggle="modal"][data-bs-target="#searchModal"]',
        'a[href="#searchModal"]',
      ].join(","))
    );
  if (triggers.length === 0) return;

  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform);

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl, {
    backdrop: true,
    focus: true,
    keyboard: true,
  });

  // 最後に使ったトリガー（閉じた後に戻す）
  let lastTrigger = triggers[0] || null;

  const focusInput = () => {
    // focus trap の確定後に入れるため 1tick 遅らせる
    setTimeout(() => {
      inputEl?.focus?.({ preventScroll: true });
      inputEl?.select?.();
    }, 0);
  };

  modalEl.addEventListener("shown.bs.modal", focusInput);

  // ★重要：閉じる直前にフォーカスを “モーダル外” へ逃がす（警告対策）
  modalEl.addEventListener("hide.bs.modal", () => {
    const target =
      lastTrigger && typeof lastTrigger.focus === "function" ? lastTrigger : null;

    // blur は効かないことがあるので、退避フォーカスを 1tick 遅らせて確実化
    setTimeout(() => {
      document.activeElement?.blur?.();
      (target || document.body).focus?.({ preventScroll: true });
    }, 0);
  });

  function openModalSafely(fromEl) {
    // offcanvas 内から呼ばれたら先に閉じてから開く
    const offcanvasEl = fromEl?.closest?.(".offcanvas");
    if (offcanvasEl && offcanvasEl.classList.contains("show")) {
      const oc = bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl);
      offcanvasEl.addEventListener(
        "hidden.bs.offcanvas",
        () => modal.show(),
        { once: true }
      );
      oc.hide();
      return;
    }
    modal.show();
  }

  // クリックは “これだけ” に統一（重複登録しない）
  triggers.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      lastTrigger = btn;
      openModalSafely(btn);
    });
  });

  // Ctrl/Cmd + / と Ctrl/Cmd + K
  document.addEventListener("keydown", (e) => {
    const t = e.target;
    const typing =
      t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
    if (typing) return;

    const mod = isMac ? e.metaKey : e.ctrlKey;
    const slash = mod && (e.key === "/" || e.code === "Slash");
    const k = mod && e.key.toLowerCase() === "k";
    if (!slash && !k) return;

    e.preventDefault();
    lastTrigger = document.activeElement instanceof HTMLElement ? document.activeElement : lastTrigger;

    if (!modalEl.classList.contains("show")) openModalSafely(null);
    else focusInput();
  });
}