import { defineConfig, devices } from '@playwright/test';

const target = new URL(process.env.COUNTY_BROWSER_BASE_URL ?? 'http://127.0.0.1:8080');
if (
  target.protocol !== 'http:' ||
  target.hostname !== '127.0.0.1' ||
  target.username ||
  target.password ||
  target.pathname !== '/' ||
  target.search ||
  target.hash
) {
  throw new Error('Compose smoke requires a credential-free loopback HTTP origin');
}

export default defineConfig({
  testDir: './e2e',
  testMatch: 'compose.spec.ts',
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 30000,
  outputDir: '.artifacts/compose-browser-results',
  reporter: [['list'], ['junit', { outputFile: '.artifacts/compose-browser.xml' }]],
  use: { baseURL: target.origin, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [{ name: 'compose-chromium', use: { ...devices['Desktop Chrome'] } }],
});
