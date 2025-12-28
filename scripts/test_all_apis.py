#!/usr/bin/env python
"""
Vobiz API Test Suite
====================
Tests all API endpoints matching the Postman collection.
Uses JWT authentication (login with email/password).

Usage:
    python scripts/test_all_apis.py
"""
import httpx
import asyncio
import json
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "http://localhost:8000"
LOGIN_EMAIL = "test@test.com"
LOGIN_PASSWORD = "test@test.com"

# Test data storage
test_data = {}

# ============================================================
# Colors for output
# ============================================================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"  [{status}] {name}")
    if details and not passed:
        print(f"       {Colors.YELLOW}→ {details}{Colors.END}")


def log_section(name: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{name}{Colors.END}")
    print(f"{Colors.CYAN}{'='*50}{Colors.END}")


async def test_all_apis():
    """Test all APIs."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        
        # ============================================================
        # HEALTH CHECK
        # ============================================================
        log_section("1. HEALTH CHECK")
        
        try:
            r = await client.get("/health")
            passed = r.status_code == 200
            log_test("GET /health", passed, f"{r.status_code}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /health", False, str(e))
            results["failed"] += 1
        
        # ============================================================
        # AUTHENTICATION
        # ============================================================
        log_section("2. AUTHENTICATION")
        
        # Login
        try:
            r = await client.post("/api/auth/login", json={
                "email": LOGIN_EMAIL,
                "password": LOGIN_PASSWORD
            })
            passed = r.status_code == 200 and "tokens" in r.json()
            log_test("POST /api/auth/login", passed, f"{r.status_code}")
            
            if passed:
                data = r.json()
                token = data["tokens"]["access_token"]
                client.headers["Authorization"] = f"Bearer {token}"
                test_data["token"] = token
                test_data["user_id"] = data["user"]["user_id"]
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/auth/login", False, str(e))
            results["failed"] += 1
            return results  # Can't continue without auth
        
        # Get current user
        try:
            r = await client.get("/api/auth/me")
            passed = r.status_code == 200
            log_test("GET /api/auth/me", passed, f"{r.status_code}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/auth/me", False, str(e))
            results["failed"] += 1
        
        # ============================================================
        # ASSISTANTS
        # ============================================================
        log_section("3. ASSISTANTS")
        
        # Create Assistant
        try:
            r = await client.post("/api/assistants", json={
                "name": "Test Assistant",
                "instructions": "You are a test assistant.",
                "first_message": "Hello, I am a test assistant.",
                "voice": {"provider": "openai", "voice_id": "alloy"}
            })
            passed = r.status_code in [200, 201]
            log_test("POST /api/assistants (create)", passed, f"{r.status_code}")
            if passed:
                test_data["assistant_id"] = r.json().get("assistant_id")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/assistants", False, str(e))
            results["failed"] += 1
        
        # List Assistants
        try:
            r = await client.get("/api/assistants")
            passed = r.status_code == 200 and isinstance(r.json(), list)
            log_test("GET /api/assistants (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/assistants", False, str(e))
            results["failed"] += 1
        
        # Get Assistant
        if test_data.get("assistant_id"):
            try:
                r = await client.get(f"/api/assistants/{test_data['assistant_id']}")
                passed = r.status_code == 200
                log_test("GET /api/assistants/{id} (get)", passed, f"{r.status_code}")
                results["passed" if passed else "failed"] += 1
            except Exception as e:
                log_test("GET /api/assistants/{id}", False, str(e))
                results["failed"] += 1
            
            # Update Assistant
            try:
                r = await client.patch(f"/api/assistants/{test_data['assistant_id']}", json={
                    "name": "Updated Test Assistant"
                })
                passed = r.status_code == 200
                log_test("PATCH /api/assistants/{id} (update)", passed, f"{r.status_code}")
                results["passed" if passed else "failed"] += 1
            except Exception as e:
                log_test("PATCH /api/assistants/{id}", False, str(e))
                results["failed"] += 1
        
        # ============================================================
        # PHONE NUMBERS
        # ============================================================
        log_section("4. PHONE NUMBERS")
        
        # Add Phone Number
        try:
            r = await client.post("/api/phone-numbers", json={
                "number": "+919999888877",
                "label": "Test Number",
                "provider": "vobiz"
            })
            passed = r.status_code in [200, 201]
            log_test("POST /api/phone-numbers (create)", passed, f"{r.status_code}")
            if passed:
                test_data["phone_id"] = r.json().get("phone_id")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/phone-numbers", False, str(e))
            results["failed"] += 1
        
        # List Phone Numbers
        try:
            r = await client.get("/api/phone-numbers")
            passed = r.status_code == 200
            log_test("GET /api/phone-numbers (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/phone-numbers", False, str(e))
            results["failed"] += 1
        
        # Get Phone Number
        if test_data.get("phone_id"):
            try:
                r = await client.get(f"/api/phone-numbers/{test_data['phone_id']}")
                passed = r.status_code == 200
                log_test("GET /api/phone-numbers/{id} (get)", passed, f"{r.status_code}")
                results["passed" if passed else "failed"] += 1
            except Exception as e:
                log_test("GET /api/phone-numbers/{id}", False, str(e))
                results["failed"] += 1
        
        # ============================================================
        # SIP CONFIGS
        # ============================================================
        log_section("5. SIP CONFIGS")
        
        # Create SIP Config
        try:
            r = await client.post("/api/sip-configs", json={
                "name": "Test SIP Config",
                "sip_domain": "test.sip.domain.com",
                "sip_username": "testuser",
                "sip_password": "testpass",
                "from_number": "+919999888877",
                "is_default": False
            })
            passed = r.status_code in [200, 201]
            log_test("POST /api/sip-configs (create)", passed, f"{r.status_code}")
            if passed:
                test_data["sip_id"] = r.json().get("sip_id")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/sip-configs", False, str(e))
            results["failed"] += 1
        
        # List SIP Configs
        try:
            r = await client.get("/api/sip-configs")
            passed = r.status_code == 200
            log_test("GET /api/sip-configs (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/sip-configs", False, str(e))
            results["failed"] += 1
        
        # Get SIP Config
        if test_data.get("sip_id"):
            try:
                r = await client.get(f"/api/sip-configs/{test_data['sip_id']}")
                passed = r.status_code == 200
                log_test("GET /api/sip-configs/{id} (get)", passed, f"{r.status_code}")
                results["passed" if passed else "failed"] += 1
            except Exception as e:
                log_test("GET /api/sip-configs/{id}", False, str(e))
                results["failed"] += 1
        
        # ============================================================
        # CAMPAIGNS
        # ============================================================
        log_section("6. CAMPAIGNS")
        
        # Create Campaign
        try:
            r = await client.post("/api/campaigns", json={
                "name": "Test Campaign",
                "description": "API test campaign",
                "assistant_id": test_data.get("assistant_id", "asst_test"),
                "sip_id": test_data.get("sip_id", "sip_test"),
                "contacts": [
                    {"phone_number": "+919999888877", "name": "Test Contact"}
                ],
                "max_concurrent_calls": 1
            })
            passed = r.status_code in [200, 201]
            log_test("POST /api/campaigns (create)", passed, f"{r.status_code}")
            if passed:
                test_data["campaign_id"] = r.json().get("campaign_id")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/campaigns", False, str(e))
            results["failed"] += 1
        
        # List Campaigns
        try:
            r = await client.get("/api/campaigns")
            passed = r.status_code == 200
            log_test("GET /api/campaigns (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/campaigns", False, str(e))
            results["failed"] += 1
        
        # Get Campaign
        if test_data.get("campaign_id"):
            try:
                r = await client.get(f"/api/campaigns/{test_data['campaign_id']}")
                passed = r.status_code == 200
                log_test("GET /api/campaigns/{id} (get)", passed, f"{r.status_code}")
                results["passed" if passed else "failed"] += 1
            except Exception as e:
                log_test("GET /api/campaigns/{id}", False, str(e))
                results["failed"] += 1
        
        # ============================================================
        # TOOLS
        # ============================================================
        log_section("7. TOOLS")
        
        # Create Tool
        try:
            r = await client.post("/api/tools", json={
                "name": "test_tool",
                "description": "A test tool for API testing",
                "type": "webhook",
                "webhook_url": "https://example.com/test",
                "http_method": "POST",
                "parameters": [
                    {"name": "param1", "type": "string", "description": "Test param", "required": True}
                ]
            })
            passed = r.status_code in [200, 201]
            log_test("POST /api/tools (create)", passed, f"{r.status_code}")
            if passed:
                test_data["tool_id"] = r.json().get("tool_id")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("POST /api/tools", False, str(e))
            results["failed"] += 1
        
        # List Tools
        try:
            r = await client.get("/api/tools")
            passed = r.status_code == 200
            log_test("GET /api/tools (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/tools", False, str(e))
            results["failed"] += 1
        
        # ============================================================
        # CALLS
        # ============================================================
        log_section("8. CALLS")
        
        # List Calls (don't create a real call in test)
        try:
            r = await client.get("/api/calls")
            passed = r.status_code == 200
            log_test("GET /api/calls (list)", passed, f"{r.status_code}, count={len(r.json()) if passed else 0}")
            results["passed" if passed else "failed"] += 1
        except Exception as e:
            log_test("GET /api/calls", False, str(e))
            results["failed"] += 1
        
        # ============================================================
        # SUMMARY
        # ============================================================
        log_section("TEST SUMMARY")
        
        total = results["passed"] + results["failed"]
        print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
        print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
        
        if results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}⚠ Some tests failed - check details above{Colors.END}")
        
        # Print test data created
        print(f"\n{Colors.CYAN}Test Data Created:{Colors.END}")
        for key, value in test_data.items():
            if key != "token":
                print(f"  • {key}: {value}")
        
        return results


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("VOBIZ API TEST SUITE")
    print("Testing all endpoints with JWT Authentication")
    print("=" * 60)
    
    results = asyncio.run(test_all_apis())


if __name__ == "__main__":
    main()
