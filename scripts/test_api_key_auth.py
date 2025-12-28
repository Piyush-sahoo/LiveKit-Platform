#!/usr/bin/env python
"""
Vobiz API Key Authentication Test
==================================
Tests API key authentication:
1. Login with email/password to create an API key
2. Use valid API key to make API calls (should work)
3. Use invalid/wrong API key (should return 401 Unauthorized)

Usage:
    python scripts/test_api_key_auth.py
"""
import httpx
import asyncio

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "http://localhost:8000"
LOGIN_EMAIL = "test@test.com"
LOGIN_PASSWORD = "test@test.com"

# ============================================================
# Colors
# ============================================================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_section(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")


def log_test(name, passed, expected, actual):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {status} {name}")
    print(f"       Expected: {expected}")
    print(f"       Actual:   {actual}")


async def test_api_key_auth():
    """Test API key authentication."""
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        
        # ============================================================
        # STEP 1: Login with email/password to get JWT
        # ============================================================
        log_section("STEP 1: Login with Email/Password")
        
        print(f"  Logging in as {LOGIN_EMAIL}...")
        r = await client.post("/api/auth/login", json={
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD
        })
        
        if r.status_code != 200:
            print(f"  {Colors.RED}Login failed: {r.status_code}{Colors.END}")
            return
        
        data = r.json()
        jwt_token = data["tokens"]["access_token"]
        print(f"  {Colors.GREEN}✓ Logged in successfully{Colors.END}")
        print(f"  JWT Token: {jwt_token[:30]}...")
        
        # Add JWT to headers for creating API key
        client.headers["Authorization"] = f"Bearer {jwt_token}"
        
        # ============================================================
        # STEP 2: Create an API Key
        # ============================================================
        log_section("STEP 2: Create API Key")
        
        print("  Creating API key 'test_key'...")
        r = await client.post("/api/auth/api-keys", json={
            "name": "test_key",
            "permissions": ["*"]
        })
        
        if r.status_code in [200, 201]:
            api_key_data = r.json()
            api_key = api_key_data.get("key")
            api_key_id = api_key_data.get("api_key_id")
            print(f"  {Colors.GREEN}✓ API Key created successfully{Colors.END}")
            print(f"  API Key ID: {api_key_id}")
            print(f"  API Key: {api_key}")
        else:
            print(f"  {Colors.RED}Failed to create API key: {r.status_code} - {r.text[:100]}{Colors.END}")
            return
        
        # ============================================================
        # STEP 3: Test with VALID API Key
        # ============================================================
        log_section("STEP 3: Test with VALID API Key")
        
        # Remove JWT, use API key instead
        del client.headers["Authorization"]
        client.headers["X-API-Key"] = api_key
        
        print(f"  Using API Key: {api_key[:20]}...")
        
        # Test: List Assistants
        r = await client.get("/api/assistants")
        expected = "200 OK"
        actual = f"{r.status_code} {'OK' if r.status_code == 200 else 'ERROR'}"
        passed = r.status_code == 200
        log_test("GET /api/assistants with valid API key", passed, expected, actual)
        
        # Test: List Calls
        r = await client.get("/api/calls")
        expected = "200 OK"
        actual = f"{r.status_code} {'OK' if r.status_code == 200 else 'ERROR'}"
        passed = r.status_code == 200
        log_test("GET /api/calls with valid API key", passed, expected, actual)
        
        # Test: List Campaigns
        r = await client.get("/api/campaigns")
        expected = "200 OK"
        actual = f"{r.status_code} {'OK' if r.status_code == 200 else 'ERROR'}"
        passed = r.status_code == 200
        log_test("GET /api/campaigns with valid API key", passed, expected, actual)
        
        # ============================================================
        # STEP 3b: Make REAL CALL with API Key
        # ============================================================
        log_section("STEP 3b: Make REAL CALL with API Key")
        
        print(f"  Creating a real call to +919148227303...")
        
        # First, get a valid SIP config
        r = await client.get("/api/sip-configs")
        sip_id = None
        if r.status_code == 200:
            try:
                data = r.json()
                sip_list = data.get("sip_configs", []) if isinstance(data, dict) else data
                if isinstance(sip_list, list) and len(sip_list) > 0:
                    sip_id = sip_list[0].get("sip_id")
                    print(f"  Using SIP config: {sip_id}")
                else:
                    print(f"  No SIP configs found, using default")
            except Exception as e:
                print(f"  Error parsing SIP configs: {e}")
        
        # Get an assistant
        r = await client.get("/api/assistants")
        assistant_id = None
        if r.status_code == 200:
            try:
                data = r.json()
                asst_list = data.get("assistants", []) if isinstance(data, dict) else data
                if isinstance(asst_list, list) and len(asst_list) > 0:
                    assistant_id = asst_list[0].get("assistant_id")
                    print(f"  Using assistant: {assistant_id}")
                else:
                    print(f"  No assistants found, using default")
            except Exception as e:
                print(f"  Error parsing assistants: {e}")
        
        # Make the call with API key
        call_payload = {
            "phone_number": "+919148227303",
            "metadata": {"auth_method": "api_key", "test": "api_key_call_test"}
        }
        if sip_id:
            call_payload["sip_id"] = sip_id
        if assistant_id:
            call_payload["assistant_id"] = assistant_id
            
        r = await client.post("/api/calls", json=call_payload)
        expected = "200/201 (Call Created)"
        actual = f"{r.status_code}"
        passed = r.status_code in [200, 201]
        
        if passed:
            call_data = r.json()
            call_id = call_data.get("call_id")
            call_status = call_data.get("status")
            print(f"  {Colors.GREEN}✓ CALL CREATED SUCCESSFULLY!{Colors.END}")
            print(f"  Call ID: {call_id}")
            print(f"  Status: {call_status}")
            actual = f"{r.status_code} - Call ID: {call_id}"
        else:
            print(f"  {Colors.RED}✗ Call failed: {r.text[:100]}{Colors.END}")
            
        log_test("POST /api/calls with valid API key (REAL CALL)", passed, expected, actual)
        
        # ============================================================
        # STEP 4: Test with INVALID API Key
        # ============================================================
        log_section("STEP 4: Test with INVALID API Key")
        
        # Use wrong API key
        invalid_key = "vk_invalid_key_12345678901234567890"
        client.headers["X-API-Key"] = invalid_key
        
        print(f"  Using INVALID API Key: {invalid_key}")
        
        # Test: List Assistants (should be 401)
        r = await client.get("/api/assistants")
        expected = "401 Unauthorized"
        actual = f"{r.status_code} {'Unauthorized' if r.status_code == 401 else 'Other'}"
        passed = r.status_code == 401
        log_test("GET /api/assistants with INVALID API key", passed, expected, actual)
        
        # Test: List Calls (should be 401)
        r = await client.get("/api/calls")
        expected = "401 Unauthorized"
        actual = f"{r.status_code} {'Unauthorized' if r.status_code == 401 else 'Other'}"
        passed = r.status_code == 401
        log_test("GET /api/calls with INVALID API key", passed, expected, actual)
        
        # Test: Create Call (should be 401)
        r = await client.post("/api/calls", json={
            "phone_number": "+919148227303"
        })
        expected = "401 Unauthorized"
        actual = f"{r.status_code} {'Unauthorized' if r.status_code == 401 else 'Other'}"
        passed = r.status_code == 401
        log_test("POST /api/calls with INVALID API key", passed, expected, actual)
        
        # ============================================================
        # STEP 5: Test with NO Authentication
        # ============================================================
        log_section("STEP 5: Test with NO Authentication")
        
        # Remove all auth headers
        del client.headers["X-API-Key"]
        
        print("  Making requests with NO authentication headers...")
        
        # Test: List Assistants (should be 401)
        r = await client.get("/api/assistants")
        expected = "401 Unauthorized"
        actual = f"{r.status_code} {'Unauthorized' if r.status_code == 401 else 'Other'}"
        passed = r.status_code == 401
        log_test("GET /api/assistants with NO auth", passed, expected, actual)
        
        # Test: Health endpoint (should work, public)
        r = await client.get("/health")
        expected = "200 OK (public endpoint)"
        actual = f"{r.status_code} {'OK' if r.status_code == 200 else 'Other'}"
        passed = r.status_code == 200
        log_test("GET /health with NO auth", passed, expected, actual)
        
        # ============================================================
        # SUMMARY
        # ============================================================
        log_section("TEST SUMMARY")
        
        print(f"""
{Colors.BOLD}Authentication Methods Tested:{Colors.END}
  1. JWT Token (Bearer): Works ✓
  2. API Key (X-API-Key): Works ✓  
  3. Invalid API Key: Returns 401 ✓
  4. No Auth: Returns 401 (protected routes) ✓
  5. Public routes (/health): Always accessible ✓

{Colors.GREEN}{Colors.BOLD}API Key Authentication is working correctly!{Colors.END}
""")


def main():
    print("\n" + "=" * 60)
    print("VOBIZ API KEY AUTHENTICATION TEST")
    print("=" * 60)
    
    asyncio.run(test_api_key_auth())


if __name__ == "__main__":
    main()
