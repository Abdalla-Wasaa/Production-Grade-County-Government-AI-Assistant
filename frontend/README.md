# Frontend foundation

P1-03 is an independent React/Vite/strict TypeScript/Tailwind 4 application shell.
It uses fictional information only and is not an official government service.
Public routes remain `/`, `/assistant` and a localized catch-all 404. P2-02 source
adds `/login`, `/activate` and protected `/account`, with no public registration or
admin UI. Public preview routes initiate no authentication requests and remain
independent of backend availability. The assistant remains visibly unavailable.

P2-02 has actual isolated synthetic runtime evidence under the owner's explicit
17 October validation authorization: 53 unit/component tests, 78 preview-browser
cases and the real-backend Compose auth case passed. See
[the focused assessment](../docs/P2_02_EXPOSURE_ASSESSMENT.md) for the exact source,
security decision status and any remaining PR gate. Validation is not permission
for production, future source changes or silently reusing the P2-01 acceptance.

## Local setup

Use Node 24.22.0 with bundled npm 11.19.1. `.nvmrc`, package engines, `.npmrc` and
`packageManager` record the tested toolchain. Activate an isolated Node environment
if your host is older; do not install into coursework or change its environments.
From the repository root:

```bash
cd frontend
node --version
npm --version
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Navigate directly to `/assistant`, change the language,
reload and use browser back/forward. The dev server binds to loopback, requires
its configured port and supports SPA deep links. Stop it with Ctrl+C.

`npm run build` creates ignored `dist/`; `npm run preview` serves that build on
`http://127.0.0.1:4173` for local verification. Neither server is a production host.
Later hosting must explicitly support SPA fallback; unknown client routes render
the 404 page within a successful SPA document response, not an HTTP 404 status.

## Architecture and boundaries

- `src/main.tsx`: React root, strict mode, language context and browser router.
- `src/app/`: composition, safe error boundary and route title/focus management.
- `src/components/`: layout, native language selector and loading/error/empty states.
- `src/features/`: public preview pages and bounded `auth` client/context/pages.
- `src/i18n/`: complete typed dictionaries, defensive resolution, preference storage.
- `src/config.ts`: public same-origin API path validation for native Fetch auth.
- `src/styles.css`: Tailwind entry, layout, colour/focus and responsive styles.

React context owns language and memory-only authentication state. Native Fetch uses
same-origin cookies, no-store and redirect rejection. Account and conversation routes are guarded;
these guards provide UX, while backend authorization remains authoritative.
Web Locks serialize cookie-changing operations across tabs, with fresh CSRF inside
the lock before each mutation. BroadcastChannel carries only invalidation markers.
No access/CSRF/invitation token is written to storage or included in a redirect.
Refresh cookies remain backend-owned and HttpOnly. Missing browser coordination
capabilities fail closed. Ambiguous refresh is not automatically retried; sign in
afresh. Failed logout clears local identity but warns server revocation is unconfirmed.

Activation/reset uses the synthetic-v1 notice matching the synthetic backend.
A different configured version requires a reviewed notice-content update. Paste the
one-time token, or use `/activate#token=...`; initial fragment/query data is scrubbed
before React renders. Never use query-string tokens, analytics or telemetry. Only
language preference persists. Recovery remains operator-assisted; no public endpoint.

## Language and review gate

English is the default. Choosing English/Kiswahili updates visible text, page titles,
accessible names and `html[lang]`. Only `county.ui.language.v1` with value `en` or `sw`
is saved locally. Invalid values default to English; denied reads/writes continue
with in-memory state. Reload restores a valid saved preference. A language change
preserves the route and selector focus. No user/account/chat data is stored.

The Kiswahili dictionary is a development-quality draft, **pending human review**.
This status is visible in the footer in both languages. No external translation API
is used and no official linguistic approval is claimed. Before a real pilot,
appoint a fluent bilingual reviewer, review every key and scope/privacy statement,
record dated approval and resolve feedback under the
[pre-pilot gate](../docs/PRE_PILOT_GATE.md). Automated parity tests verify completeness,
not translation accuracy. The owner's implementation approval permits this draft;
it does not approve it for a real pilot.

