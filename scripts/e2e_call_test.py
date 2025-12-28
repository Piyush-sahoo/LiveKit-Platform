#!/usr/bin/env python
"""
Vobiz Complete E2E Test Script
==============================
Runs through the entire call workflow automatically:
1. Create Assistant
2. Create SIP Configuration  
3. Create Phone Number
4. Create Campaign
5. Make a Call
6. Get Call Details & Analytics

Usage:
    python scripts/e2e_call_test.py
"""
import httpx
import asyncio
import time
import json

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "http://localhost:8000"

# SIP Credentials
SIP_DOMAIN = "008654e7.sip.vobiz.ai"
SIP_USERNAME = "piyush123"
SIP_PASSWORD = "Password@123"
FROM_NUMBER = "+912271264303"

# Target phone number to call
TARGET_PHONE = "+919148227303"

# ============================================================
# API HELPERS
# ============================================================

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_step(step_num, total, message):
    print(f"\n{Colors.BLUE}[{step_num}/{total}]{Colors.END} {Colors.BOLD}{message}{Colors.END}")


def log_success(message):
    print(f"   {Colors.GREEN}✓{Colors.END} {message}")


def log_error(message):
    print(f"   {Colors.RED}✗{Colors.END} {message}")


def log_info(message):
    print(f"   → {message}")


