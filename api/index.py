from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from openai import OpenAI, OpenAIError
import os

app = FastAPI()

@app.get("/api", response_class=PlainTextResponse)
def idea():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set in environment")
        client = OpenAI(
            # increase default timeout to 15 minutes (from 10 minutes) for service_tier="flex" calls to be on the safe side
            # timeout=900.0,
            api_key=api_key
        )
        prompt = [{"role": "user", "content": "In a few sentences, come up with a new business idea using AI Agents"}]
        response = client.chat.completions.create(model="gpt-5-nano", messages=prompt, service_tier="flex") # service_tier="flex"
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            raise HTTPException(status_code=500, detail="No response from OpenAI")

    except OpenAIError as oe:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(oe)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")