import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api/client";
import { parseApiErrorMessage, resolveUploadErrorMessage } from "../../lib/api/errorMessage";
import {
  FALLBACK_ALLOWED_EXTENSIONS,
  filePickerAcceptAttribute,
  isExtensionAllowed,
  resolveAllowedExtensions,
  supportedFormatsLabel,
  validateClientUpload,
} from "./uploadValidation";

const ALLOWED = [".md", ".txt"];

function mockFile(name: string): File {
  return new File(["content"], name, { type: "application/octet-stream" });
}

describe("uploadValidation", () => {
  it("accepts valid TXT upload before API call", () => {
    const file = mockFile("notes.txt");
    expect(isExtensionAllowed(file.name, ALLOWED)).toBe(true);
    expect(validateClientUpload(file, ALLOWED)).toEqual({ ok: true });
  });

  it("accepts valid Markdown upload before API call", () => {
    const file = mockFile("readme.md");
    expect(isExtensionAllowed(file.name, ALLOWED)).toBe(true);
    expect(validateClientUpload(file, ALLOWED)).toEqual({ ok: true });
  });

  it("rejects PDF before API call", () => {
    const file = mockFile("report.pdf");
    const result = validateClientUpload(file, ALLOWED);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toContain("report.pdf");
      expect(result.message).toContain(".md");
      expect(result.message).toContain(".txt");
    }
  });

  it("rejects DOCX before API call", () => {
    const file = mockFile("spec.docx");
    const result = validateClientUpload(file, ALLOWED);
    expect(result.ok).toBe(false);
  });

  it("rejects JPG before API call", () => {
    const file = mockFile("scan.jpg");
    const result = validateClientUpload(file, ALLOWED);
    expect(result.ok).toBe(false);
  });

  it("rejects unsupported drag-and-drop file with a clear message", () => {
    const file = mockFile("photo.jpeg");
    const result = validateClientUpload(file, ALLOWED);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toMatch(/not supported/i);
      expect(result.message).toMatch(/Supported formats:/);
    }
  });

  it("syncs file picker accept attribute with allowed extensions", () => {
    expect(filePickerAcceptAttribute([".txt", ".md"])).toBe(".txt,.md");
    expect(filePickerAcceptAttribute([])).toBe(".md,.txt");
  });

  it("uses settings allowlist when present", () => {
    expect(
      resolveAllowedExtensions({
        app_name: "test",
        app_env: "development",
        embedding_provider: "fake",
        embedding_model_name: "fake",
        llm_provider: "mock",
        retrieval_top_k: 5,
        allowed_upload_extensions: [".txt", ".md"],
        max_upload_bytes: 5242880,
        agent_enabled: false,
        demo_mode: false,
      }),
    ).toEqual([".txt", ".md"]);
  });

  it("falls back to md and txt when settings missing", () => {
    expect(resolveAllowedExtensions(null)).toEqual([...FALLBACK_ALLOWED_EXTENSIONS]);
    expect(supportedFormatsLabel(ALLOWED)).toBe("Supported formats: .md, .txt");
  });
});

describe("upload API error messages", () => {
  it("displays backend 422 error.message when available", () => {
    const body = JSON.stringify({
      error: {
        code: "VALIDATION_ERROR",
        message: "Unsupported file type '.exe'. Allowed: ['.txt', '.md']",
      },
    });
    expect(parseApiErrorMessage(body)).toContain("Unsupported file type");
    const msg = resolveUploadErrorMessage(new ApiError(422, body));
    expect(msg).toContain("Unsupported file type");
  });

  it("displays backend 413 with size guidance", () => {
    const body = JSON.stringify({
      error: { code: "PAYLOAD_TOO_LARGE", message: "File exceeds max size of 5242880 bytes" },
    });
    const msg = resolveUploadErrorMessage(new ApiError(413, body), 5_242_880);
    expect(msg).toContain("5242880");
  });

  it("uses fallback when 413 body is not JSON", () => {
    const msg = resolveUploadErrorMessage(new ApiError(413, ""), 5_242_880);
    expect(msg).toContain("5 MB");
  });

  it("uses generic fallback for unexpected errors", () => {
    expect(resolveUploadErrorMessage(new Error("network"))).toBe("Upload failed. Please try again.");
  });

  it("does not call upload API when client validation fails", () => {
    const upload = vi.fn();
    const file = mockFile("bad.pdf");
    const check = validateClientUpload(file, ALLOWED);
    if (!check.ok) {
      expect(check.message).toBeTruthy();
    } else {
      upload(file);
    }
    expect(upload).not.toHaveBeenCalled();
  });
});

/**
 * Mirrors LibraryPage onUpload + drop guard (uploading + uploadInFlightRef).
 * Regression: second drop while first upload pending must not call API again.
 */
async function simulateLibraryUploadFlow(
  file: File,
  uploadDocument: (file: File) => Promise<void>,
  flight: { uploading: boolean; inFlight: boolean },
): Promise<void> {
  if (flight.uploading || flight.inFlight) {
    return;
  }
  const clientCheck = validateClientUpload(file, ALLOWED);
  if (!clientCheck.ok) {
    return;
  }
  flight.inFlight = true;
  flight.uploading = true;
  try {
    await uploadDocument(file);
  } finally {
    flight.inFlight = false;
    flight.uploading = false;
  }
}

describe("library upload in-flight guard", () => {
  it("calls uploadDocument once when a second drop happens during pending upload", async () => {
    const file = mockFile("notes.md");
    const uploadDocument = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(resolve, 30);
        }),
    );
    const flight = { uploading: false, inFlight: false };

    const first = simulateLibraryUploadFlow(file, uploadDocument, flight);
    await simulateLibraryUploadFlow(file, uploadDocument, flight);
    await first;

    expect(uploadDocument).toHaveBeenCalledTimes(1);
    expect(uploadDocument).toHaveBeenCalledWith(file);
    expect(flight.uploading).toBe(false);
    expect(flight.inFlight).toBe(false);
  });
});
