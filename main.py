import os
import json  # <-- FIX: Add this import
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# --- Pydantic Models (for data validation) ---
class LeaseText(BaseModel):
    """The input text from the user."""
    text: str


class LeaseReport(BaseModel):
    """The structured JSON output we want from the AI."""
    security_deposit: str
    pet_policy: str
    termination_notice: str
    guest_policy: str
    auto_renewal: str
    hidden_fees: str


# --- FastAPI App ---
app = FastAPI()

# --- CORS Middleware (CRITICAL for Day 2) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- The AI Prompt (The "Secret Sauce") ---
# FIX: This is now a simple template with placeholders
PROMPT_TEMPLATE = """
You are an expert legal assistant specializing in rental agreements.
Your task is to extract specific, critical information from the lease text provided.

Analyze the text and return *only* a JSON object that strictly follows this Pydantic schema:
{schema}

Here is the lease text:
---
{lease_text}
---

Return *only* the JSON. Do not add any conversational text or markdown.
If you cannot find a specific piece of information, return "Not found" for that field.
"""


# --- API Endpoint ---
@app.post("/summarize", response_model=LeaseReport)
async def summarize_lease(lease: LeaseText):
    """
    Receives lease text, queries Gemini, and returns a structured report.
    """
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        )
    )

    # FIX: We build the schema string and format the prompt here
    schema_string = json.dumps(LeaseReport.model_json_schema(), indent=2)

    prompt = PROMPT_TEMPLATE.format(
        lease_text=lease.text,
        schema=schema_string
    )

    response = await model.generate_content_async(prompt)
    print(response.text)

    # This part was already correct for Pydantic v2
    return LeaseReport.model_validate_json(response.text)


# --- Entrypoint (for running the server) ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)