# Auth And Permissions Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate authentication to HttpOnly cookie priority, lock down system-level alert endpoints, and remove dangerous demo-admin defaults.

**Architecture:** Keep JWT as the server-side auth primitive, but move browser persistence from `localStorage` to `HttpOnly` cookie. Preserve Bearer compatibility during the transition. Tighten alert endpoint authorization based on existing `admin_required`, and make startup bootstrap opt-in instead of dangerous by default.

**Tech Stack:** Flask, Flask test client, pytest, Vue 3, Pinia, Vue Router, Axios

---

### Task 1: Add failing backend auth and authorization tests

**Files:**
- Modify: `tests/test_auth_jwt.py`
- Modify: `tests/test_authz.py`

**Step 1: Write the failing tests**

Add tests for:
- `/api/session/check` returns `authenticated: false` when unauthenticated
- `/api/session/extend` returns `401` when unauthenticated
- `/api/auth/login` sets `weibo_access_token`
- `/api/auth/logout` clears `weibo_access_token`
- cookie-based auth works for protected endpoints
- non-admin users are blocked from alert rule mutation endpoints and alert broadcast/test endpoints

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth_jwt.py tests/test_authz.py -q`

Expected:
- New auth/cookie tests fail
- New alert permission tests fail

**Step 3: Commit no production code yet**

Do not change implementation before seeing the failures.

### Task 2: Implement cookie-priority auth on the backend

**Files:**
- Modify: `src/app.py`
- Modify: `src/views/api/api.py`

**Step 1: Implement cookie helpers**

Add:
- helper to read auth cookie
- helper to set auth cookie on login
- helper to clear auth cookie on logout

**Step 2: Update auth resolution**

Change auth lookup order:
1. Bearer token
2. auth cookie

**Step 3: Fix session endpoints**

Make:
- `/api/session/check` return false/null when unauthenticated
- `/api/session/extend` return `401` when unauthenticated

**Step 4: Re-run targeted tests**

Run: `pytest tests/test_auth_jwt.py -q`

Expected: all auth-related tests pass

### Task 3: Lock down system-level alert endpoints

**Files:**
- Modify: `src/views/api/alert_api.py`
- Test: `tests/test_authz.py`

**Step 1: Add admin protection**

Apply `@admin_required` to:
- create rule
- update rule
- delete rule
- toggle rule
- mark all read
- test alert
- evaluate alert

**Step 2: Keep read-only endpoints available to authenticated users**

Do not change:
- rules list
- history
- stats
- unread count
- mark single alert read

**Step 3: Re-run targeted tests**

Run: `pytest tests/test_authz.py -q`

Expected: new alert permission tests pass

### Task 4: Remove dangerous demo-admin defaults

**Files:**
- Modify: `src/config/settings.py`
- Modify: `src/services/startup_service.py`

**Step 1: Change defaults**

Set:
- `AUTO_CREATE_DEMO_ADMIN=False` by default
- `DEMO_ADMIN_RESET_PASSWORD=False` by default

**Step 2: Remove default reset behavior**

Ensure bootstrap only creates missing demo admin when explicitly enabled; never reset existing password by default.

**Step 3: Run focused tests**

Run: `pytest tests/test_startup_service.py tests/test_auth_jwt.py -q`

Expected: startup-related behavior remains green

### Task 5: Migrate frontend away from token persistence

**Files:**
- Modify: `frontend/src/api/request.js`
- Modify: `frontend/src/stores/user.js`
- Modify: `frontend/src/router/index.js`

**Step 1: Remove token persistence**

Change store to:
- stop reading token from `localStorage`
- stop writing/removing token in login/logout flows
- keep in-memory token only if needed for current-session WebSocket use

**Step 2: Enable credentialed requests**

Set axios `withCredentials = true`.

**Step 3: Update route guard**

Replace local token gate with:
- public route bypass
- cached user check
- fallback fetch to `/api/auth/me`
- redirect to login on 401

**Step 4: Verify frontend build**

Run: `pnpm build`

Expected: build succeeds

### Task 6: Update docs to match actual auth model

**Files:**
- Modify: `docs/API.md`
- Modify: `README.md`
- Modify: `docs/DEPLOYMENT.md`
- Modify: `frontend/README.md`

**Step 1: Update API docs**

Document:
- cookie-priority auth
- Bearer compatibility
- alert admin-only endpoints
- session check semantics

**Step 2: Update run/deploy docs**

Remove stale instructions that still point to manual query config or old frontend startup guidance.

**Step 3: Run verification**

Run:
- `pytest tests/test_auth_jwt.py tests/test_authz.py tests/test_startup_service.py -q`
- `pytest -q`
- `pnpm build`

Expected:
- targeted tests pass
- full suite passes
- frontend build succeeds
