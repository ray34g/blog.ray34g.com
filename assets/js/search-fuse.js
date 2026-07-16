// assets/js/search-fuse.js
export function initFuseSearch(options = {}) {
  const modalEl = document.getElementById("searchModal");
  const inputEl = document.getElementById("search-input");
  const resultsEl = document.getElementById("search-results");
  const statusEl = document.getElementById("search-status");
  const emptyEl = document.getElementById("search-empty");
  if (!modalEl || !inputEl || !resultsEl) return;

  const lang = (options.lang || document.documentElement.lang || "ja").toLowerCase();
  const indexBaseURL = String(options.indexBaseURL || "").replace(/\/$/, "");
  const indexPath = lang.startsWith("en") ? "/en/index.json" : "/index.json";
  const INDEX_URL = `${indexBaseURL}${indexPath}`;
  let indexPromise = null;
  let indexData = null;
  let fuse = null;

  const setStatus = (t) => { if (statusEl) statusEl.textContent = t || ""; };

  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c])
  );

  function render(items) {
    resultsEl.innerHTML = "";
    if (!items || items.length === 0) {
      setStatus("No results.");
      return;
    }
    const frag = document.createDocumentFragment();
    items.forEach((item) => {
      const a = document.createElement("a");
      a.className = "list-group-item list-group-item-action";
      a.href = item.url;
      a.setAttribute("role", "option");

      const title = escapeHtml(item.title || item.url);
      const url = escapeHtml(item.url);
      const summary = item.summary ? escapeHtml(item.summary) : "";

      a.innerHTML = `
        <div class="fw-semibold">${title}</div>
        ${summary ? `<small class="text-body-secondary d-block">${summary}</small>` : ""}
        <small class="text-body-secondary">${url}</small>
      `.trim();

      frag.appendChild(a);
    });
    resultsEl.appendChild(frag);
    setStatus(`${items.length} results.`);
  }

  async function loadIndex() {
    if (indexData) return indexData;
    if (!indexPromise) {
      // Search indexes change independently from fingerprinted assets. Always
      // revalidate so a browser cannot retain stale cross-site destinations.
      indexPromise = fetch(INDEX_URL, { credentials: "same-origin", cache: "no-cache" })
        .then((r) => r.ok ? r.json() : Promise.reject(new Error(String(r.status))))
        .then((data) => {
          indexData = Array.isArray(data) ? data : [];
          return indexData;
        })
        .catch((err) => {
          console.error("index.json load failed", err);
          indexData = [];
          return indexData;
        });
    }
    return indexPromise;
  }

  function ensureFuse(data) {
    if (fuse) return fuse;
    if (!window.Fuse) return null;

    fuse = new window.Fuse(data, {
      includeScore: true,
      shouldSort: true,
      threshold: 0.35,        // ノイズが多ければ 0.30 くらいへ
      ignoreLocation: true,
      minMatchCharLength: 1,  // ご希望どおり
      keys: [
        { name: "title", weight: 0.75 },
        { name: "summary", weight: 0.2 },
        { name: "content", weight: 0.05 },
      ],
    });
    return fuse;
  }

  // モーダルが開いたら先読み（体感改善）
  modalEl.addEventListener("shown.bs.modal", async () => {
    setStatus("Loading…");
    const data = await loadIndex();
    const f = ensureFuse(data);
    setStatus(f ? "Ready." : "Search unavailable.");
  });

  // 閉じたらUIリセット
  modalEl.addEventListener("hidden.bs.modal", () => {
    inputEl.value = "";
    resultsEl.innerHTML = "";
    if (emptyEl) emptyEl.classList.remove("d-none");
    setStatus("");
  });

  // 入力→検索
  let debounce = null;
  inputEl.addEventListener("input", () => {
    const q = inputEl.value || "";
    if (emptyEl) emptyEl.classList.toggle("d-none", q.trim().length > 0);

    window.clearTimeout(debounce);
    debounce = window.setTimeout(async () => {
      if (!q.trim()) {
        resultsEl.innerHTML = "";
        setStatus("");
        return;
      }
      const data = await loadIndex();
      const f = ensureFuse(data);
      if (!f) {
        setStatus("Search unavailable.");
        return;
      }
      const hits = f.search(q).slice(0, 30).map((x) => x.item);
      render(hits);
    }, 60);
  });
}
