import asyncio
from agents.notification_agent import notify_cluster_status_change
from dotenv import load_dotenv

# Load the keys from .env
load_dotenv()

async def test_twilio():
    print("🚀 Sending test SMS via Twilio...")
    
    # We will send a test notification to the phone number configured in Twilio
    # (replace this if you want to test sending to a different verified number)
    import os
    test_number = os.getenv("TWILIO_FROM_NUMBER") # We'll just text yourself!
    
    if not test_number:
        print("❌ Error: TWILIO_FROM_NUMBER not found in .env")
        return

    # Trigger the agent to simulate a cluster being "Approved"
    result = await notify_cluster_status_change(
        cluster_id="DEMO1234",
        new_status="Approved",
        citizen_phones=[test_number]
    )
    
    print("\n✅ Result:", result)
    if result.get("mode") == "sms" and result.get("sent") > 0:
        print("📱 Check your phone! You should have received a text.")
    else:
        print("⚠️ Looks like it failed or used the stub. Did you save the keys in .env?")

if __name__ == "__main__":
    asyncio.run(test_twilio())
