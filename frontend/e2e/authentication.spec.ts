import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import type { BrowserContext } from '@playwright/test';
// Auth tests never retain traces/screenshots containing request bodies or inputs.
test.use({ trace: 'off', screenshot: 'off' });
const user = {
  id: '00000000-0000-4000-8000-000000000001',
  email: 'browser@example.invalid',
  role: 'citizen',
  preferred_language: 'en',
};
const session = {
  id: '00000000-0000-4000-8000-000000000002',
  created_at: '2026-10-17T12:00:00Z',
  last_used_at: '2026-10-17T12:00:00Z',
  expires_at: '2026-10-24T12:00:00Z',
  is_current: true,
};
async function api(context: BrowserContext, initial = false) {
  let signedIn = initial;
  let csrf = 0;
  let active = 0;
  let maxActive = 0;
  let unavailable = false;
  await context.route('**/api/v1/auth/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.split('/auth')[1]!;
    const json = (status: number, body: unknown = null) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: status === 204 ? '' : JSON.stringify(body),
      });
    if (unavailable) return json(503);
    if (path === '/csrf') return json(200, { csrf_token: 'fixture-' + ++csrf });
    if (request.method() !== 'GET' && request.headers()['x-csrf-token'] !== 'fixture-' + csrf)
      return json(403);
    if (path === '/activate') return json(204);
    if (path === '/login') {
      const body: unknown = request.postDataJSON();
      if (
        !body ||
        typeof body !== 'object' ||
        !('password' in body) ||
        body.password !== 'Synthetic-browser-password'
      )
        return json(401);
      signedIn = true;
    }
    if (path === '/refresh' || path === '/login') {
      active++;
      maxActive = Math.max(maxActive, active);
      await new Promise((resolve) => setTimeout(resolve, 30));
      active--;
      return signedIn
        ? json(200, {
            access_token: 'fixture-access-' + csrf,
            token_type: 'bearer',
            expires_in: 900,
            user,
          })
        : json(401);
    }
    if (path === '/logout' || path === '/logout-all' || path.startsWith('/sessions/')) {
      signedIn = false;
      return json(204);
    }
    if (!signedIn) return json(401);
    if (path === '/me') return json(200, user);
    if (path === '/sessions') return json(200, { items: [session], next_cursor: null });
    return json(404);
  });
  return {
    maxActive: () => maxActive,
    outage: (value: boolean) => {
      unavailable = value;
    },
  };
}
async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeEnabled();
  await page.getByLabel('Email address').fill(user.email);
  await page.getByLabel('Password', { exact: true }).fill('Synthetic-browser-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'My account', exact: true })).toBeVisible();
}
test('guards routes, login failure is accessible and successful login restores across reload', async ({
  page,
  context,
}) => {
  await api(context);
  await page.goto('/account');
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Email address').fill(user.email);
  await page.getByLabel('Password', { exact: true }).fill('wrong-synthetic');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('alert')).toBeFocused();
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('');
  await signIn(page);
  await page.reload();
  await expect(page.getByText(user.email)).toBeVisible();
  expect(
    await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
    })),
  ).toEqual({ local: ['county.ui.language.v1'], session: [] });
  await page.getByRole('button', { name: 'Sign out all sessions' }).click();
  await expect(page).toHaveURL(/\/login$/);
});
test('concurrent same-context tabs serialize restoration and propagate revocation', async ({
  page,
  context,
}) => {
  const server = await api(context, true);
  const other = await context.newPage();
  await Promise.all([page.goto('/account'), other.goto('/account')]);
  await expect(page.getByText(user.email)).toBeVisible();
  await expect(other.getByText(user.email)).toBeVisible();
  expect(server.maxActive()).toBe(1);
  await page.getByRole('button', { name: 'Revoke this session' }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(other).toHaveURL(/\/login$/);
});
test('activation fragment is scrubbed and success never logs in automatically', async ({
  page,
  context,
}) => {
  await api(context);
  await page.goto('/activate#token=' + 'a'.repeat(43));
  expect(await page.evaluate(() => location.hash === '' && location.search === '')).toBe(true);
  await page.getByLabel('Password', { exact: true }).fill('Synthetic-browser-password');
  await page.getByLabel('Confirm password').fill('Synthetic-browser-password');
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Set password and activate' }).click();
  await expect(page.getByRole('heading', { name: 'Password saved' })).toBeVisible();
  expect(await page.evaluate(() => location.pathname)).toBe('/activate');
});
test('unavailable backend can recover without showing protected content', async ({
  page,
  context,
}) => {
  const server = await api(context, true);
  server.outage(true);
  await page.goto('/account');
  await expect(page.getByRole('alert')).toContainText('unavailable');
  expect(await page.getByText(user.email).count()).toBe(0);
  server.outage(false);
  await page.getByRole('button', { name: 'Retry session check' }).click();
  // CSRF bootstrap failed before any rotation; explicit retry can restore safely.
  await expect(page.getByText(user.email)).toBeVisible();
});
for (const path of ['/login', '/activate', '/account'])
  for (const language of ['en', 'sw'])
    test(`auth keyboard/reflow/axe ${path} ${language}`, async ({ page, context }) => {
      await api(context, path === '/account');
      await page.setViewportSize({ width: 320, height: 850 });
      await page.goto(path);
      await page.getByRole('combobox').selectOption(language);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await page.keyboard.press('Tab');
      const scan = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(scan.violations).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
    });
