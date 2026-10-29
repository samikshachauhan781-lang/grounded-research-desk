import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const fixturePath = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../tests/fixtures/sample.md",
);

test.describe("Live demo checklist", () => {
  test("Guide + RAG smoke (5 items)", async ({ page }) => {
    const uniqueName = `demo-${Date.now()}.md`;
    await page.goto("/library");
    await page.locator('input[type="file"]').setInputFiles({
      name: uniqueName,
      mimeType: "text/markdown",
      buffer: fs.readFileSync(fixturePath),
    });
    await expect(page.getByRole("link", { name: uniqueName })).toBeVisible({ timeout: 15000 });

    await page.goto("/");

    // [1] Guide button + welcome
    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText(/Hi! I'm your Research Desk Guide/i)).toBeVisible();

    // [2] FAQ responses
    await page.getByRole("button", { name: "How do I upload documents?" }).click();
    await expect(page.getByText(/\.md and \.txt/i)).toBeVisible();
    await page.getByRole("button", { name: "What are citations?" }).click();
    await expect(page.getByText(/document chunks/i)).toBeVisible();

    // [3] Navigation (Research first — already on /, then Library)
    await page.getByRole("button", { name: "Start Research" }).first().click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/(\?.*)?$/);
    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await page.getByRole("button", { name: "Open Library" }).first().click();
    await expect(page).toHaveURL(/\/library/);
    await expect(page.getByRole("dialog")).toHaveCount(0);

    await page.goto("/");
    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();

    // [4] Close controls
    await page.getByRole("dialog").getByRole("button", { name: "Close guide" }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);

    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await page.locator(".grd-guide-backdrop").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);

    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);

    // [5] Original RAG — rollback question + open citation
    await page.getByLabel("Research question").fill("What command rolls back the database migration?");
    await page.getByRole("button", { name: "Submit question" }).click();
    await expect(page.getByText(/flyway rollback/i).first()).toBeVisible({ timeout: 15000 });
    const evidence = page.getByRole("complementary", { name: "Evidence rail" });
    await expect(evidence.getByText(/flyway rollback/i).first()).toBeVisible();
    await evidence.getByRole("button", { name: "Open source" }).first().click();
    await expect(page).toHaveURL(/\/library\/.+/);
  });
});
