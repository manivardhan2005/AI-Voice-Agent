import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('VAPI_API_KEY')
target_number = os.environ.get('TEST_PHONE_NUMBER')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

print("1. Fetching your Assistant ID...")
res_ast = httpx.get('https://api.vapi.ai/assistant', headers=headers)
assistants = res_ast.json()
assistant_id = assistants[0]['id'] if assistants else None

print("2. Fetching your Phone Number ID...")
res_phone = httpx.get('https://api.vapi.ai/phone-number', headers=headers)
phone_numbers = res_phone.json()
phone_number_id = phone_numbers[0]['id'] if phone_numbers else None

if not assistant_id or not phone_number_id:
    print("Error: Could not find an Assistant or Phone Number in your Vapi account.")
    exit(1)

print(f"-> Found Assistant: {assistant_id}")
print(f"-> Found Phone: {phone_number_id}")

print(f"\n3. Placing call to {target_number}...")
payload = {
    "assistantId": assistant_id,
    "phoneNumberId": phone_number_id,
    "customer": {
        "number": target_number
    }
}

res_call = httpx.post('https://api.vapi.ai/call/phone', headers=headers, json=payload)

if res_call.status_code == 201:
    print("\n✅ SUCCESS! Vapi is calling your phone right now!")
else:
    print(f"\n❌ Error placing call: {res_call.status_code}")
    print(res_call.text)
