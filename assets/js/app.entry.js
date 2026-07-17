// assets/js/app.entry.js (Hugo template)

import { initApp } from "./app.js";
import * as params from "@params";

import { initThemeMenu } from "./theme.js";
import { initYouTubeFacades } from "./youtube-facade.js";

{{ if .Site.Params.appearance.useHeaderOverlay | default false -}}
import { initHeaderOverlay } from "./header-overlay.js";
{{- end }}

{{ if .Site.Params.enableSearch | default false -}}
import { initSearchModal } from "./search-modal.js";
import { initFuseSearch } from "./search-fuse.js";
{{- end }}

const LANG = params.lang || "ja";
const SEARCH_SOURCES = Array.isArray(params.searchSources) ? params.searchSources : [];

(() => {
  initApp();

  initThemeMenu();
  initYouTubeFacades();

  {{ if .Site.Params.appearance.useHeaderOverlay | default false -}}
  initHeaderOverlay();
  {{- end }}

  {{ if .Site.Params.enableSearch | default false -}}
  initSearchModal({ lang: LANG });
  initFuseSearch({ lang: LANG, sources: SEARCH_SOURCES });
  {{- end }}
})();
