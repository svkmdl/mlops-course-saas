from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI, OpenAIError
import os

app = FastAPI()

@app.get("/api", response_class=StreamingResponse)
def idea():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set in environment")
    client = OpenAI(
        # increase default timeout to 15 minutes (from 10 minutes) for service_tier="flex" calls to be on the safe side
        # timeout=900.0,
        api_key=api_key
    )
    prompt = [{"role": "user", "content": "In a few sentences, come up with a new business idea using AI Agents"}]
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