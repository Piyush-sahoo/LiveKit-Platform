#!/usr/bin/env python
"""
Vobiz Comprehensive API Automation Test
=========================================
Tests ALL APIs with real data using API Key authentication:
1. Create multiple agents with different names (Pooja, Riya, Ananya, Rakhi)
2. Create phone numbers and SIP configs
3. Make real calls
4. Verify data in database via API
5. Delete agents
6. Verify deletion

Usage:
    python scripts/full_api_automation.py
"""
import httpx
import asyncio
import json
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "http://localhost:8000"
LOGIN_EMAIL = "test@test.com"
LOGIN_PASSWORD = "test@test.com"

# Test agent names
AGENT_NAMES = ["Pooja", "Riya", "Ananya", "Rakhi", "Priya"]

# Target phone for calls
TARGET_PHONE = "+919148227303"

# ============================================================
# Colors
# ============================================================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_section(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}")


def log_step(num, total, msg):
    print(f"\n{Colors.BLUE}[{num}/{total}]{Colors.END} {Colors.BOLD}{msg}{Colors.END}")


def log_success(msg):
    print(f"    {Colors.GREEN}✓{Colors.END} {msg}")


def log_error(msg):
    print(f"    {Colors.RED}✗{Colors.END} {msg}")


def log_info(msg):
    print(f"    → {msg}")


