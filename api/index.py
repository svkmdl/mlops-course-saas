from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from openai import OpenAI, OpenAIError
import os

app = FastAPI()

clerk_config = ClerkConfig(jwks_url =os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

@app.get("/api", response_class=StreamingResponse)
def idea(creds: HTTPAuthorizationCredentials = Depends(clerk_guard)):

    user_id = creds.decoded["sub"] # User ID from JWT - for future use
    # We now know which user is making the request
    # How to use this info :
    # - track usage per user
    # - store generated ideas in db
    # - apply user specific limits or customization

    client = OpenAI(
        # increase default timeout to 15 minutes (from 10 minutes) for service_tier="flex" calls to be on the safe side
        # timeout=900.0
    )
    prompt = [
        {
            "role": "user",
            "content": "Reply with a new business idea for AI Agents, formatted with headings, sub-headings and bullet points"
        }
    ]
    stream = client.chat.completions.create(model="gpt-5-nano", messages=prompt, stream=True) # service_tier="flex"

    def event_stream():
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                lines = text.split("\n")
                for line in lines:
                    yield f"data: {line}\n"
                yield "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")