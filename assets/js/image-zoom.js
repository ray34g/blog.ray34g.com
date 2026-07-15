export function initImageZoom() {
  const modalEl = document.getElementById("imageZoomModal");
  if (!modalEl || !window.bootstrap) return;
  const belowBootstrapMd = window.matchMedia("(max-width: 767.98px)");

  const imageEl = document.getElementById("imageZoomModalImage");
  const bodyEl = modalEl.querySelector(".modal-body");
  const zoomLinks = document.querySelectorAll('a[data-zoom="true"]');
  if (!imageEl) return;
  if (!zoomLinks.length) return;

  zoomLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      if (!belowBootstrapMd.matches) return;
      event.preventDefault();
      event.stopPropagation();
    });
  });

  modalEl.addEventListener("show.bs.modal", (event) => {
    if (belowBootstrapMd.matches) {
      event.preventDefault();
      return;
    }

    const trigger = event.relatedTarget?.closest?.('a[data-zoom="true"]');
    if (!trigger) return;

    imageEl.src = trigger.getAttribute("href") || "";
    imageEl.alt = trigger.querySelector("img")?.getAttribute("alt") || "";
  });

  modalEl.addEventListener("hidden.bs.modal", () => {
    imageEl.removeAttribute("src");
    imageEl.alt = "";
  });

  bodyEl?.addEventListener("click", (event) => {
    if (event.target !== bodyEl) return;
    bootstrap.Modal.getInstance(modalEl)?.hide();
  });
}
