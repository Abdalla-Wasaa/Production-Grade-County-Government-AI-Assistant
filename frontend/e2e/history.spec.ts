import AxeBuilder from '@axe-core/playwright';
import { test, expect } from '@playwright/test';
import type { BrowserContext } from '@playwright/test';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
const id = '10000000-0000-4000-8000-000000000001';
const when = '2026-10-18T12:00:00Z';
async function fixture(context: BrowserContext) {
  let signed = true;
  let version = 1;
  let title = 'Synthetic saved topic';
  let exists = true;
  const messages: Record<string, unknown>[] = [];
  const keys = new Map<string, Record<string, unknown>>();
  await context.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const user = {
      id: '00000000-0000-4000-8000-000000000001',
      email: 'history@example.invalid',
      role: 'citizen',
      preferred_language: 'en',
    };
    const row = () => ({
      id,
      title,
      language: 'en',
      version,
      created_at: when,
      updated_at: when,
      expires_at: '2026-11-17T12:00:00Z',
    });
    const json = (status: number, value: unknown = null, etag = false) =>
      route.fulfill({
        status,
        headers: { 'Content-Type': 'application/json', ...(etag ? { ETag: `"${version}"` } : {}) },
        body: status === 204 ? '' : JSON.stringify(value),
      });
    if (path.endsWith('/auth/csrf')) return json(200, { csrf_token: 'synthetic-history-csrf' });
    if (path.endsWith('/auth/refresh'))
      return signed
        ? json(200, {
            access_token: 'synthetic-history-access',
            token_type: 'bearer',
            expires_in: 900,
            user,
          })
        : json(401);
    if (path.endsWith('/auth/me')) return signed ? json(200, user) : json(401);
    if (path.endsWith('/auth/logout')) {
      signed = false;
      return json(204);
    }
    if (!signed || !request.headers().authorization) return json(401);
    if (path === '/api/v1/conversations') {
      if (method === 'POST') {
        exists = true;
        title = (request.postDataJSON() as { title?: string }).title ?? 'New conversation';
        return json(201, row(), true);
      }
      return json(200, { items: exists ? [row()] : [], next_cursor: null });
    }
    if (!exists || !path.startsWith('/api/v1/conversations/' + id)) return json(404);
    if (path.endsWith('/messages')) {
      if (method === 'POST') {
        const key = request.headers()['idempotency-key']!;
        const old = keys.get(key);
        if (old) return json(200, old, true);
        const m = {
          id: crypto.randomUUID(),
          conversation_id: id,
          role: 'user',
          content: (request.postDataJSON() as { content: string }).content,
          language: 'en',
          sequence: messages.length + 1,
          created_at: when,
        };
        messages.push(m);
        keys.set(key, m);
        version++;
        return json(201, m, true);
      }
      return json(200, { items: messages, next_cursor: null }, true);
    }
    if (method === 'PATCH') {
      if (request.headers()['if-match'] !== `"${version}"`) return json(412);
      title = (request.postDataJSON() as { title: string }).title;
      version++;
    }
    if (method === 'DELETE') {
      exists = false;
      messages.length = 0;
      return json(204);
    }
    return json(200, row(), true);
  });
}
test.beforeEach(async ({ context }) => fixture(context));
test('bilingual keyboard history flow persists text, renames and confirms deletion', async ({
  page,
}) => {
  await page.goto('/conversations');
  await page.getByRole('link', { name: /Synthetic saved topic/ }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Synthetic saved topic' })).toBeFocused();
  await page.getByLabel('Your fictional message').fill('<script>fictional plain text</script>');
  await page.getByRole('button', { name: 'Save message' }).click();
  await expect(
    page.getByText('<script>fictional plain text</script>', { exact: true }),
  ).toBeVisible();
  await page.getByLabel('Conversation title', { exact: true }).fill('Renamed saved topic');
  await page.getByRole('button', { name: 'Save title' }).click();
  await expect(page.getByRole('heading', { name: 'Renamed saved topic' })).toBeVisible();
  await page.getByRole('combobox').selectOption('sw');
  await expect(page.getByLabel('Ujumbe wako wa kubuni')).toBeVisible();
  await page.getByRole('combobox').selectOption('en');
  const accessibility = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Keep conversation' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Delete conversation', exact: true }),
  ).toBeFocused();
  await page.getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await page.getByRole('button', { name: 'Delete permanently' }).click();
  await expect(page.getByRole('heading', { name: 'Choose a conversation' })).toBeVisible();
});
test('responsive saved history stays within a narrow viewport', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto('/conversations/' + id);
  await expect(page.getByLabel('Your fictional message')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
});
test('cross-tab invalidation clears rendered messages and protects session restoration', async ({
  context,
  page,
}) => {
  await page.goto('/conversations/' + id);
  await page.getByLabel('Your fictional message').fill('Private synthetic message');
  await page.getByRole('button', { name: 'Save message' }).click();
  await expect(page.getByText('Private synthetic message', { exact: true })).toBeVisible();
  const other = await context.newPage();
  await other.goto('/');
  await other.evaluate(() => {
    const c = new BroadcastChannel('county.auth.invalidate.v1');
    c.postMessage('invalidate');
    c.close();
  });
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  await expect(page.getByText('Private synthetic message', { exact: true })).not.toBeVisible();
  const storage = await page.evaluate(() => Object.keys(localStorage));
  expect(storage.filter((key) => key !== 'county.ui.language.v1')).toEqual([]);
});
