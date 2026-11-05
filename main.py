# ===========================================================================
# 1. DEPENDENCY INITIALIZATION & ENVIRONMENT SETUP
# ===========================================================================
# Install official Google GenAI SDK and processing requirements
# !pip install --quiet google-genai pydantic pandas openpyxl

import os
import pandas as pd
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.colab import userdata

# Initialize API Key safely from system workspace contexts
try:
    os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
    print("[+] Gemini API Key successfully loaded.")
except Exception:
    os.environ["GEMINI_API_KEY"] = "YOUR_RAW_GEMINI_API_KEY_HERE"
    print("[!] Warning: Using raw inline API Key definition.")

# ===========================================================================
# 2. SCHEMA ARCHITECTURE (Type-Safe Cost Enforcement Constraints)
# ===========================================================================
class InvoiceAuditData(BaseModel):
    carrier_name: str = Field(description="The name of the logistics shipping line or carrier (e.g., Maersk, MSC).")
    container_number: str = Field(description="The tracking ID or container number.")
    base_freight_billed: float = Field(description="The standard base ocean freight rate charged in USD.")
    detention_demurrage_charged: float = Field(description="Total hidden or extra fees like detention, demurrage, or port storage in USD. Return 0 if none.")
    total_amount_billed: float = Field(description="The absolute total invoice amount due in USD.")

# ===========================================================================
# 3. AI COGNITIVE AUDITING NODE
# ===========================================================================
def audit_invoice_via_ai(raw_invoice_text: str, client: genai.Client) -> Optional[InvoiceAuditData]:
    """Uses Gemini API to extract target SCM billing and extra charges from unstructured text."""
    prompt = f"""
    You are an expert Logistics Cost Auditor. Analyze the following raw, unstructured carrier invoice text.
    Extract the billing metrics accurately and map them exactly to the requested schema.
    Do not assume or guess values. Convert all currency to numeric float format.
    
    Raw Carrier Invoice Text:
    \"\"\"{raw_invoice_text}\"\"\"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InvoiceAuditData,
                temperature=0.1 # Enforce absolute rule-based determinism
            )
        )
        return InvoiceAuditData.model_validate_json(response.text)
    except Exception as e:
        print(f"[-] AI Auditing Node Failure: {e}")
        return None

# ===========================================================================
# 4. CONTRACT MATCHING PIPELINE & OVERBILLING DETECTION
# ===========================================================================
def run_cost_auditor_pipeline():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Pre-negotiated standard rate sheet matrix (Company Baseline Contract Rates)
    CONTRACT_RATES = {
        "MSK8890": {"allowed_base": 4500.00, "allowed_extra": 0.00},
        "MSC4012": {"allowed_base": 4200.00, "allowed_extra": 200.00}
    }
    
    # Raw unstructured carrier invoice data stream dumps
    carrier_invoices = [
        """
        MAERSK LINE GLOBAL INVOICE
        Container Ref: MSK8890
        Base Ocean Freight: $4,500.00
        Late Container Return Fee (Detention): $650.00
        Port Storage Charges: $200.00
        Total Billed Amount: $5,350.00 USD
        """,
        """
        MSC SHIPPING INVOICE #9921
        Container Ref: MSC4012
        Standard Ocean Freight: $4,200.00
        Demurrage (Free days exceeded): $200.00
        Total Due: $4,400.00 USD
        """
    ]
    
    print("[*] Launching Logistics Cost Auditor Tool...\n")
    audit_results = []
    
    for idx, invoice_text in enumerate(carrier_invoices):
        print(f"[*] Auditing Invoice {idx+1} across contract matrix...")
        parsed_data = audit_invoice_via_ai(invoice_text, client)
        
        if parsed_data:
            audit_dict = parsed_data.model_dump()
            container = parsed_data.container_number
            
            # Auditor Core Logic: System configuration rate sheets matching bounds
            if container in CONTRACT_RATES:
                allowed_base = CONTRACT_RATES[container]["allowed_base"]
                allowed_extra = CONTRACT_RATES[container]["allowed_extra"]
                
                # Check for baseline discrepancies and hidden charge overbilling
                base_overcharge = max(0.0, parsed_data.base_freight_billed - allowed_base)
                extra_overcharge = max(0.0, parsed_data.detention_demurrage_charged - allowed_extra)
                total_overbilling = base_overcharge + extra_overcharge
                
                audit_dict["allowed_base_rate"] = allowed_base
                audit_dict["overbilled_amount"] = total_overbilling
                audit_dict["audit_status"] = "OVERBILLED - FLAG" if total_overbilling > 0 else "AUDIT PASSED"
            else:
                audit_dict["allowed_base_rate"] = "No Contract Found"
                audit_dict["overbilled_amount"] = 0.0
                audit_dict["audit_status"] = "MANUAL REVIEW REQUIRED"
                
            audit_results.append(audit_dict)
            
    # Flatten database array and save matrix formats onto local disk storage
    if audit_results:
        df = pd.DataFrame(audit_results)
        output_file = "logistics_audit_report.xlsx"
        df.to_excel(output_file, index=False)
        df.to_csv("logistics_audit_report.csv", index=False)
        
        print("\n" + "="*60)
        print(f"[++] AUDIT COMPLETE! Report compiled and locked at: {os.path.abspath(output_file)}")
        print("="*60)
        print(df.to_markdown(index=False))

if __name__ == "__main__":
    run_cost_auditor_pipeline()
