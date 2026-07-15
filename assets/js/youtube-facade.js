export function initYouTubeFacades() {
  const warmConnections = () => {
    if (document.documentElement.dataset.youtubePreconnected) return;

    [
      "https://www.youtube-nocookie.com",
      "https://www.google.com",
      "https://googleads.g.doubleclick.net",
      "https://static.doubleclick.net",
    ].forEach((href) => {
      const link = document.createElement("link");
      link.rel = "preconnect";
      link.href = href;
      document.head.append(link);
    });

    document.documentElement.dataset.youtubePreconnected = "true";
  };

  document.querySelectorAll("[data-youtube-embed]").forEach((button) => {
    button.addEventListener("pointerover", warmConnections, { once: true });
    button.addEventListener("focus", warmConnections, { once: true });

    button.addEventListener(
      "click",
      () => {
        const videoId = button.dataset.youtubeEmbed;
        if (!videoId) return;

        const iframe = document.createElement("iframe");
        iframe.className = "youtube-embed bg-black border-0 rounded-4 d-block w-100 h-100 overflow-hidden";
        iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1`;
        iframe.title = button.dataset.youtubeTitle || "YouTube video";
        iframe.loading = "lazy";
        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
        iframe.allowFullscreen = true;
        iframe.referrerPolicy = "strict-origin-when-cross-origin";

        const facade = button.closest(".youtube-facade");
        (facade || button).replaceWith(iframe);
        iframe.focus();
      },
      { once: true }
    );
  });
}
