import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const fixturePath = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../tests/fixtures/sample.md",
);

test("upload, grounded answer, and insufficient evidence", async ({ page }) => {
  const uniqueName = `e2e-${Date.now()}.md`;
  await page.goto("/library");
  await page.locator('input[type="file"]').setInputFiles({
    name: uniqueName,
    mimeType: "text/markdown",
    buffer: fs.readFileSync(fixturePath),
  });
  await expect(page.getByRole("link", { name: uniqueName })).toBeVisible({ timeout: 15000 });

  await page.goto("/");
  await page.getByLabel("Research question").fill("What command rolls back the database migration?");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByText(/flyway rollback/i).first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("complementary", { name: "Evidence rail" }).getByText(/flyway rollback/i).first()).toBeVisible();

  await page.getByLabel("Ask another question").fill("What is the capital of Mars colony Zephyr-9?");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByText("Insufficient evidence")).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("complementary", { name: "Evidence rail" }).getByText("Open source")).toHaveCount(0);

  await page.route("**/api/v1/ask", (route) => {
    void route.fulfill({ status: 503, body: "Service unavailable" });
  });
  await page.getByLabel("Ask another question").fill("Another question?");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByText(/couldn't complete your research request/i)).toBeVisible({ timeout: 10000 });

  await page.goto("/library");
  const row = page.getByRole("row").filter({ hasText: uniqueName });
  await row.getByRole("button", { name: "Delete" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("link", { name: uniqueName })).toHaveCount(0, { timeout: 15000 });
});
