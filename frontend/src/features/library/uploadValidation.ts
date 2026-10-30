import type { PublicSettings } from "../../lib/api/client";

export const FALLBACK_ALLOWED_EXTENSIONS = [".md", ".txt"] as const;

export type ClientUploadValidationResult = { ok: true } | { ok: false; message: string };

function normalizeExtension(ext: string): string {
  const trimmed = ext.trim().toLowerCase();
  if (!trimmed) return "";
  return trimmed.startsWith(".") ? trimmed : `.${trimmed}`;
}

function normalizedAllowList(allowedExtensions: string[]): string[] {
  const list = allowedExtensions.map(normalizeExtension).filter(Boolean);
  return list.length > 0 ? list : [...FALLBACK_ALLOWED_EXTENSIONS];
}

/** Allowed extensions from public settings, or .md / .txt fallback. */
export function resolveAllowedExtensions(settings: PublicSettings | null): string[] {
  const fromSettings = settings?.allowed_upload_extensions;
  if (fromSettings?.length) {
    return normalizedAllowList(fromSettings);
  }
  return [...FALLBACK_ALLOWED_EXTENSIONS];
}

/** Value for `<input accept="...">` aligned with server allowlist. */
export function filePickerAcceptAttribute(allowedExtensions: string[]): string {
  return normalizedAllowList(allowedExtensions).join(",");
}

export function getUploadFileExtension(filename: string): string {
  const base = filename.split(/[/\\]/).pop() ?? filename;
  const lower = base.toLowerCase();
  const dot = lower.lastIndexOf(".");
  if (dot <= 0) {
    return "";
  }
  return lower.slice(dot);
}

export function isExtensionAllowed(filename: string, allowedExtensions: string[]): boolean {
  const ext = getUploadFileExtension(filename);
  if (!ext) {
    return false;
  }
  const allowed = new Set(normalizedAllowList(allowedExtensions));
  return allowed.has(ext);
}

export function unsupportedUploadMessage(filename: string, allowedExtensions: string[]): string {
  const list = normalizedAllowList(allowedExtensions).join(", ");
  return `"${filename}" is not supported. Supported formats: ${list}.`;
}

export function supportedFormatsLabel(allowedExtensions: string[]): string {
  return `Supported formats: ${normalizedAllowList(allowedExtensions).join(", ")}`;
}

/** Client-side gate before POST /api/v1/documents (picker and drag-and-drop). */
export function validateClientUpload(
  file: File,
  allowedExtensions: string[],
): ClientUploadValidationResult {
  if (isExtensionAllowed(file.name, allowedExtensions)) {
    return { ok: true };
  }
  return {
    ok: false,
    message: unsupportedUploadMessage(file.name, allowedExtensions),
  };
}
