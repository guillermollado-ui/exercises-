# SEO Analyzer

A small full-stack exercise: paste a URL, get its on-page SEO basics (title,
meta description, H1/H2 headings, word count), and see a history of the last
10 analyses. Backend is FastAPI + httpx + BeautifulSoup, persisted to
Firestore; frontend is a single Next.js (App Router) page that only talks to
the FastAPI backend.

## What it does

- `POST /api/analyze` — fetches a URL server-side, parses it, saves the
  result to Firestore, and returns it.
- `GET /api/analyses` — the last 10 saved analyses, newest first.
- `GET /api/health` — liveness check.
- The frontend has one page: a URL input + "Analyze" button, the result of
  the latest analysis, and the history list. Loading and error states are
  shown inline; the frontend never talks to Firebase directly.

## Running it locally

### Prerequisites
- Python 3.11+ (tested with 3.14)
- Node.js 18+ (tested with Node 24)
- A Firebase project with Firestore enabled, and a service account key JSON

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # defaults work for local dev, edit if needed
```

Place your Firebase service account key at `backend/serviceAccountKey.json`
(Firebase Console → Project Settings → Service Accounts → Generate new
private key). This file is gitignored and must never be committed.

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if backend isn't on :8000
npm run dev
```

Open `http://localhost:3000`.

### Troubleshooting: SSL certificate errors on Windows

If the backend logs `CERTIFICATE_VERIFY_FAILED` when fetching pages or
talking to Firestore, it's almost always local antivirus/corporate TLS
inspection (e.g. Avast) injecting a root certificate that Python's bundled
CA store doesn't trust — not a bug in this app. curl/browsers use the
Windows trust store and work fine; Python's `httpx` and the Firestore
client's `grpc` transport each ship their own CA bundle. Two independent
workarounds, applied only in the dev venv (not part of the app's own
dependencies):

- `pip install pip-system-certs` fixes `httpx`/`ssl`-based calls (page
  fetching).
- Exporting the Windows Root/CA certificate stores to a PEM file and setting
  `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` to it fixes the Firestore/`grpc` calls.

## Running the tests

```bash
cd backend
.venv\Scripts\activate   # or source .venv/bin/activate
pytest -v
```

26 tests, all offline: HTTP fetches are mocked via `httpx.get` monkeypatching
with real `httpx.Response` objects built from local HTML fixtures, DNS
resolution is mocked at `url_safety.resolve_hostname` (except for literal-IP
cases, which resolve locally without any network call), and Firestore is
mocked at both the `firestore_repo` client layer and the route layer. No
test touches the network or a real Firestore project.

Frontend has no unit test suite (out of scope for this exercise); it's
verified via `npm run build` (type-checking + lint) and a manual/Playwright
smoke test of the golden path and one error path.

## Key decisions and why

- **SSRF protection resolves DNS itself, before fetching.** `url_safety.py`
  parses the URL, rejects non-`http(s)` schemes, resolves the hostname via
  `socket.getaddrinfo`, and blocks the request if *any* resolved address is
  loopback/private/link-local/reserved/multicast/unspecified, or if the host
  is literally `localhost`. This also blocks DNS-rebinding-style attacks
  (a normal-looking hostname that resolves to a private IP), which a
  scheme-only or literal-string check would miss. `resolve_hostname` is a
  thin wrapper specifically so tests can monkeypatch DNS without hitting the
  network, while private-IP tests use IP literals directly (no DNS needed at
  all, since `getaddrinfo` doesn't do a lookup for a literal address).

- **Redirects are re-validated hop by hop, not auto-followed.** The first
  version let `httpx` follow redirects automatically after validating only
  the original URL — so a public URL that 302'd to a private IP (e.g. a
  cloud metadata endpoint) would bypass the SSRF guard entirely, since the
  redirect target was never checked. This was caught during the `revisor`
  subagent review, not by the test suite (which only had redirect-free
  fixtures at that point). `fetch_html` now disables `httpx`'s
  `follow_redirects` and re-runs `ensure_safe_url` on every `Location`
  header before following it, capped at `MAX_REDIRECTS`. Covered by
  `test_analyze_blocks_ssrf_via_redirect`, `test_analyze_follows_safe_redirect`,
  and `test_analyze_too_many_redirects`.

