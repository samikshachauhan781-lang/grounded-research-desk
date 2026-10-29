import { test, expect } from "@playwright/test";

test.describe("Research Desk Guide", () => {
  test("opens, shows welcome, answers chip, closes with Escape", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Research Desk Guide" })).toBeVisible();
    await expect(page.getByText(/Hi! I'm your Research Desk Guide/i)).toBeVisible();
    await page.getByRole("button", { name: "How do I upload documents?" }).click();
    await expect(page.getByText(/\.md and \.txt/i)).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("navigation link closes panel and routes to library", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Open Research Desk Guide" }).click();
    await page.getByRole("button", { name: "Open Library" }).first().click();
    await expect(page).toHaveURL(/\/library/);
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });
});
