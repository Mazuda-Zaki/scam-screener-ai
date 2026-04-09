import re
import json
import base64
import requests
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. SYSTEM PROMPTS & CONFIG
# ==========================================
JSON_PROMPT = """
You are an elite cybersecurity AI. Analyze this digital evidence.
Output ONLY a valid JSON object. No markdown, no explanations.
Ensure your response matches this exact JSON structure:
{
  "threat_level": "High",
  "confidence_score": 95, 
  "scam_category": "Phishing",
  "verdict": "Scam",
  "action_plan": "Write 2-3 sentences explaining EXACTLY what the user must do next to stay safe (e.g., Do not click the link, block the sender immediately, and monitor your bank accounts).",
  "incident_summary": "Write a highly detailed, descriptive paragraph explaining EXACTLY how this specific scam works. Break down the scammer's tactic, what their ultimate goal is (e.g., stealing passwords, draining funds), and the psychological trick they are using (like false urgency or authority).",
  "links": ["http://example.com"], 
  "red_flags": [
    {"title": "Suspicious Link", "severity": "red", "description": "1 clear sentence explaining exactly why this specific element is dangerous."}
  ]
}
"""

def get_gemini_client():
    try:
        return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        st.error("System Error: Missing GEMINI_API_KEY in secrets.")
        st.stop()

# ==========================================
# 2. DATA PROCESSING LOGIC
# ==========================================
def extract_robust_json(raw_text):
    """Safely extracts JSON, with a graceful fallback if the AI fails to read the image."""
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except Exception:
        return {
            "threat_level": "Low",
            "confidence_score": 0,
            "scam_category": "Diagnostic Failure",
            "action_plan": "The AI could not extract readable text. Please crop the image or paste the raw text.",
            "incident_summary": "Diagnostic assessment failed. The visual evidence provided was either unreadable, contained no text, or was blocked by safety filters.",
            "links": [],
            "red_flags": [{"title": "Unreadable Evidence", "severity": "orange", "description": "No readable threat patterns were detected in this input."}]
        }

def check_virustotal(url):
    """Queries the VT API for domain reputation."""
    try:
        VT_API_KEY = st.secrets["VIRUSTOTAL_API_KEY"]
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        headers = {"x-apikey": VT_API_KEY}
        response = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
    except Exception:
        return None
    return None