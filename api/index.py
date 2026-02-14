from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
import os

app = FastAPI()

clerk_config = ClerkConfig(jwks_url =os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str

system_prompt = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.
Reply with exactly three sections with the headings:
### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
"""
# improvement idea : respond with json instead of markdown with the headings above

def user_prompt_for_visit(visit: Visit) -> str :
    return f"""Create the summary, next steps and draft email for:
Patient name: {visit.patient_name}
Date of visit: {visit.date_of_visit}
Notes: 
{visit.notes}"""

@app.post("/api", response_class=StreamingResponse)
def consultation_summary(
        visit: Visit,
        creds: HTTPAuthorizationCredentials = Depends(clerk_guard)
):

    user_id = creds.decoded["sub"] # User ID from JWT - for future use
    # We now know which user is making the request
    # How to use this info :
    # - track usage per user
    # - store generated ideas in db
    # - apply user specific limits or customization using their subscription plan

    client = OpenAI(
        # increase default timeout to 15 minutes (from 10 minutes) for service_tier="flex" calls to be on the safe side
        # timeout=900.0
    )

    user_prompt = user_prompt_for_visit(visit)
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    stream = client.chat.completions.create(
        model="gpt-5-nano",
        messages=prompt,
        stream=True
        # service_tier="flex"
    )

    def event_stream():
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                lines = text.split("\n")
                for line in lines:
                    yield f"data: {line}\n"
                yield "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")