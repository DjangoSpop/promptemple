"""
Comprehensive endpoint test - all AI services + key app endpoints
Tests with funded DeepSeek API key
"""
import requests
import json
import time
import sys

BASE = "http://127.0.0.1:8000"

# 1) Login
print("=" * 70)
print("AUTHENTICATION")
print("=" * 70)
r = requests.post(f"{BASE}/api/v2/auth/login/", json={"username": "testbot", "password": "testpass123"})
if r.status_code != 200:
    print(f"  FAIL login: {r.status_code} - {r.text[:200]}")
    sys.exit(1)
data = r.json()
tok = data.get("access") or data.get("token") or data.get("tokens", {}).get("access", "")
if not tok:
    print(f"  FAIL: no token in response keys={list(data.keys())}")
    sys.exit(1)
print(f"  OK  login -> got JWT token")
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

results = {"ok": [], "fail": [], "skip": []}

def test(method, path, payload=None, stream=False, expect=200, label=None, allow_any=False):
    name = label or f"{method.upper()} {path}"
    url = f"{BASE}{path}"
    headers = {} if allow_any else H
    try:
        if method == "get":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "post":
            r = requests.post(url, headers=headers, json=payload or {}, stream=stream, timeout=30)
        elif method == "delete":
            r = requests.delete(url, headers=headers, timeout=15)
        
        ok = r.status_code == expect or (isinstance(expect, list) and r.status_code in expect)
        
        # For stream, read body  
        if stream:
            body = ""
            for chunk in r.iter_content(chunk_size=512, decode_unicode=True):
                body += chunk
                if len(body) > 2000:
                    break
        else:
            body = r.text[:300]
        
        status = "OK" if ok else "FAIL"
        icon = "  OK " if ok else " FAIL"
        print(f"{icon} {name} -> {r.status_code} | {body[:120]}")
        
        if ok:
            results["ok"].append(name)
        else:
            results["fail"].append((name, r.status_code, body[:200]))
        return r
    except Exception as e:
        print(f" FAIL {name} -> EXCEPTION: {e}")
        results["fail"].append((name, "ERR", str(e)[:200]))
        return None

print()
print("=" * 70)
print("AI SERVICES - GET ENDPOINTS")
print("=" * 70)
test("get", "/api/v2/ai/providers/", label="providers")
test("get", "/api/v2/ai/models/", label="models")
test("get", "/api/v2/ai/usage/", label="usage")
test("get", "/api/v2/ai/quotas/", label="quotas")
test("get", "/api/v2/ai/suggestions/", label="suggestions")
test("get", "/api/v2/ai/deepseek/test/", label="deepseek-test")
test("get", "/api/v2/ai/assistant/", label="assistant-list")
test("get", "/api/v2/ai/assistant/threads/", label="assistant-threads")
test("get", "/api/v2/ai/agent/stats/", label="agent-stats", expect=[200, 403])

print()
print("=" * 70)
print("AI SERVICES - POST ENDPOINTS (DeepSeek AI calls)")
print("=" * 70)
test("post", "/api/v2/ai/generate/", {"prompt": "Say hello in one word", "model": "deepseek-chat"}, label="generate")
test("post", "/api/v2/ai/deepseek/chat/", {"messages": [{"role": "user", "content": "Say hi in 5 words"}], "model": "deepseek-chat"}, label="deepseek-chat")
test("post", "/api/v2/ai/deepseek/stream/", {"messages": [{"role": "user", "content": "Count 1 to 3"}]}, stream=True, label="deepseek-stream")
test("post", "/api/v2/ai/agent/optimize/", {"session_id": "test-session-1", "original": "write me an email"}, label="agent-optimize")
test("post", "/api/v2/ai/rag/retrieve/", {"query": "email writing tips"}, label="rag-retrieve")
test("post", "/api/v2/ai/rag/answer/", {"query": "How to write better prompts?"}, label="rag-answer")

# AskMe endpoints (AllowAny)
print()
print("=" * 70)
print("ASKME ENDPOINTS")
print("=" * 70)
askme_r = test("post", "/api/v2/ai/askme/start/", {"intent": "Write a marketing email", "domain": "marketing"}, label="askme-start", allow_any=True)
if askme_r and askme_r.status_code == 200:
    askme_data = askme_r.json()
    session_id = askme_data.get("session_id", "")
    questions = askme_data.get("questions", [])
    if questions:
        q_id = questions[0].get("qid", "")
        test("post", "/api/v2/ai/askme/answer/", {"session_id": session_id, "qid": q_id, "value": "B2B SaaS audience"}, label="askme-answer", allow_any=True)
    test("post", "/api/v2/ai/askme/finalize/", {"session_id": session_id}, label="askme-finalize", allow_any=True)
    test("get", "/api/v2/ai/askme/sessions/", label="askme-sessions", allow_any=True)
    test("get", f"/api/v2/ai/askme/sessions/{session_id}/", label="askme-session-detail", allow_any=True)

