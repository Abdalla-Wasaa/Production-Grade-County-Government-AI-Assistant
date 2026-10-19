import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import type { Locator } from '@playwright/test';

// Credentials are read from a private disposable file, never CLI arguments/env
// values or report attachments. No traces, videos or screenshots are retained.
function fixture(): { token: string; password: string; email: string } {
  const path = process.env.COUNTY_AUTH_FIXTURE_FILE;
  if (!path) throw new Error('Private synthetic authentication fixture is required.');
  const value: unknown = JSON.parse(readFileSync(path, 'utf8'));
  if (
    !value ||
    typeof value !== 'object' ||
    !('token' in value) ||
    !('password' in value) ||
    !('email' in value) ||
    typeof value.token !== 'string' ||
    typeof value.password !== 'string' ||
    typeof value.email !== 'string' ||
    !value.email.endsWith('@example.invalid')
  )
    throw new Error('Invalid private synthetic fixture.');
  return { token: value.token, password: value.password, email: value.email };
}
async function privateFill(locator: Locator, value: string) {
  try {
    await locator.fill(value);
  } catch {
    throw new Error('Could not fill private synthetic form field.');
  }
}
test('actual Nginx activation, login, bilingual account, refresh, cross-tab restoration and revocation', async ({
  page,
  context,
}) => {
  const data = fixture();
  // Install before app startup so its already-scheduled refresh timer is controlled.
  await page.clock.install();
  let secretInUrl = false;
  let refreshes = 0;
  context.on('request', (request) => {
    if ([data.token, data.password].some((value) => request.url().includes(value)))
      secretInUrl = true;
    if (request.url().endsWith('/auth/refresh')) refreshes++;
  });
  await page.goto('/activate');
  await privateFill(page.getByLabel('Invitation or recovery token'), data.token);
  await privateFill(page.getByLabel('Password', { exact: true }), data.password);
  await privateFill(page.getByLabel('Confirm password'), data.password);
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Set password and activate' }).click();
  await expect(page.getByRole('heading', { name: 'Password saved' })).toBeVisible();
  expect((await context.cookies()).some((cookie) => cookie.name === 'county_refresh')).toBe(false);
  await page.getByRole('link', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeEnabled();
  await privateFill(page.getByLabel('Email address'), data.email);
  await privateFill(page.getByLabel('Password', { exact: true }), data.password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'My account', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'This browser session' })).toBeVisible();
  const cookies = (await context.cookies()).filter((cookie) =>
    ['county_refresh', 'county_csrf'].includes(cookie.name),
  );
  expect(cookies.length).toBe(2);
  expect(
    cookies.every(
      (cookie) => cookie.httpOnly && cookie.sameSite === 'Strict' && cookie.path === '/api/v1/auth',
    ),
  ).toBe(true);
  await page.getByRole('combobox').selectOption('sw');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Akaunti yangu');
  const axe = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(axe.violations).toEqual([]);
  await page.getByRole('combobox').selectOption('en');
  // P2-04: actual persistence API through Nginx, never a model response.
  await page.getByRole('link', { name: 'My conversations', exact: true }).click();
  await page.getByLabel('New conversation title (optional)').fill('Synthetic history smoke');
  await page.getByRole('button', { name: 'Create conversation', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Synthetic history smoke', exact: true }),
  ).toBeVisible();
  await page
    .getByLabel('Your fictional message')
    .fill('Synthetic saved question without AI generation');
  // A matching draft textarea is not proof of persistence. Wait for the actual
  // write and the reloaded history list before testing a full browser reload.
  const persisted = page.waitForResponse(
    (response) =>
      response.url().endsWith('/messages') &&
      response.request().method() === 'POST' &&
      response.status() === 201,
  );
  await page.getByRole('button', { name: 'Save message', exact: true }).click();
  await persisted;
  const savedMessage = page
    .getByRole('list', { name: 'Saved messages', exact: true })
    .getByText('Synthetic saved question without AI generation', { exact: true });
  await expect(savedMessage).toBeVisible();
  await page.reload();
  await expect(savedMessage).toBeVisible();
  await page.getByLabel('Conversation title', { exact: true }).fill('Renamed synthetic history');
  await page.getByRole('button', { name: 'Save title', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Renamed synthetic history', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await page.getByRole('button', { name: 'Keep conversation', exact: true }).click();
  await page.getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await page.getByRole('button', { name: 'Delete permanently', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Choose a conversation', exact: true }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'My account', exact: true }).click();
  const other = await context.newPage();
  await Promise.all([page.reload(), other.goto('/account')]);
  await expect(page.getByRole('heading', { name: 'This browser session' })).toBeVisible();
  await expect(other.getByRole('heading', { name: 'This browser session' })).toBeVisible();
  const previous = refreshes;
  await page.bringToFront();
  const rotated = page.waitForResponse(
    (response) =>
      response.url().endsWith('/auth/refresh') &&
      response.request().method() === 'POST' &&
      response.status() === 200,
  );
  await page.clock.fastForward(871000);
  await rotated;
  await expect.poll(() => refreshes > previous).toBe(true);
  await expect(page.getByRole('heading', { name: 'My account', exact: true })).toBeVisible();
  const stored = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
  }));
  expect(stored).toEqual({ local: ['county.ui.language.v1'], session: [] });
  expect(secretInUrl).toBe(false);
  await other.getByRole('button', { name: 'Revoke this session' }).click();
  await expect(other).toHaveURL(/\/login$/);
  await expect(page).toHaveURL(/\/login$/);
});
