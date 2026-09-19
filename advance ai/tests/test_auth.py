import asyncio
import os
import sys
import httpx
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from memory.store import MemoryStore
from server.app import app

async def run_auth_tests():
    print("==================================================")
    print(">>> Testing Nexus-AI Email Authentication Gate <<<")
    print("==================================================")

    store = MemoryStore()

    # 1. Test Registration
    test_email = f"user_{os.urandom(4).hex()}@nexus.ai"
    test_pwd = "StrongPassword123!"

    print("\n[1/7] Testing User Registration...")
    reg_result = store.register_user(test_email, test_pwd)
    assert "token" in reg_result, "Token missing in registration result"
    assert reg_result["user"]["email"] == test_email
    token1 = reg_result["token"]
    user1_id = reg_result["user"]["id"]
    print(f"    [PASS] User registered successfully with ID: {user1_id}")

    # 2. Test Duplicate Email Prevention
    print("\n[2/7] Testing Duplicate Email Prevention...")
    try:
        store.register_user(test_email, "anotherpassword")
        assert False, "Duplicate email registration did not raise error"
    except ValueError as e:
        assert "already exists" in str(e).lower()
        print("    [PASS] Correctly rejected duplicate email registration.")

    # 3. Test Invalid Login
    print("\n[3/7] Testing Invalid Password Handling...")
    bad_login = store.authenticate_user(test_email, "WrongPassword!")
    assert bad_login is None, "Expected None for wrong password"
    print("    [PASS] Invalid password correctly rejected.")

    # 4. Test Valid Login
    print("\n[4/7] Testing Valid Login...")
    login_result = store.authenticate_user(test_email, test_pwd)
    assert login_result is not None
    assert login_result["user"]["email"] == test_email
    token2 = login_result["token"]
    print(f"    [PASS] Authentication succeeded, issued token: {token2[:10]}...")

    # 5. Test Token Lookup
    print("\n[5/7] Testing Token Resolution...")
    user_info = store.get_user_by_token(token2)
    assert user_info is not None
    assert user_info["email"] == test_email
    print("    [PASS] User profile retrieved from token.")

    # 6. Test Multi-User Session Isolation
    print("\n[6/7] Testing Multi-User Session Isolation...")
    user2_email = f"user2_{os.urandom(4).hex()}@nexus.ai"
    reg2 = store.register_user(user2_email, "Password456!")
    user2_id = reg2["user"]["id"]

    # User 1 creates session
    s1_id = store.create_session("User 1 Secret Project", user_id=user1_id)
    # User 2 creates session
    s2_id = store.create_session("User 2 Personal Research", user_id=user2_id)

    u1_sessions = store.list_sessions(user_id=user1_id)
    u2_sessions = store.list_sessions(user_id=user2_id)

    u1_ids = [s["id"] for s in u1_sessions]
    u2_ids = [s["id"] for s in u2_sessions]

    assert s1_id in u1_ids and s2_id not in u1_ids, "User 1 can see User 2's session!"
    assert s2_id in u2_ids and s1_id not in u2_ids, "User 2 can see User 1's session!"
    print("    [PASS] Sessions are strictly isolated between accounts.")

    # 7. Test FastAPI Route Protection (401 Unauthorized vs 200 OK)
    print("\n[7/7] Testing FastAPI HTTP Route Guards...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Request /api/sessions without token -> 401
        res_unauth = await client.get("/api/sessions")
        assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
        print("    [PASS] Unauthenticated request to /api/sessions returned 401 Unauthorized.")

        # Request /api/sessions with token -> 200
        res_auth = await client.get("/api/sessions", headers={"Authorization": f"Bearer {token2}"})
        assert res_auth.status_code == 200, f"Expected 200, got {res_auth.status_code}"
        assert len(res_auth.json()["sessions"]) > 0
        print("    [PASS] Authenticated request with Bearer token returned 200 OK.")

        # Request /api/auth/me
        res_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert res_me.status_code == 200
        assert res_me.json()["user"]["email"] == test_email
        print(f"    [PASS] /api/auth/me correctly returned email: {test_email}")

        # Logout
        res_logout = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token2}"})
        assert res_logout.status_code == 200
        # Check token is invalidated
        res_after = await client.get("/api/sessions", headers={"Authorization": f"Bearer {token2}"})
        assert res_after.status_code == 401
        print("    [PASS] Token invalidated upon logout.")

    print("\n==================================================")
    print(">>> ALL 7 AUTHENTICATION TESTS PASSED! <<<")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_auth_tests())
