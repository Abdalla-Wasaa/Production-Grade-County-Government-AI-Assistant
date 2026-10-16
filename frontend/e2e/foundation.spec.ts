import { expect, test } from '@playwright/test';

test('navigation, history, reload and localized deep links', async ({ page }) => {
  const external: string[] = [];
  page.on('request', (request) => {
    if (!request.url().startsWith('http://127.0.0.1:4173/')) external.push(request.url());
  });
  await page.goto('/');
  await page.getByRole('link', { name: 'View assistant preview' }).click();
  await expect(page).toHaveURL(/\/assistant$/);
  await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
  await expect(page.getByRole('textbox')).toHaveCount(0);
  await page.goBack();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'A clearer path to county information.',
  );
  await page.goForward();
  const selector = page.getByRole('combobox');
  await selector.focus();
  await selector.selectOption('sw');
  await expect(selector).toBeFocused();
  await expect(page.locator('html')).toHaveAttribute('lang', 'sw');
  await page.reload();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Msaidizi anaendelea kuandaliwa.',
  );
  await page.goto('/missing?private=never-display');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Hatukuweza kupata ukurasa huo.',
  );
  await expect(page.locator('body')).not.toContainText('never-display');
  expect(external).toEqual([]);
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(['county.ui.language.v1']);
});

test('keyboard skip link, language control and route focus', async ({ page }) => {
  await page.goto('/');
  // Start sequential navigation at the document start, as when entering the page.
  await page.evaluate(() => {
    document.querySelector<HTMLElement>('h1')?.blur();
  });
  await page.keyboard.press('Control+Home');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  const selector = page.getByRole('combobox');
  await selector.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page.locator('html')).toHaveAttribute('lang', 'sw');
  await expect(selector).toBeFocused();
  const link = page.getByRole('link', { name: 'Tazama onyesho la msaidizi' });
  await link.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
});

for (const width of [320, 768, 1440]) {
  test(`layout reflows at ${width}px in both languages`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    for (const language of ['en', 'sw']) {
      await page.getByRole('combobox').selectOption(language);
      await expect(page.getByRole('navigation')).toBeVisible();
      await expect(page.getByRole('combobox')).toBeVisible();
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
      ).toBe(true);
      await page.goto('/assistant');
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
      ).toBe(true);
      await page.goto('/');
    }
  });
}

test('invalid and unavailable storage do not block use', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('county.ui.language.v1', 'invalid');
  });
  await page.goto('/assistant');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => {
      throw new DOMException('Denied');
    };
    Storage.prototype.setItem = () => {
      throw new DOMException('Denied');
    };
  });
  await page.reload();
  await page.getByRole('combobox').selectOption('sw');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Msaidizi anaendelea kuandaliwa.',
  );
});

test('invalid public configuration produces a safe boundary fallback', async ({ page }) => {
  // Test the actual built error boundary by substituting only a local JS asset.
  await page.route('**/assets/*.js', async (route) => {
    const response = await route.fetch();
    const script = await response.text();
    const replaced = script.replace('/api/v1', 'https://private:secret@internal.invalid');
    expect(replaced).not.toBe(script);
    await route.fulfill({ response, body: replaced });
  });
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Something went wrong.');
  await expect(page.locator('body')).not.toContainText('internal.invalid');
  expect(errors.join(' ')).not.toMatch(/internal.invalid|private:secret|Invalid public API/);
});

test('route focus brings the new heading into view from a scrolled mobile page', async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 600 });
  await page.goto('/assistant');
  const homeLink = page.getByRole('link', { name: 'Return to home' });
  await homeLink.scrollIntoViewIfNeeded();
  await homeLink.click();
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toBeFocused();
  await expect(heading).toBeInViewport();
});