TypeScript enforces identical keys and tests require nonempty values. Missing/blank
translations fall back to English with language markup; if both lookups fail, a fixed
English error label is used. Runtime fallback is a defense, not permission to ship
missing production dictionary entries.

## Public configuration and security

`VITE_API_BASE_URL` defaults to `/api/v1`; only a same-origin `/api` path with safe
segments is accepted. Origins, credentials, traversal, queries and fragments are
rejected with a generic message. Invalid configuration reaches the safe render
boundary. Authentication uses this path for approved account operations.

Vite loads environment files only from this frontend package (`envDir` is explicit).
Use `.env.example` as documentation; local `.env` files stay ignored. **Every VITE\_
value is public build-time configuration**, never a place for secrets. Keep all
backend database/provider/auth settings out of the frontend and browser bundle.

All content is ordinary React text. No raw HTML/Markdown injection, analytics,
telemetry, service worker or remote fonts/assets are enabled. Rendering failures
show fixed localized text and reload action. Default React caught/uncaught/recovery
reporting is disabled to prevent exception content being echoed to the console;
review privacy-safe diagnostic reporting before adding telemetry later.

## Quality checks

```bash
npm ci
npm ls --all
npm audit --audit-level=high
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
npx --no-install playwright install --with-deps chromium firefox webkit
npm run test:e2e
```

Playwright system dependencies are needed on a fresh Linux host; browser downloads
live outside the repository. Unit tests deny real Fetch calls; auth cases explicitly mock synthetic responses.
Browser tests run the actual production build on loopback. They cover navigation,
history, deep links, keyboard use, focus, both languages, denied storage, safe errors,
reflow and text enlargement. Browser automation checks for unexpected external
requests and confirms that only language preference is persisted.

axe scans home, assistant and 404 in both languages with WCAG 2 A/AA, 2.1 A/AA and
2.2 AA tags. Chromium, Firefox and WebKit projects provide engine coverage. These
are Playwright test builds, not certification against installed Chrome, Edge or
macOS/iOS Safari. Manual screen-reader/native-browser review is still required.

Keyboard route transitions focus the new page heading. Initial load keeps natural
Tab order so the skip link is first; language changes do not move focus. Layout
reflows down to 320 CSS pixels, uses visible focus and reduced-motion rules, and
provides semantic labels and loading/error announcements. See
[frontend verification](../docs/FRONTEND_VERIFICATION.md) for actual evidence and
remaining manual checks. WCAG 2.2 AA is a target, not a conformance certification.

## Dependency decisions

Exact direct pins and `package-lock.json` capture the installed tree; use `npm ci`
for repeat installs without lock changes. Metadata was checked before installation
and compatibility was validated by strict engine enforcement, `npm ls`, type/lint,
component tests, builds and browser execution. No force/legacy-peer install flags.

Node 24.22.0/npm 11.19.1; React/DOM 19.3.1; Router 8.4.0; Vite 8.3.4/React plugin
6.1.2; TypeScript 6.0.3; Tailwind/Vite plugin 4.3.3; Vitest 5.0.5/jsdom 30.1.3;
Testing Library 16.3.3; ESLint 10.12.0/typescript-eslint 8.71.2; Playwright 1.64.1;
axe integration 4.14.0. Prettier 3.9.10 provides reproducible formatting.

