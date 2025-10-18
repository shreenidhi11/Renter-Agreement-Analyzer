import os
import io  # <-- Add this import
import PyPDF2  # <-- Add this import
import json  # <-- FIX: Add this import
from docx import Document
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# --- Pydantic Models (for data validation) ---
# We do not need the LeaseText Model now that we are tryong to upload a file
# class LeaseText(BaseModel):
#     """The input text from the user."""
#     text: str


class LeaseReport(BaseModel):
    """The structured JSON output we want from the AI."""

    # --- Money Questions ---
    security_deposit: str = Field(description="Total amount of the security deposit (e.g., '$2000').")
    deposit_conditions: str = Field(
        description="Summary of conditions for losing the deposit (e.g., 'Damage beyond normal wear, unpaid rent, cleaning fees').")
    non_refundable_fees: str = Field(
        description="List any non-refundable fees (e.g., 'Move-in fee: $500, Pet fee: $250').")
    late_fee_policy: str = Field(
        description="The policy for late rent (e.g., '$50 fee if paid after the 5th of the month').")

    # --- Moving Out Questions ---
    termination_notice: str = Field(
        description="The required notice period before the lease ends (e.g., '60 days written notice').")
    early_termination_penalty: str = Field(
        description="The penalty for breaking the lease early (e.g., 'Must pay 2 months' rent').")
    auto_renewal_clause: str = Field(
        description="Does the lease auto-renew? (e.g., 'Yes, renews month-to-month' or 'Yes, renews for 1 year').")

    # --- Living There Questions ---
    pet_policy: str = Field(
        description="Summary of pet rules (e.g., 'Allowed, $50/month pet rent, 40lb weight limit').")
    guest_policy: str = Field(
        description="Summary of guest rules (e.g., 'Guests allowed for up to 14 consecutive days').")
    subletting_policy: str = Field(
        description="Is subletting allowed? (e.g., 'Not allowed without written landlord consent').")
    maintenance_and_repairs: str = Field(
        description="Who is responsible for repairs (e.g., 'Tenant responsible for minor repairs, landlord for major systems').")
    utilities_included: str = Field(
        description="List all utilities paid by the landlord (e.g., 'Water and trash. Tenant pays gas and electric.').")

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

# --- The AI Prompt ---
# FIX: This is now a simple template with placeholders
PROMPT_TEMPLATE = """
You are an expert legal assistant specializing in rental agreements.
Your task is to extract specific, critical information from the lease text provided.
Analyze the text and populate *all* fields in the JSON object.

**CRITICAL RULES:**
1.  **Strictly Adhere to Schema:** Each field's summary must *only* contain information directly related to that field's description from the schema.
2.  **Handle Missing Information:** If information for a specific field is not present in the text, the value for that field must be *only* the string "Not found".
3.  **No Data Contamination:** Do *not* mention the absence of information for one field (e.g., "Guest policy was not found") in the summary of *another* field.

**Field Instructions:**
* For policies (like 'pet_policy' or 'guest_policy'), summarize the rule.
* For fees (like 'late_fee_policy'), state the cost and conditions.

Return *only* a JSON object that strictly follows this Pydantic schema:
{schema}

Here is the lease text:
---
{lease_text}
---

Return *only* the JSON. Do not add any conversational text or markdown.
"""


# --- API Endpoint ---
@app.post("/summarize", response_model=LeaseReport)
async def summarize_lease(file: UploadFile = File(...)):
    """
    Receives a lease file (PDF or TXT or DOCX), extracts text, queries Gemini,
    and returns a structured report.
    """

    lease_text = ""
    contents = await file.read()  # Read the file bytes

    # --- File Processing Logic ---
    if file.filename.endswith('.pdf'):
        try:
            # Read PDF from in-memory bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            for page in pdf_reader.pages:
                lease_text += page.extract_text()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing PDF: {e}")

    elif file.filename.endswith('.txt'):
        try:
            # Decode text file from bytes
            lease_text = contents.decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing TXT file: {e}")
    # adding support for .docx file.from
    elif file.filename.endswith('.docx'):
        try:
            file_stream = io.BytesIO(contents)
            doc = Document(file_stream)
            lease_text = "".join([para.text for para in doc.paragraphs])
            # lease_text = contents.decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing DOCX file: {e}")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a .pdf or .txt file.")

    if not lease_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        )
    )

    # FIX: We build the schema string and format the prompt here
    schema_string = json.dumps(LeaseReport.model_json_schema(), indent=2)

    prompt = PROMPT_TEMPLATE.format(
        lease_text=lease_text,
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