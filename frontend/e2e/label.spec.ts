import { expect, test } from '@playwright/test';
import path from 'node:path';

test('adds and removes a clause-type label on a sentence', async ({ page }) => {
  await page.goto('/upload');
  await page.getByText('Choose file').click();
  await page
    .locator('input[type="file"]')
    .setInputFiles(path.join(__dirname, 'fixtures', 'sample.txt'));
  await page.getByRole('button', { name: 'Upload' }).click();
  await expect(page).toHaveURL(/\/documents\/\d+$/);

  const confidentialitySentence = page
    .getByRole('listitem')
    .filter({ hasText: 'Each party shall keep all Confidential Information' });

  await confidentialitySentence.getByRole('button', { name: 'Add label' }).click();
  await page.getByRole('menuitem', { name: 'Confidentiality' }).click();

  await expect(confidentialitySentence.getByText('Confidentiality')).toBeVisible();

  await confidentialitySentence
    .getByRole('button', { name: /Remove Confidentiality label/ })
    .click();

  await expect(confidentialitySentence.getByText('Confidentiality')).toHaveCount(0);
});
