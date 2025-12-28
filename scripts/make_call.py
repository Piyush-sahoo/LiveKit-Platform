#!/usr/bin/env python
"""
Vobiz Call Setup Script
-----------------------
This script sets up a SIP configuration, creates an assistant, and makes a test call.

Usage:
    python scripts/make_call.py
"""
import httpx
import asyncio
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Gateway API

# SIP Credentials (provided by user)
SIP_CONFIG = {
    "name": "Vobiz Production",
    "sip_domain": "008654e7.sip.vobiz.ai",
    "sip_username": "piyush123",
    "sip_password": "Password@123",
    "from_number": "+912271264303",
    "is_default": True
}

# Target phone number
TARGET_PHONE = "+919148227303"

# Assistant configuration
ASSISTANT_CONFIG = {
    "name": "Vobiz Test Agent",
    "instructions": """You are a friendly AI assistant from Vobiz. 
    
    When the call is answered:
    1. Greet the person warmly
    2. Introduce yourself as an AI assistant from Vobiz
    3. Mention this is a test call to verify the system is working
    4. Ask if they have any questions
    5. End the call politely when they're done
    
    Be concise, professional, and friendly.""",
    "first_message": "Hello! This is a test call from Vobiz AI. How are you doing today?",
    "voice": {
        "provider": "openai",
        "voice_id": "alloy"
    }
}


async def setup_and_call():
    """Set up SIP config, assistant, and make a call."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 50)
        print("VOBIZ CALL SETUP SCRIPT")
        print("=" * 50)
        
        # Step 1: Create Phone Number
        print("\n[1/4] Adding phone number...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/phone-numbers",
                json={
                    "number": SIP_CONFIG["from_number"],
                    "label": "Vobiz Outbound",
                    "provider": "vobiz"
                }
            )
            if response.status_code in [200, 201]:
                phone_data = response.json()
                phone_id = phone_data.get("phone_id")
                print(f"   ✓ Phone number added: {phone_id}")
            else:
                print(f"   ! Phone number may already exist ({response.status_code})")
        except Exception as e:
            print(f"   ! Error: {e}")
        
        # Step 2: Create SIP Config
        print("\n[2/4] Creating SIP configuration...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/sip-configs",
                json=SIP_CONFIG
            )
            if response.status_code in [200, 201]:
                sip_data = response.json()
                sip_id = sip_data.get("sip_id")
                trunk_id = sip_data.get("trunk_id")
                print(f"   ✓ SIP config created: {sip_id}")
                print(f"   ✓ LiveKit trunk ID: {trunk_id}")
            else:
                print(f"   ! Error: {response.status_code} - {response.text}")
                # Try to get existing SIP config
                response = await client.get(f"{BASE_URL}/api/sip-configs")
                if response.status_code == 200:
                    configs = response.json()
                    if configs:
                        sip_id = configs[0].get("sip_id")
                        print(f"   → Using existing SIP config: {sip_id}")
                    else:
                        print("   ✗ No SIP configs found. Exiting.")
                        return
                else:
                    print("   ✗ Failed to get SIP configs. Exiting.")
                    return
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return
        
        # Step 3: Create Assistant
        print("\n[3/4] Creating AI assistant...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/assistants",
                json=ASSISTANT_CONFIG
            )
            if response.status_code in [200, 201]:
                assistant_data = response.json()
                assistant_id = assistant_data.get("assistant_id")
                print(f"   ✓ Assistant created: {assistant_id}")
            else:
                print(f"   ! Error: {response.status_code} - {response.text}")
                # Try to get existing assistant
                response = await client.get(f"{BASE_URL}/api/assistants")
                if response.status_code == 200:
                    assistants = response.json()
                    if assistants:
                        assistant_id = assistants[0].get("assistant_id")
                        print(f"   → Using existing assistant: {assistant_id}")
                    else:
                        print("   ✗ No assistants found. Exiting.")
                        return
                else:
                    print("   ✗ Failed to get assistants. Exiting.")
                    return
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return
        
        # Step 4: Make the call
        print(f"\n[4/4] Making call to {TARGET_PHONE}...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/calls",
                json={
                    "phone_number": TARGET_PHONE,
                    "assistant_id": assistant_id,
                    "sip_id": sip_id,
                    "metadata": {
                        "purpose": "test_call",
                        "initiated_by": "setup_script"
                    }
                }
            )
            if response.status_code in [200, 201]:
                call_data = response.json()
                call_id = call_data.get("call_id")
                status = call_data.get("status")
                print(f"   ✓ Call initiated!")
                print(f"   → Call ID: {call_id}")
                print(f"   → Status: {status}")
                print(f"\n{'=' * 50}")
                print("CALL INITIATED SUCCESSFULLY!")
                print(f"Target: {TARGET_PHONE}")
                print(f"Call ID: {call_id}")
                print(f"{'=' * 50}")
            else:
                print(f"   ✗ Call failed: {response.status_code}")
                print(f"   → {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")


def main():
    """Main entry point."""
    print("\nStarting Vobiz Call Setup...")
    print(f"Target number: {TARGET_PHONE}")
    print(f"SIP domain: {SIP_CONFIG['sip_domain']}")
    print(f"From number: {SIP_CONFIG['from_number']}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return
    
    asyncio.run(setup_and_call())


if __name__ == "__main__":
    main()
