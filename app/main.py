from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
import os
import sqlite3
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ElevateBox Voice Agent API")

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect("callbacks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_datetime TEXT,
            timezone TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Voice Agent API is running"}

@app.post("/tools")
async def handle_tool_calls(request: Request):
    payload = await request.json()
    
    # Vapi wraps everything in a "message" object
    message = payload.get("message", {})
    
    if message.get("type") == "tool-calls":
        results = []
        
        # Vapi can send multiple tool calls at once
        for tool_call_block in message.get("toolWithToolCallList", []):
            tool_call = tool_call_block.get("toolCall", {})
            function_data = tool_call.get("function", {})
            
            function_name = function_data.get("name")
            raw_args = function_data.get("arguments", {})
            if isinstance(raw_args, str):
                arguments = json.loads(raw_args) if raw_args else {}
            else:
                arguments = raw_args
            call_id = tool_call.get("id")
            
            print(f"\n--- AI TRIGGERED TOOL: {function_name} ---")
            print(f"Arguments: {arguments}")
            
            # 1. Handle WhatsApp Mid-Call Action
            if function_name == "send_whatsapp":
                intent = arguments.get("intent")
                print(f"[HOT LEAD] Customer is {intent}! Sending real WhatsApp via Twilio...")
                
                try:
                    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                    twilio_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
                    if not twilio_number:
                        twilio_number = 'whatsapp:+14155238886'
                    target_number = os.environ.get('TEST_PHONE_NUMBER')
                    
                    if account_sid and auth_token and target_number:
                        client = Client(account_sid, auth_token)
                        message = client.messages.create(
                            from_=twilio_number.replace('whatsapp:', ''),
                            body=f"Hi there! Thank you for contacting ElevateBox. We noticed you're highly interested (Intent: {intent}). A human agent will call you back shortly with a special offer!",
                            to=target_number.replace('whatsapp:', '')
                        )
                        print(f"[SUCCESS] SMS Message sent! SID: {message.sid}")
                    else:
                        print("[ERROR] Missing Twilio credentials in .env")
                except Exception as e:
                    print(f"[TWILIO ERROR] {e}")

                results.append({
                    "toolCallId": call_id,
                    "result": "WhatsApp sent successfully mid-call."
                })
                
            # 2. Handle Callback Scheduling
            elif function_name == "schedule_callback":
                scheduled_datetime = arguments.get("scheduled_datetime")
                timezone = arguments.get("timezone", "Asia/Kolkata")
                reason = arguments.get("callback_reason", "General callback")
                
                print(f"[CALLBACK] Customer wants a callback at: {scheduled_datetime} ({timezone}) for '{reason}'")
                
                try:
                    conn = sqlite3.connect("callbacks.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO callbacks (scheduled_datetime, timezone, reason) VALUES (?, ?, ?)",
                        (scheduled_datetime, timezone, reason)
                    )
                    conn.commit()
                    conn.close()
                    print("[SUCCESS] Callback saved to database.")
                except Exception as e:
                    print(f"[DB ERROR] {e}")

                results.append({
                    "toolCallId": call_id,
                    "result": f"Callback successfully scheduled for {scheduled_datetime}."
                })
                
            # 3. Handle Saving the Lead
            elif function_name == "save_lead":
                print(f"[SAVE LEAD] Saving Lead Data: {arguments}")
                results.append({
                    "toolCallId": call_id,
                    "result": "Lead details saved to database."
                })
                
            else:
                results.append({
                    "toolCallId": call_id,
                    "result": f"Unknown tool: {function_name}"
                })
                
        return {"results": results}
        
    elif message.get("type") == "end-of-call-report":
        print("\n" + "="*50)
        print("📞 CALL HAS ENDED - GENERATING POST-CALL FOLLOW UP")
        print("="*50)
        
        analysis = message.get("analysis", {})
        summary = analysis.get("summary", "We discussed your requirements for an e-commerce website.")
        
        final_follow_up = f"""Hi there! Thank you for speaking with me today.
        
Here is a quick summary of what we discussed regarding your e-commerce build:
{summary}

As promised, here is my contact information and project details:
Phone: +91 83098 34564
Resume: https://elevatebox-intern-resume.com/maniv
Architecture Diagram: https://elevatebox-intern-architecture.com/diagram.png

Looking forward to building something cool together!"""
        print(final_follow_up)
        
        try:
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            twilio_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            target_number = os.environ.get('TEST_PHONE_NUMBER')
            
            if account_sid and auth_token and target_number:
                client = Client(account_sid, auth_token)
                sms = client.messages.create(
                    from_=twilio_number.replace('whatsapp:', ''),
                    body=final_follow_up[:1500],
                    to=target_number.replace('whatsapp:', '')
                )
                print(f"[SUCCESS] Post-Call SMS Follow-up sent! SID: {sms.sid}")
        except Exception as e:
            print(f"[TWILIO ERROR] {e}")
            
        return {"status": "success"}

    return {"status": "ignored", "reason": "Unhandled event type"}
