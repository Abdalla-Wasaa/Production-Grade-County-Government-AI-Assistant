import { expect, test } from '@playwright/test';

test('built Nginx application loads, switches language, navigates and refreshes', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();
  const language = page.getByRole('combobox');
  await language.selectOption('sw');
  await expect(page.locator('html')).toHaveAttribute('lang', 'sw');
  await language.selectOption('en');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await page
    .locator('nav')
    .getByRole('link', { name: /assistant/i })
    .click();
  await expect(page).toHaveURL(/\/assistant$/);
  await page.reload();
  await expect(page.getByRole('main')).toBeVisible();
  expect(errors).toEqual([]);
});
