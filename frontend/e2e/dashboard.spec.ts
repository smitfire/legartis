import { expect, test } from '@playwright/test';
import path from 'node:path';

test('dashboard filter and search narrow to the labelled contract', async ({ page }) => {
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

  // Filter by Confidentiality chip — only matching docs remain.
  await page.getByRole('option', { name: 'Confidentiality' }).click();
  await expect(page.getByRole('link', { name: /sample\.txt/ }).first()).toBeVisible();

  // Clear, then search by keyword.
  await page.getByRole('option', { name: 'Confidentiality' }).click();
  await page.getByRole('searchbox', { name: 'Search documents' }).fill('liability');
  await expect(page.getByRole('link', { name: /sample\.txt/ }).first()).toBeVisible();

  // Search for non-existent term → empty state.
  await page.getByRole('searchbox', { name: 'Search documents' }).fill('zzzzzz_no_such_text');
  await expect(page.getByText('No contracts yet')).toBeVisible();
});
