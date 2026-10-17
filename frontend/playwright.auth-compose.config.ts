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
)
  throw new Error('Authentication acceptance requires a credential-free loopback origin.');
export default defineConfig({
  testDir: './e2e',
  testMatch: 'auth-compose.spec.ts',
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 90000,
  outputDir: '.artifacts/auth-compose-results',
  reporter: [['list'], ['junit', { outputFile: '.artifacts/auth-compose.xml' }]],
  use: { baseURL: target.origin, trace: 'off', screenshot: 'off', video: 'off' },
  projects: [{ name: 'auth-compose-chromium', use: { ...devices['Desktop Chrome'] } }],
});
