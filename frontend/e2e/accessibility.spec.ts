import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

for (const route of ['/', '/assistant', '/missing']) {
  for (const language of ['en', 'sw']) {
    test(`WCAG automated checks: ${route} ${language}`, async ({ page }) => {
      await page.goto(route);
      await page.getByRole('combobox').selectOption(language);
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(results.violations).toEqual([]);
    });
  }
}

test('reduced motion is respected', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(
    true,
  );
  const duration = await page
    .getByRole('combobox')
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(duration).toBe('0s');
});

test('text enlargement preserves navigation and reflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto('/');
  await page.evaluate(() => {
    document.documentElement.style.fontSize = '200%';
  });
  for (const language of ['en', 'sw']) {
    await page.getByRole('combobox').selectOption(language);
    await expect(page.getByRole('combobox')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
});
