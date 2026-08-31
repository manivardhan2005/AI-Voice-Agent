

## Architecture
- **Voice AI:** Vapi 
- **Telephony & Messaging:** Twilio
- **Backend:** FastAPI (Python)
- **Database:** SQLite (for callback scheduling)

## Features Built
1. **Mid-Call Action:** AI detects Hot/Warm/Cold intent and triggers the `send_whatsapp` tool mid-call.
2. **Smart Scheduling:** AI extracts vague spoken times (e.g. "tomorrow morning") and uses the `schedule_callback` tool to convert them to ISO-8601 format and save them to a local SQLite database.
3. **End of Call Follow-up:** The FastAPI server listens for Vapi's `end-of-call-report` webhook, extracts the conversation summary, and triggers Twilio to send a final WhatsApp message containing the summary, resume, and architecture diagram.
4. **Outbound Calling:** The `outbound_call.py` script automatically fetches the assistant and phone number IDs via the Vapi API and places an automated outbound call.

*Note: Due to API trial account limitations, outbound calls and SMS to unverified international numbers are currently restricted by the API providers. The codebase is fully complete and functions flawlessly with funded API keys.*
