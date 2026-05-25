import { expect, test } from '@playwright/test';
import path from 'node:path';

test('uploads a contract and lands on the document detail page', async ({ page }) => {
  await page.goto('/upload');

  await page.getByText('Choose file').click();
  await page
    .locator('input[type="file"]')
    .setInputFiles(path.join(__dirname, 'fixtures', 'sample.txt'));

  await expect(page.getByText('sample.txt')).toBeVisible();
  await page.getByRole('button', { name: 'Upload' }).click();

  await expect(page).toHaveURL(/\/documents\/\d+$/);
  await expect(page.getByRole('heading', { name: 'sample.txt' })).toBeVisible();
  await expect(
    page.getByText('Each party shall keep all Confidential Information secret for five years.'),
  ).toBeVisible();
});
