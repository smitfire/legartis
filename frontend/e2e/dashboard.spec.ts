import { expect, test } from '@playwright/test';
import path from 'node:path';

test('dashboard filter and search narrow to the labelled contract', async ({ page }) => {
  // Production-quality guard: any JS error or failed request fails the test.
  // A render loop on the chip filter previously fired hundreds of requests
  // before Chrome returned ERR_INSUFFICIENT_RESOURCES — this catches it.
  const pageErrors: Error[] = [];
  const failedRequests: string[] = [];
  page.on('pageerror', (err) => pageErrors.push(err));
  page.on('requestfailed', (req) => failedRequests.push(`${req.method()} ${req.url()}`));

  // Upload + label a contract so the dashboard has something to filter on.
  await page.goto('/upload');
  await page.getByText('Choose file').click();
  await page
    .locator('input[type="file"]')
    .setInputFiles(path.join(__dirname, 'fixtures', 'sample.txt'));
  await page.getByRole('button', { name: 'Upload' }).click();
  await expect(page).toHaveURL(/\/documents\/\d+$/);

  await page
    .getByRole('listitem')
    .filter({ hasText: 'Each party shall keep all Confidential Information' })
    .getByRole('button', { name: 'Add label' })
    .click();
  await page.getByRole('menuitem', { name: 'Confidentiality' }).click();

  // Navigate to the dashboard.
  await page.getByRole('link', { name: 'All contracts' }).click();
  await expect(page).toHaveURL('/');

  // Confirm card visible.
  await expect(page.getByText('sample.txt').first()).toBeVisible();

  // Chips show per-type document counts so users never click a filter that
  // yields zero results. Confidentiality has at least one match, Non-Compete
  // has zero — the latter chip is disabled.
  await expect(page.getByRole('option', { name: /Confidentiality \(\d+\)/ })).toBeVisible();
  await expect(page.getByRole('option', { name: /Non-Compete \(0\)/ })).toBeDisabled();

  // Filter by Confidentiality chip — only matching docs remain.
  await page.getByRole('option', { name: /Confidentiality/ }).click();
  await expect(page.getByRole('link', { name: /sample\.txt/ }).first()).toBeVisible();

  // Clear, then search by keyword.
  await page.getByRole('option', { name: /Confidentiality/ }).click();
  await page.getByRole('searchbox', { name: 'Search documents' }).fill('liability');
  await expect(page.getByRole('link', { name: /sample\.txt/ }).first()).toBeVisible();

  // Search for non-existent term → empty state.
  await page.getByRole('searchbox', { name: 'Search documents' }).fill('zzzzzz_no_such_text');
  await expect(page.getByText('No contracts yet')).toBeVisible();

  // Give Angular a moment to settle, then assert no JS errors or failed requests.
  await page.waitForTimeout(500);
  expect(pageErrors, `Unhandled JS errors: ${pageErrors.map((e) => e.message).join('; ')}`).toEqual(
    [],
  );
  expect(failedRequests, `Failed requests: ${failedRequests.join('; ')}`).toEqual([]);
});