Current typescript-eslint excludes TypeScript 7, so TypeScript 6 is selected.
The proposed ESLint 9 was marked unsupported at installation; supported ESLint 10
is used instead. The current JSX accessibility lint plugin excludes ESLint 10, so
it is omitted rather than bypassing peers; axe browser checks and documented manual
review cover accessibility. Reassess compatible static accessibility rules in a
focused dependency update. See [Vite setup](https://vite.dev/guide/),
[Tailwind integration](https://tailwindcss.com/docs/installation/using-vite) and
[Playwright accessibility](https://playwright.dev/docs/accessibility-testing).

The frontend CI uses the pinned Node version, clean install, dependency security,
lint/format/types/unit/build/browser checks and lock-drift verification. Existing
backend, PostgreSQL, documentation and secret workflows remain in place. P1-04/P1-05 are now merged. Current P1-06 results belong in the consolidated
[acceptance record](../docs/PHASE_1_ACCEPTANCE.md); no merge or Phase 2 start is
permitted without the owner's separate approval.

## P2-02 authentication verification

Auth unit/component and preview-browser tests cover forms, safe errors, protected
routes, restoration/expiry, cross-tab serialization/revocation, memory-only tokens,
fragment scrubbing, keyboard behavior, bilingual labels and axe. Preview cases use
mocked API responses and are not proof of backend integration.

The normal `scripts/compose_smoke.py --browser` command additionally runs
`playwright.auth-compose.config.ts` against the actual auth-enabled backend/Nginx.
The fixture seeds a fresh synthetic invitation and hands credentials through an
owned temporary 0600 file; the environment carries only its path. It deletes the
file afterward. Browser cases cover real activation/login, HttpOnly cookie attributes,
restoration, automatic refresh, two tabs, bilingual axe and current-session revocation.
Auth traces/screenshots/videos are disabled to avoid credential/body artifacts.
The sanitized auth-compose.xml joins the existing retained browser evidence. No
workflow/check/ruleset changes are introduced. These cases were executed under the
owner's isolated validation grant; the first clock-fixture failure, test-only fix and
passing rerun are recorded in the assessment. Manual screen-reader and fluent
Kiswahili review remain required; automated axe is not WCAG certification.

## P2-04 conversation history source

Protected `/conversations` and `/conversations/:id` use the existing memory-only
authentication client. Users can list and paginate private conversations, create,
open, rename with an ETag, confirm deletion, and save user messages. Messages are
shown in ascending sequence, with explicit pagination. No assistant reply is
invented. New conversations use the selected interface language; changing the
interface does not rewrite the stored message language. Use synthetic content only.

The `features/conversations` module contains strict public DTO parsers, a bounded
API client, a session-scoped provider and accessible page/detail/dialog components.
Bearer requests omit cookies; backend ownership remains authoritative. Account or
session changes invalidate requests, clear pending data and remount the workspace.
Response bodies are checked again after decoding to reject late account responses.
No history, draft, access token or idempotency key is written to browser storage.

An ambiguous message submission retains its content and UUID key **in memory** for
an explicit identical retry; double submission shares one request. Navigation within
the authenticated application preserves an uncertain submission. Reload/closing the
tab loses the key, so the browser warns while a submission is pending. After reload,
inspect saved history before sending again; a new key can create another message.
Creation is not automatically retried. Stale rename versions require a reload.
Expired sessions return to sign-in; network outages do not erase a valid identity.

Prepared tests are `contracts.test.ts`, `client.test.ts` and `pages.test.tsx` in that
module, `e2e/history.spec.ts`, and the extended real-backend
`e2e/auth-compose.spec.ts`. Initial execution on c344364 produced 25 passing unit/client cases, nine component
setup failures and six passing/three failing browser cases. The real-backend
Compose history flow passed. Two corrections now await authorization to execute
the revised exposure; no passing result is claimed for the corrected source.
Runtime commands below require the owner's separate synthetic-validation approval:

```bash
npm run test:ci
npm run build
npm run test:e2e
```

The existing root `python scripts/compose_smoke.py --browser` also requires that
approval and runs the actual PostgreSQL/backend/Nginx authentication/history flow.
See [the P2-04 assessment](../docs/P2_04_EXPOSURE_ASSESSMENT.md) for static results,
scan evidence and the outstanding runtime/security decisions. Existing P2-03 green
CI is prerequisite evidence, not a passing result for this changed application.

The corrected ea2e842 validation passed all nine browser cases and the actual
Compose authentication/history flow; 32/34 focused unit/component cases passed.
Two remaining fixture corrections affect only `pages.test.tsx` and await the
owner's explicit test-inclusive exposure authorization before execution. Production
UI code is unchanged from that passing browser/Compose run. See the assessment for
exact source hashes, retained failures and PostgreSQL evidence reuse.