# Assistant run
print()
print("=" * 70)
print("ASSISTANT RUN")
print("=" * 70)
test("post", "/api/v2/ai/assistant/run/", {"assistant_type": "writing", "message": "Help me write a tagline"}, label="assistant-run")

print()
print("=" * 70)
print("CHAT ENDPOINTS")
print("=" * 70)
test("get", "/api/v2/chat/health/", label="chat-health")
test("get", "/api/v2/chat/auth-test/", label="chat-auth-test")
test("post", "/api/v2/chat/completions/basic/", {"messages": [{"role": "user", "content": "Say one word"}], "model": "deepseek-chat"}, stream=True, label="chat-completions-basic")
test("post", "/api/v2/chat/completions/", {"messages": [{"role": "user", "content": "Say hi briefly"}], "model": "deepseek-chat"}, stream=True, label="chat-completions-enhanced")
test("get", "/api/v2/chat/templates/status/", label="chat-template-status")
test("get", "/api/v2/chat/templates/extracted/", label="chat-extracted-templates")
test("get", "/api/v2/chat/sessions/", label="chat-sessions")

print()
print("=" * 70)
print("TEMPLATES & SEARCH")
print("=" * 70)
test("get", "/api/v2/templates/", label="templates-list")
test("get", "/api/v2/template-categories/", label="template-categories")
test("get", "/api/v2/status/", label="system-status")
test("post", "/api/v2/search/prompts/", {"query": "email"}, label="search-prompts")
test("get", "/api/v2/prompts/featured/", label="featured-prompts")
test("get", "/api/v2/health/websocket/", label="websocket-health")

print()
print("=" * 70)
print("GAMIFICATION")
print("=" * 70)
test("get", "/api/v2/gamification/achievements/", label="achievements")
test("get", "/api/v2/gamification/badges/", label="badges")
test("get", "/api/v2/gamification/leaderboard/", label="leaderboard")
test("get", "/api/v2/gamification/daily-challenges/", label="daily-challenges")
test("get", "/api/v2/gamification/user-level/", label="user-level")
test("get", "/api/v2/gamification/streak/", label="streak")

print()
print("=" * 70)
print("ANALYTICS")
print("=" * 70)
test("get", "/api/v2/analytics/dashboard/", label="analytics-dashboard")
test("get", "/api/v2/analytics/user-insights/", label="user-insights")
test("post", "/api/v2/analytics/track/", {"event": "test_event", "data": {}}, label="analytics-track", expect=[200, 201])

print()
print("=" * 70)
print("BILLING (stubs)")
print("=" * 70)
test("get", "/api/v2/billing/plans/", label="billing-plans")
test("get", "/api/v2/billing/me/subscription/", label="billing-subscription")
test("get", "/api/v2/billing/me/entitlements/", label="billing-entitlements")
test("get", "/api/v2/billing/me/usage/", label="billing-usage")

print()
print("=" * 70)
print("ORCHESTRATOR (stubs)")
print("=" * 70)
test("post", "/api/v2/orchestrator/intent/", {"text": "help me write an email"}, label="orchestrator-intent")
test("post", "/api/v2/orchestrator/assess/", {"prompt": "write an email"}, label="orchestrator-assess")

print()
print("=" * 70)
print("PROMPT HISTORY")
print("=" * 70)
test("get", "/api/v2/history/history/", label="prompt-history")
test("get", "/api/v2/history/saved-prompts/", label="saved-prompts")
test("get", "/api/v2/history/iterations/", label="iterations")
test("get", "/api/v2/history/threads/", label="threads")

print()
print("=" * 70)
print("CORE ENDPOINTS")
print("=" * 70)
test("get", "/health/", label="health", allow_any=True)
test("get", "/api/", label="api-root", allow_any=True)

# SUMMARY
print()
print("=" * 70)
print(f"RESULTS: {len(results['ok'])} OK / {len(results['fail'])} FAIL / {len(results['skip'])} SKIP")
print("=" * 70)
if results["fail"]:
    print("\nFAILED ENDPOINTS:")
    for name, code, body in results["fail"]:
        print(f"  - {name}: {code} | {body[:100]}")
print()
print(f"Total endpoints tested: {len(results['ok']) + len(results['fail'])}")
