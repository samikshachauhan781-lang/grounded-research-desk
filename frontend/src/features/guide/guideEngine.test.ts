import { describe, expect, it } from "vitest";
import {
  matchGuideQuery,
  WELCOME_REPLY,
  SUGGESTED_CHIPS,
  WELCOME_TEXT,
} from "./guideEngine";
import { GUIDE_ASSISTANT_NAME } from "./guideConfig";

describe("guideEngine", () => {
  it("exposes welcome content and suggested chips", () => {
    expect(GUIDE_ASSISTANT_NAME).toBe("Research Desk Guide");
    expect(WELCOME_REPLY.text).toBe(WELCOME_TEXT);
    expect(SUGGESTED_CHIPS).toHaveLength(5);
    expect(WELCOME_REPLY.links?.some((l) => l.to === "/library")).toBe(true);
  });

  it("matches upload FAQ", () => {
    const r = matchGuideQuery("How do I upload documents?");
    expect(r.text.toLowerCase()).toContain("library");
    expect(r.text.toLowerCase()).toContain(".md");
  });

  it("matches insufficient evidence FAQ", () => {
    const r = matchGuideQuery("what does insufficient evidence mean");
    expect(r.text.toLowerCase()).toContain("insufficient");
  });

  it("returns fallback for unknown questions", () => {
    const r = matchGuideQuery("quantum blockchain nft pricing");
    expect(r.text.toLowerCase()).toContain("not sure");
    expect(r.followUpChips?.length).toBeGreaterThan(0);
  });

  it("includes navigation links for settings", () => {
    const r = matchGuideQuery("settings environment config");
    expect(r.links?.some((l) => l.to === "/settings")).toBe(true);
  });

  it("redirects document-specific questions to Research", () => {
    const r = matchGuideQuery("what does my document say about rollback");
    expect(r.text.toLowerCase()).toContain("research");
    expect(r.links?.some((l) => l.to === "/")).toBe(true);
  });
});
