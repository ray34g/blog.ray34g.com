// assets/js/obfuscate-link.js

let initialized = false;

function b64ToUtf8(b64) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  if (window.TextDecoder) {
    return new TextDecoder("utf-8").decode(bytes);
  }
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
  return decodeURIComponent(escape(binary));
}

function decodeDataValue(text) {
  return decodeURIComponent(String(text).replace(/\+/g, "%20"));
}

function encodeDataValue(text) {
  return encodeURIComponent(String(text));
}

function encodeMailtoRecipient(text) {
  return encodeURIComponent(String(text)).replace(/%40/gi, "@");
}

function normalizeSubject(text) {
  return String(text).replace(/[\r\n]+/g, " ").trim();
}

function normalizeBody(text) {
  return String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/\n/g, "\r\n");
}

function escapeRegExp(text) {
  return String(text).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function replaceTemplateTokens(template, replacements) {
  const source = String(template);
  const tokens = Object.keys(replacements).filter(Boolean);
  if (!tokens.length) return source;

  const pattern = new RegExp(tokens.map(escapeRegExp).join("|"), "g");
  return source.replace(pattern, (token) => String(replacements[token] ?? ""));
}

function generateInquiryId() {
  const now = new Date();
  const yy = String(now.getFullYear()).slice(-2);
  const mm = `0${now.getMonth() + 1}`.slice(-2);
  const prefix = `INQ-${yy}${mm}-`;
  const alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
  const randomLength = 5;
  const bytes = new Uint8Array(randomLength);

  if (window.crypto && window.crypto.getRandomValues) {
    window.crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }

  let token = "";
  for (let i = 0; i < bytes.length; i += 1) {
    token += alphabet[bytes[i] % alphabet.length];
  }
  return prefix + token;
}

function replaceToken(text, token, value) {
  if (!token) return text;
  return String(text).split(token).join(value);
}

function materializeContactTemplate(link, extraReplacements = {}) {
  const placeholder = link.dataset.inquiryIdPlaceholder || "";
  const subjectTemplate =
    link.dataset.contactSubjectTemplate || decodeDataValue(link.dataset.subject || "");
  const bodyTemplate =
    link.dataset.contactBodyTemplate || decodeDataValue(link.dataset.body || "");
  link.dataset.contactSubjectTemplate = subjectTemplate;
  link.dataset.contactBodyTemplate = bodyTemplate;

  const replacements = {
    "[[NAME]]": "",
    "[[REPLY_TO]]": "",
    "[[MESSAGE]]": "",
    ...extraReplacements
  };
  if (placeholder && !Object.prototype.hasOwnProperty.call(replacements, placeholder)) {
    replacements[placeholder] = generateInquiryId();
  }

  const subjectWithId = replaceToken(subjectTemplate, placeholder, replacements[placeholder] || "");
  const bodyWithId = replaceToken(bodyTemplate, placeholder, replacements[placeholder] || "");
  const subject = normalizeSubject(replaceTemplateTokens(subjectWithId, replacements));
  const body = normalizeBody(replaceTemplateTokens(bodyWithId, replacements));

  link.dataset.subject = encodeDataValue(subject);
  link.dataset.body = encodeDataValue(body);
}

function buildMailtoHref(link) {
  const to = b64ToUtf8(link.dataset.toB64 || "");
  const subject = decodeDataValue(link.dataset.subject || "");
  const body = decodeDataValue(link.dataset.body || "");

  let href = "mailto:" + encodeMailtoRecipient(to);
  const query = [];
  if (subject) query.push(`subject=${encodeURIComponent(subject)}`);
  if (body) query.push(`body=${encodeURIComponent(body)}`);
  if (query.length) href += `?${query.join("&")}`;

  return href;
}

function buildRecipientOnlyMailtoHref(link) {
  const to = b64ToUtf8(link.dataset.toB64 || "");
  return "mailto:" + encodeMailtoRecipient(to);
}

function openMailtoLink(link) {
  window.location.href = buildMailtoHref(link);
}

function openRecipientOnlyMailtoLink(link) {
  window.location.href = buildRecipientOnlyMailtoHref(link);
}

function collectContactFormReplacements(form) {
  const replacements = {};
  const fields = form.querySelectorAll("[data-mailto-token]");
  fields.forEach((field) => {
    const token = field.dataset.mailtoToken || "";
    if (!token) return;
    const value = String(field.value || "").trim();
    replacements[token] = normalizeBody(value);
  });
  return replacements;
}

function copyTextToClipboard(text) {
  const value = String(text);
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(value);
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();

  return new Promise((resolve, reject) => {
    try {
      if (document.execCommand("copy")) {
        resolve();
      } else {
        reject(new Error("Copy command was not successful."));
      }
    } catch (error) {
      reject(error);
    } finally {
      textarea.remove();
    }
  });
}

function showContactCopyStatus(form) {
  const status = form.querySelector(".js-contact-copy-status");
  if (!status) return;

  const timeoutId = Number(status.dataset.copyStatusTimeout || 0);
  if (timeoutId) window.clearTimeout(timeoutId);

  status.textContent = status.dataset.copySuccess || "コピー完了";
  status.classList.remove("d-none");

  status.dataset.copyStatusTimeout = String(
    window.setTimeout(() => {
      status.classList.add("d-none");
      status.textContent = "";
      delete status.dataset.copyStatusTimeout;
    }, 2500)
  );
}

async function copyContactBodyToClipboard(form, link) {
  try {
    await copyTextToClipboard(decodeDataValue(link.dataset.body || ""));
    showContactCopyStatus(form);
    return true;
  } catch {
    return false;
  }
}

export function initObfuscatedLink() {
  if (initialized) return;
  initialized = true;

  document.addEventListener(
    "click",
    (e) => {
      const link = e.target.closest(".js-contact-mailto-template");
      if (!link) return;
      materializeContactTemplate(link);
    },
    true
  );

  document.addEventListener("submit", async (e) => {
    const form = e.target.closest(".js-contact-mailto-form");
    if (!form) return;

    e.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const link = form.querySelector(".js-contact-mailto-form-link");
    if (!link) return;

    materializeContactTemplate(link, collectContactFormReplacements(form));
    openMailtoLink(link);
  });

  document.addEventListener("click", async (e) => {
    const button = e.target.closest("#copy-address, #copy-template");
    if (!button) return;

    const form = button.closest(".js-contact-mailto-form");
    if (!form) return;

    const link = form.querySelector(".js-contact-mailto-form-link");
    if (!link) return;

    e.preventDefault();
    materializeContactTemplate(link, collectContactFormReplacements(form));

    if (button.id === "copy-address") {
      await copyContactBodyToClipboard(form, link);
      openRecipientOnlyMailtoLink(link);
      return;
    }

    copyContactBodyToClipboard(form, link);
  });

  document.addEventListener("click", (e) => {
    const link = e.target.closest(".js-obfuscated-mailto");
    if (!link) return;

    e.preventDefault();
    openMailtoLink(link);
  });
}