async def run_e2e_test():
    """Run the complete end-to-end test."""
    
    total_steps = 8
    results = {}
    
    # Login credentials
    LOGIN_EMAIL = "test@test.com"
    LOGIN_PASSWORD = "test@test.com"
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}VOBIZ E2E CALL TEST{Colors.END}")
        print("=" * 60)
        print(f"Target: {TARGET_PHONE}")
        print(f"From: {FROM_NUMBER}")
        print(f"SIP Domain: {SIP_DOMAIN}")
        print("=" * 60)
        
        # ---------------------------------------------------------
        # STEP 0: Login
        # ---------------------------------------------------------
        log_step(0, total_steps, "Logging in...")
        
        try:
            response = await client.post("/api/auth/login", json={
                "email": LOGIN_EMAIL,
                "password": LOGIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                # Token is nested under 'tokens' object
                tokens_data = data.get("tokens", {})
                token = tokens_data.get("access_token") or data.get("access_token")
                if token:
                    # Add auth header to all future requests
                    client.headers["Authorization"] = f"Bearer {token}"
                    log_success(f"Logged in as {LOGIN_EMAIL}")
                else:
                    log_error(f"No token in response: {list(data.keys())}")
                    return
            else:
                log_error(f"Login failed: {response.status_code} - {response.text[:100]}")
                return
        except Exception as e:
            log_error(f"Login error: {e}")
            return
        
        # ---------------------------------------------------------
        # STEP 1: Create Assistant
        # ---------------------------------------------------------
        log_step(1, total_steps, "Creating AI Assistant")
        
        try:
            response = await client.post("/api/assistants", json={
                "name": "Vobiz Sales Agent",
                "instructions": """You are a professional AI sales assistant from Vobiz.
                
When the call is answered:
1. Greet them warmly and introduce yourself
2. Mention this is a test call from Vobiz AI platform
3. Ask how you can help them today
4. Be conversational and helpful
5. End the call politely when they want to finish

Keep responses concise and natural.""",
                "first_message": "Hi there! This is Alex calling from Vobiz. I hope I'm not catching you at a bad time. This is a quick test call from our AI platform. How are you doing today?",
                "voice": {
                    "provider": "openai",
                    "voice_id": "alloy"
                },
                "temperature": 0.8
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                results['assistant_id'] = data['assistant_id']
                log_success(f"Created assistant: {results['assistant_id']}")
            elif response.status_code == 400 and "already exists" in response.text.lower():
                # Get existing
                list_resp = await client.get("/api/assistants")
                assistants = list_resp.json()
                if assistants:
                    results['assistant_id'] = assistants[0]['assistant_id']
                    log_info(f"Using existing assistant: {results['assistant_id']}")
                else:
                    log_error("No assistants found")
                    return
            else:
                log_error(f"Failed: {response.status_code} - {response.text[:100]}")
                return
        except Exception as e:
            log_error(f"Error: {e}")
            return
        
        # ---------------------------------------------------------
        # STEP 2: Create SIP Configuration
        # ---------------------------------------------------------
        log_step(2, total_steps, "Creating SIP Configuration")
        
        try:
            response = await client.post("/api/sip-configs", json={
                "name": "Vobiz Outbound Trunk",
                "sip_domain": SIP_DOMAIN,
                "sip_username": SIP_USERNAME,
                "sip_password": SIP_PASSWORD,
                "from_number": FROM_NUMBER,
                "is_default": True
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                results['sip_id'] = data['sip_id']
                results['trunk_id'] = data.get('trunk_id', 'N/A')
                log_success(f"Created SIP config: {results['sip_id']}")
                log_info(f"LiveKit trunk: {results['trunk_id']}")
            else:
                # Try to get existing
                list_resp = await client.get("/api/sip-configs")
                if list_resp.status_code == 200:
                    configs = list_resp.json()
                    if configs:
                        results['sip_id'] = configs[0]['sip_id']
                        results['trunk_id'] = configs[0].get('trunk_id', 'N/A')
                        log_info(f"Using existing SIP config: {results['sip_id']}")
                    else:
                        log_error("No SIP configs found")
                        return
                else:
                    log_error(f"Failed: {response.status_code}")
                    return
        except Exception as e:
            log_error(f"Error: {e}")
            return
        
        # ---------------------------------------------------------
        # STEP 3: Create Phone Number
        # ---------------------------------------------------------
        log_step(3, total_steps, "Creating Phone Number")
        
        try:
            response = await client.post("/api/phone-numbers", json={
                "number": FROM_NUMBER,
                "label": "Vobiz Outbound Line",
                "provider": "vobiz"
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                results['phone_id'] = data['phone_id']
                log_success(f"Created phone number: {results['phone_id']}")
            else:
                # Get existing
                list_resp = await client.get("/api/phone-numbers")
                if list_resp.status_code == 200:
                    phones = list_resp.json()
                    if phones:
                        results['phone_id'] = phones[0]['phone_id']
                        log_info(f"Using existing phone: {results['phone_id']}")
                    else:
                        results['phone_id'] = None
                        log_info("No phone numbers, continuing without...")
                else:
                    results['phone_id'] = None
                    log_info("Skipping phone number step")
        except Exception as e:
            log_error(f"Error: {e}")
            results['phone_id'] = None
        
        # ---------------------------------------------------------
        # STEP 4: Create Campaign (optional)
        # ---------------------------------------------------------
        log_step(4, total_steps, "Creating Campaign")
        
        try:
            response = await client.post("/api/campaigns", json={
                "name": "E2E Test Campaign",
                "description": "Automated test campaign",
                "assistant_id": results['assistant_id'],
                "sip_id": results['sip_id'],
                "contacts": [
                    {
                        "phone_number": TARGET_PHONE,
                        "name": "Test Contact",
                        "variables": {"campaign": "e2e_test"}
                    }
                ],
                "max_concurrent_calls": 1
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                results['campaign_id'] = data['campaign_id']
                log_success(f"Created campaign: {results['campaign_id']}")
            else:
                log_info(f"Campaign creation skipped: {response.status_code}")
                results['campaign_id'] = None
        except Exception as e:
            log_info(f"Campaign skipped: {e}")
            results['campaign_id'] = None
        
        # ---------------------------------------------------------
        # STEP 5: Make the Call
        # ---------------------------------------------------------
        log_step(5, total_steps, f"Making Call to {TARGET_PHONE}")
        
        try:
            response = await client.post("/api/calls", json={
                "phone_number": TARGET_PHONE,
                "assistant_id": results['assistant_id'],
                "sip_id": results['sip_id'],
                "metadata": {
                    "test": "e2e",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                results['call_id'] = data['call_id']
                results['call_status'] = data.get('status', 'queued')
                log_success(f"Call initiated: {results['call_id']}")
                log_info(f"Status: {results['call_status']}")
            else:
                log_error(f"Call failed: {response.status_code} - {response.text[:200]}")
                return
        except Exception as e:
            log_error(f"Call error: {e}")
            return
        
        # ---------------------------------------------------------
        # STEP 6: Wait and Get Call Details
        # ---------------------------------------------------------
        log_step(6, total_steps, "Waiting for Call Details")
        
        print("   Waiting 10 seconds for call to connect...")
        await asyncio.sleep(10)
        
        try:
            response = await client.get(f"/api/calls/{results['call_id']}")
            
            if response.status_code == 200:
                data = response.json()
                results['call_details'] = data
                log_success("Call details retrieved")
                log_info(f"Status: {data.get('status', 'unknown')}")
                log_info(f"Duration: {data.get('duration_seconds', 0)}s")
                if data.get('recording_url'):
                    log_info(f"Recording: {data['recording_url'][:50]}...")
            else:
                log_error(f"Failed to get details: {response.status_code}")
        except Exception as e:
            log_error(f"Error: {e}")
        
        # ---------------------------------------------------------
        # STEP 7: Get Analytics
        # ---------------------------------------------------------
        log_step(7, total_steps, "Fetching Call Analytics")
        
        try:
            response = await client.get("/api/calls")
            
            if response.status_code == 200:
                calls = response.json()
                log_success(f"Total calls in system: {len(calls)}")
                
                # Show recent calls
                for call in calls[:3]:
                    log_info(f"{call.get('call_id', 'N/A')[:20]}... | {call.get('status', 'unknown')} | {call.get('phone_number', 'N/A')}")
            else:
                log_error(f"Failed: {response.status_code}")
        except Exception as e:
            log_error(f"Error: {e}")
        
        # ---------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------
        print("\n" + "=" * 60)
        print(f"{Colors.GREEN}{Colors.BOLD}E2E TEST COMPLETE{Colors.END}")
        print("=" * 60)
        print(f"Assistant ID:  {results.get('assistant_id', 'N/A')}")
        print(f"SIP Config ID: {results.get('sip_id', 'N/A')}")
        print(f"Trunk ID:      {results.get('trunk_id', 'N/A')}")
        print(f"Phone ID:      {results.get('phone_id', 'N/A')}")
        print(f"Campaign ID:   {results.get('campaign_id', 'N/A')}")
        print(f"Call ID:       {results.get('call_id', 'N/A')}")
        print(f"Call Status:   {results.get('call_status', 'N/A')}")
        print("=" * 60)
        
        # Save results to file
        with open("e2e_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: e2e_test_results.json")
        
        return results


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("VOBIZ END-TO-END CALL TEST")
    print("=" * 60)
    print(f"\nThis script will:")
    print(f"  1. Create an AI Assistant")
    print(f"  2. Create SIP Configuration ({SIP_DOMAIN})")
    print(f"  3. Create Phone Number ({FROM_NUMBER})")
    print(f"  4. Create a Campaign")
    print(f"  5. Make a call to {TARGET_PHONE}")
    print(f"  6. Get call details")
    print(f"  7. Fetch analytics")
    print("\n" + "=" * 60)
    
    asyncio.run(run_e2e_test())


if __name__ == "__main__":
    main()
