# Frontend foundation

P1-03 is an independent React/Vite/strict TypeScript/Tailwind 4 application shell.
It uses fictional information only and is not an official government service.
Routes are `/`, `/assistant` and a localized catch-all 404. The assistant is visibly
unavailable: no input, messages, fabricated history, authentication, AI or county API
integration. Backend and PostgreSQL availability do not affect this shell.

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
- `src/features/`: home, honest assistant placeholder and not-found page.
- `src/i18n/`: complete typed dictionaries, defensive resolution, preference storage.
- `src/config.ts`: public same-origin API path validation; no network client yet.
- `src/styles.css`: Tailwind entry, layout, colour/focus and responsive styles.

React state/context owns the language only. React Router uses declarative routes;
no server framework, loaders or auth guards are introduced. Native Fetch is the
choice for future consumers, but P1-03 makes no backend/provider/translation calls.
No API-client abstraction is created before there is a real consumer.

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
boundary. This value is reserved for future consumers and triggers no requests.

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
live outside the repository. Unit tests deny Fetch calls and need no backend.
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
backend, PostgreSQL, documentation and secret workflows remain in place. Do not
merge or start P1-04 without the owner's review/approval.