- **Error handling is a small typed hierarchy, not string matching.**
  `errors.py` defines `InvalidURLError` / `BlockedURLError` /
  `FetchTimeoutError` / `FetchConnectionError` / `NonHTMLContentError`, and
  `main.py` maps each to an HTTP status in one place. This keeps the
  analyzer/url_safety modules free of HTTP concerns and makes the mapping
  easy to audit. One consequence: a DNS resolution failure (host doesn't
  exist) surfaces as `400` (it's caught during URL validation, before any
  HTTP attempt), while a post-DNS connection failure (refused, reset, TLS
  error) surfaces as `502`, and a timeout as `504`.

- **Firestore is mocked at the function boundary, not with a fake SDK.**
  `firestore_repo.py` exposes `save_analysis()` / `get_recent_analyses()`;
  tests monkeypatch these directly at the route layer (`app.main.*`) for
  endpoint tests, and monkeypatch `get_firestore_client()` with a
  `MagicMock` for repo-level tests that assert the actual query shape
  (`order_by("analyzed_at", DESCENDING).limit(10)`). No custom fake
  Firestore implementation to maintain.

- **`html.parser` instead of `lxml`.** It's in the standard library, no
  compiled dependency, and is fast enough for single-page analysis. Script
  and style tags are stripped before computing word count so their content
  isn't counted as page copy.

- **Frontend is plain CSS, no UI kit.** One page, a handful of components —
  a component library would be overhead for this scope.

## What I'd improve with more time

- Rate limiting / abuse protection on `/api/analyze` (currently anyone with
  the URL can hit an arbitrary target through the backend, bounded only by
  the SSRF guard and the 10s timeout).
- Cursor-based pagination for `/api/analyses` beyond the last 10.
- Pin the DNS-resolved IP for the actual `httpx` fetch (not just the
  pre-flight check) to fully close a very-short-TTL DNS-rebinding window
  between validation and fetch.
- Server-render the history list on first load instead of a client-side
  fetch-after-mount, to avoid the "Loading history..." flash.
- A CI workflow (pytest + `next build`) on push.
- Bump Next.js to v16 to clear a residual transitive `postcss` advisory that
  a minor-version bump can't reach (noted during `npm audit`, low severity
  and build-time only, deferred since a major bump is out of scope here).

## How I used AI

I used Claude Code as a pair programmer end to end, driven by a CLAUDE.md
process file that requires a plan up front, explicit approval before
implementing, minimal-intervention changes, verification before calling
anything done, and a local `revisor` subagent review before merge.

Workflow: I described the task; Claude proposed a full plan (folder layout,
endpoints, libraries, exact test list) and waited for my go-ahead before
writing any code. Implementation went backend-first, module by module
(SSRF guard → analyzer → Firestore repo → schemas → routes → tests), running
`pytest` after each meaningful addition rather than at the very end. Once
the backend suite was green, it moved to the frontend, then did a real
end-to-end smoke test: started both servers for real, wrote a small
Playwright script to drive the actual browser (not just `curl`), and used
that to catch two real integration bugs a unit-test suite wouldn't have
caught — a CORS origin mismatch when the default dev port was already taken,
and a local-machine SSL trust issue affecting the Firestore client. Both
were root-caused and fixed (or documented as environment-specific) rather
than worked around silently. Finally, a `revisor`-persona subagent (the
project's own custom agent definition wasn't picked up by this harness since
the repo isn't at the working-directory root, so I ran an equivalent review
with the same instructions and acceptance criteria) reviewed the implemented
diff against CLAUDE.md's rules and the task's acceptance criteria before I
considered anything done — it correctly failed the first pass, flagging a
real SSRF bypass: `fetch_html` validated the original URL but let `httpx`
auto-follow redirects, so a public URL that 302'd to a private IP would
never be re-checked. That's a genuine, directly exploitable gap the test
suite hadn't covered (all fixtures were redirect-free), not a nitpick. I
fixed it — redirects are now followed manually with `ensure_safe_url`
re-run on every hop — added regression tests for the bypass, the legitimate
case, and a redirect-loop cap, and reran the full suite before moving on.
I reviewed the full `git diff` myself before any commit.