async def run_full_automation():
    """Run full API automation with API key authentication."""
    
    created_agents = []
    created_phones = []
    created_sips = []
    created_calls = []
    
    total_steps = 10
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}VOBIZ COMPREHENSIVE API AUTOMATION TEST{Colors.END}")
        print(f"Testing with API Key Authentication")
        print(f"Target Phone: {TARGET_PHONE}")
        print(f"Agent Names: {', '.join(AGENT_NAMES)}")
        print("=" * 70)
        
        # ============================================================
        # STEP 1: Login and Create API Key
        # ============================================================
        log_step(1, total_steps, "Login and Create API Key")
        
        # Login
        r = await client.post("/api/auth/login", json={
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD
        })
        
        if r.status_code != 200:
            log_error(f"Login failed: {r.status_code}")
            return
        
        jwt_token = r.json()["tokens"]["access_token"]
        log_success(f"Logged in as {LOGIN_EMAIL}")
        client.headers["Authorization"] = f"Bearer {jwt_token}"
        
        # Create API Key
        r = await client.post("/api/auth/api-keys", json={
            "name": f"automation_test_{datetime.now().strftime('%H%M%S')}",
            "permissions": ["*"]
        })
        
        if r.status_code not in [200, 201]:
            log_error(f"Failed to create API key: {r.status_code}")
            return
        
        api_key = r.json()["key"]
        log_success(f"Created API Key: {api_key[:25]}...")
        
        # Switch to API Key auth
        del client.headers["Authorization"]
        client.headers["X-API-Key"] = api_key
        log_info("Switched to API Key authentication")
        
        # ============================================================
        # STEP 2: Create Assistants with Different Names
        # ============================================================
        log_step(2, total_steps, f"Creating {len(AGENT_NAMES)} Assistants")
        
        for name in AGENT_NAMES:
            r = await client.post("/api/assistants", json={
                "name": f"{name} - AI Sales Agent",
                "instructions": f"""You are {name}, a friendly AI sales assistant from Vobiz.

When the call is answered:
1. Greet them warmly: "Hi, this is {name} from Vobiz!"
2. Ask how you can help them today
3. Be conversational and helpful
4. End politely when done

Always introduce yourself as {name}.""",
                "first_message": f"Hi there! This is {name} calling from Vobiz. How are you doing today?",
                "voice": {"provider": "openai", "voice_id": "alloy"},
                "temperature": 0.8
            })
            
            if r.status_code in [200, 201]:
                agent_id = r.json()["assistant_id"]
                created_agents.append({"name": name, "id": agent_id})
                log_success(f"Created: {name} → {agent_id}")
            else:
                log_error(f"Failed to create {name}: {r.status_code}")
        
        # ============================================================
        # STEP 3: Verify Assistants in Database (via API)
        # ============================================================
        log_step(3, total_steps, "Verify Assistants in Database")
        
        r = await client.get("/api/assistants")
        if r.status_code == 200:
            response_data = r.json()
            # API returns {"assistants": [...], "count": N}
            all_assistants = response_data.get("assistants", []) if isinstance(response_data, dict) else response_data
            log_success(f"Total assistants in database: {len(all_assistants)}")
            
            # Check our created ones exist
            for agent in created_agents:
                found = False
                for a in all_assistants:
                    if isinstance(a, dict) and a.get("assistant_id") == agent["id"]:
                        found = True
                        break
                if found:
                    log_info(f"{agent['name']}: ✓ Found in database")
                else:
                    log_error(f"{agent['name']}: Not found!")
        else:
            log_error(f"Failed to list assistants: {r.status_code}")
        
        # ============================================================
        # STEP 4: Create SIP Config
        # ============================================================
        log_step(4, total_steps, "Create/Get SIP Configuration")
        
        r = await client.post("/api/sip-configs", json={
            "name": "Automation Test SIP",
            "sip_domain": "008654e7.sip.vobiz.ai",
            "sip_username": "piyush123",
            "sip_password": "Password@123",
            "from_number": "+912271264303",
            "is_default": False
        })
        
        if r.status_code in [200, 201]:
            sip_data = r.json()
            sip_id = sip_data["sip_id"]
            created_sips.append(sip_id)
            log_success(f"Created SIP config: {sip_id}")
        else:
            # Get existing
            r = await client.get("/api/sip-configs")
            if r.status_code == 200:
                data = r.json()
                sips = data.get("sip_configs", []) if isinstance(data, dict) else data
                if isinstance(sips, list) and len(sips) > 0:
                    sip_id = sips[0]["sip_id"]
                    log_info(f"Using existing SIP config: {sip_id}")
                else:
                    log_error("No SIP configs available")
                    sip_id = None
            else:
                sip_id = None
        
        # ============================================================
        # STEP 5: Create Phone Number
        # ============================================================
        log_step(5, total_steps, "Create Phone Number")
        
        r = await client.post("/api/phone-numbers", json={
            "number": "+912271264303",
            "label": "Automation Test Line",
            "provider": "vobiz"
        })
        
        if r.status_code in [200, 201]:
            phone_id = r.json()["phone_id"]
            created_phones.append(phone_id)
            log_success(f"Created phone number: {phone_id}")
        else:
            log_info("Phone number already exists or failed")
        
        # ============================================================
        # STEP 6: Make Calls with Each Agent
        # ============================================================
        log_step(6, total_steps, f"Making Calls with {len(created_agents)} Agents")
        
        for agent in created_agents[:2]:  # Only first 2 to avoid too many calls
            call_payload = {
                "phone_number": TARGET_PHONE,
                "assistant_id": agent["id"],
                "metadata": {
                    "agent_name": agent["name"],
                    "test": "full_automation",
                    "timestamp": datetime.now().isoformat()
                }
            }
            if sip_id:
                call_payload["sip_id"] = sip_id
            
            r = await client.post("/api/calls", json=call_payload)
            
            if r.status_code in [200, 201]:
                call_data = r.json()
                call_id = call_data["call_id"]
                created_calls.append({"agent": agent["name"], "call_id": call_id})
                log_success(f"{agent['name']}: Call created → {call_id}")
            else:
                log_error(f"{agent['name']}: Call failed → {r.status_code}")
        
        # Wait a moment
        log_info("Waiting 3 seconds for calls to process...")
        await asyncio.sleep(3)
        
        # ============================================================
        # STEP 7: Verify Calls in Database
        # ============================================================
        log_step(7, total_steps, "Verify Calls in Database")
        
        r = await client.get("/api/calls")
        if r.status_code == 200:
            data = r.json()
            all_calls = data.get("calls", []) if isinstance(data, dict) else data
            log_success(f"Total calls in database: {len(all_calls)}")
            
            for call in created_calls:
                found = False
                for c in all_calls:
                     if isinstance(c, dict) and c.get("call_id") == call["call_id"]:
                         found = True
                         break
                
                if found:
                    log_info(f"{call['agent']}'s call: ✓ Found → {call['call_id'][:25]}...")
                else:
                    log_error(f"{call['agent']}'s call: Not found!")
        
        # ============================================================
        # STEP 8: Get Individual Call Details
        # ============================================================
        log_step(8, total_steps, "Get Call Details")
        
        for call in created_calls:
            r = await client.get(f"/api/calls/{call['call_id']}")
            if r.status_code == 200:
                data = r.json()
                status = data.get("status", "unknown")
                log_success(f"{call['agent']}: {call['call_id'][:20]}... → Status: {status}")
            else:
                log_error(f"Failed to get call details: {r.status_code}")
        
        # ============================================================
        # STEP 9: Delete Some Assistants
        # ============================================================
        log_step(9, total_steps, "Delete Test Assistants")
        
        # Delete last 2 agents
        for agent in created_agents[-2:]:
            r = await client.delete(f"/api/assistants/{agent['id']}")
            if r.status_code in [200, 204]:
                log_success(f"Deleted: {agent['name']} ({agent['id']})")
            else:
                log_error(f"Failed to delete {agent['name']}: {r.status_code}")
        
        # ============================================================
        # STEP 10: Verify Deletion
        # ============================================================
        log_step(10, total_steps, "Verify Deletion in Database")
        
        r = await client.get("/api/assistants")
        if r.status_code == 200:
            data = r.json()
            remaining = data.get("assistants", []) if isinstance(data, dict) else data
            log_success(f"Remaining assistants: {len(remaining)}")
            
            # Check deleted ones are gone
            for agent in created_agents[-2:]:
                found = False
                for a in remaining:
                    if isinstance(a, dict) and a.get("assistant_id") == agent["id"]:
                        found = True
                        break
                if not found:
                    log_info(f"{agent['name']}: ✓ Confirmed deleted")
                else:
                    log_error(f"{agent['name']}: Still exists!")
            
            # Check remaining ones still exist
            for agent in created_agents[:-2]:
                found = False
                for a in remaining:
                    if isinstance(a, dict) and a.get("assistant_id") == agent["id"]:
                        found = True
                        break
                if found:
                    log_info(f"{agent['name']}: ✓ Still exists")
                else:
                    log_error(f"{agent['name']}: Missing!")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        log_section("AUTOMATION TEST SUMMARY")
        
        print(f"""
{Colors.BOLD}Created Resources:{Colors.END}
  • Assistants: {len(created_agents)} (deleted {len(created_agents[-2:])})
  • Phone Numbers: {len(created_phones)}
  • SIP Configs: {len(created_sips)}
  • Calls Made: {len(created_calls)}

{Colors.BOLD}Agents Created:{Colors.END}""")
        for agent in created_agents:
            print(f"  • {agent['name']}: {agent['id']}")
        
        print(f"""
{Colors.BOLD}Calls Made:{Colors.END}""")
        for call in created_calls:
            print(f"  • {call['agent']}: {call['call_id']}")
        
        print(f"""
{Colors.GREEN}{Colors.BOLD}
✓ FULL AUTOMATION TEST COMPLETE!
  All APIs tested with API Key authentication.
{Colors.END}""")
        
        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "agents": created_agents,
            "calls": created_calls,
            "phones": created_phones,
            "sips": created_sips
        }
        with open("automation_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: automation_test_results.json")


def main():
    asyncio.run(run_full_automation())


if __name__ == "__main__":
    main()
