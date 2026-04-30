# Spider Service Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Protect the standalone Spider API service with optional Bearer Token authentication.

**Architecture:** Add a Flask `before_request` hook in `spider_service/app/main.py`. The hook reads `SPIDER_SERVICE_TOKEN`, skips auth for `/health`, and requires `Authorization: Bearer <token>` for all other routes only when the token is configured.

**Tech Stack:** Flask, pytest, monkeypatch.

---

### Task 1: Add Spider Service Auth Tests

**Files:**
- Create: `tests/test_spider_service_auth.py`
- Modify: none

**Step 1: Write the failing test**

Add tests that import `spider_service.app.main`, patch task `delay()` methods, and assert:

- no configured token allows `POST /api/spider/tasks`;
- configured token rejects missing auth;
- configured token rejects a wrong token;
- configured token allows the correct token.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_spider_service_auth.py -q`

Expected: at least one auth test fails because the Spider service does not yet enforce `SPIDER_SERVICE_TOKEN`.

### Task 2: Implement Auth Hook

**Files:**
- Modify: `spider_service/app/main.py`
- Test: `tests/test_spider_service_auth.py`

**Step 1: Write minimal implementation**

Add `os` import, `_unauthorized_if_needed()`, and `@app.before_request`.

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_spider_service_auth.py -q`

Expected: all tests pass.

### Task 3: Regression Check

**Files:**
- Test: `tests/test_spider_task_service.py`

**Step 1: Run related existing tests**

Run: `pytest tests/test_spider_task_service.py tests/test_task_status_service.py -q`

Expected: all tests pass.
