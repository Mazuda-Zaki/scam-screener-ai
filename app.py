import streamlit as st
from google import genai 
from google.genai import types
from PIL import Image
import re          
import requests    
import base64      
import urllib.parse
import json

# ==========================================
# 1. UI & APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Scam Screener AI", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

custom_css = """
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp {background-color: #F8F9FA;} 
.bento-card { background: white; padding: 18px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 100%; border-top: 4px solid #ccc; }
.border-red { border-top-color: #FA5252; }
.border-orange { border-top-color: #FD7E14; }
.border-blue { border-top-color: #339AF0; }
.metric-box { background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #eee; }
.chat-row { display: flex; width: 100%; margin-bottom: 12px; }
.row-user { justify-content: flex-end; }
.row-ai { justify-content: flex-start; }
.bubble-user { background-color: #DCF8C6; padding: 12px 16px; border-radius: 16px 16px 0px 16px; max-width: 85%; color: #111; font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);}
.bubble-ai { background-color: #ffffff; border: 1px solid #eaeaea; padding: 12px 16px; border-radius: 16px 16px 16px 0px; max-width: 85%; color: #111; font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 2. STATE MANAGEMENT 
# ==========================================
def init_session_state():
    defaults = {"analysis_done": False, "ai_json_data": {}, "messages": [], "original_threat": "", "active_tab": None}
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def reset_app():
    for key in ["analysis_done", "ai_json_data", "messages", "original_threat", "active_tab"]:
        st.session_state[key] = None
    st.session_state.analysis_done = False
    st.session_state.messages = []

init_session_state()

# ==========================================
# 3. CORE AI LOGIC (Robust & Modular)
# ==========================================
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"]) 
    VT_API_KEY = st.secrets["VIRUSTOTAL_API_KEY"]
except Exception:
    st.error("Missing API Keys in secrets.toml.")
    st.stop()

JSON_PROMPT = """
You are an elite cybersecurity AI. Analyze this text/image.
Output ONLY a valid JSON object. No markdown, no explanations.
{
  "threat_level": "Low", "Medium", or "High",
  "confidence_score": 95, 
  "scam_category": "e.g., Phishing, Job Scam, Impersonation, Safe",
  "verdict": "Scam" or "Safe",
  "action_plan": "One highly actionable sentence.",
  "links": ["url1"], 
  "red_flags": [
    {"title": "Title", "severity": "red/orange/blue", "description": "1 brief sentence explaining why."}
  ]
}
"""

def extract_robust_json(raw_text):
    """Regex bulletproofs the app against AI formatting errors."""
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("AI failed to output valid JSON.")

def check_virustotal(url):
    """Handles API calls safely without crashing the app."""
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    headers = {"x-apikey": VT_API_KEY}
    try:
        response = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
    except:
        return None
    return None

# ==========================================
# 4. DASHBOARD RENDERER 
# ==========================================
def render_dashboard():
    data = st.session_state.ai_json_data
    st.write("---")
    
    # Header Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#FA5252" if data.get("threat_level") == "High" else "#FD7E14" if data.get("threat_level") == "Medium" else "#40C057"
        st.markdown(f"<div class='metric-box'><h4 style='color:{color}; margin:0;'>{data.get('threat_level')}</h4><p style='margin:0; font-size:12px; color:#888;'>Threat Level</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'><h4 style='color:#1E88E5; margin:0;'>{data.get('confidence_score')}%</h4><p style='margin:0; font-size:12px; color:#888;'>AI Confidence</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box'><h4 style='color:#1E88E5; margin:0;'>{data.get('scam_category')}</h4><p style='margin:0; font-size:12px; color:#888;'>Typology</p></div>", unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)

    # VirusTotal Module
    links = data.get("links", [])
    if links:
        target_url = links[0]
        vt_stats = check_virustotal(target_url)
        if vt_stats and (vt_stats.get('malicious', 0) > 0 or vt_stats.get('suspicious', 0) > 0):
            st.error(f"☠️ **MALWARE DETECTED:** {vt_stats['malicious'] + vt_stats['suspicious']} global security vendors flagged `{target_url}`.")
        elif vt_stats:
            st.info(f"🛡️ `{target_url}` is clean in databases, but rely on the AI behavioral analysis below.")

    # Bento Box Red Flags
    st.markdown("### 🔍 Threat Breakdown")
    cols = st.columns(3)
    flags = data.get("red_flags", [])
    for i, col in enumerate(cols):
        if i < len(flags):
            flag = flags[i]
            border_class = f"border-{flag.get('severity', 'blue')}"
            icon = "🔴" if flag.get('severity') == 'red' else "🟠" if flag.get('severity') == 'orange' else "🔵"
            with col:
                st.markdown(f"""
                <div class="bento-card {border_class}">
                    <h5 style="margin-top:0px; margin-bottom:8px;">{icon} {flag.get('title')}</h5>
                    <p style="font-size:13.5px; color:#555; line-height: 1.4;">{flag.get('description')}</p>
                </div>
                """, unsafe_allow_html=True)
                
    st.write("<br>", unsafe_allow_html=True)
    st.success(f"**Action Plan:** {data.get('action_plan')}")

    # Action Panel & Reporting
    st.write("---")
    colA, colB = st.columns([3, 1])
    with colA:
        st.markdown("### 🚨 Report Incident")
    with colB:
        if st.button("🗑️ Clear Data", use_container_width=True):
            reset_app()
            st.rerun()

    with st.expander("✉️ Generate Formal Report to Authorities"):
        country = st.selectbox("Select Jurisdiction:", ["Malaysia (Cyber999)", "USA (CISA)", "UK (Action Fraud)", "Other"])
        email_map = {"Malaysia (Cyber999)": "cyber999@cybersecurity.my", "USA (CISA)": "report@cisa.gov", "UK (Action Fraud)": "action.fraud@police.uk", "Other": "local_police@example.com"}
        email_target = email_map[country]
        
        body = f"Incident Report\n\nORIGINAL THREAT:\n\"{st.session_state.original_threat}\"\n\nAI VERDICT: {data.get('threat_level')} Risk ({data.get('scam_category')})\n\nRegards,\n[Your Name]"
        mailto_link = f"mailto:{email_target}?subject=Cyber Incident Report&body={urllib.parse.quote(body)}"
        
        st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color:#FA5252; color:white; padding:10px 20px; border-radius:6px; border:none; width:100%; cursor:pointer;">📨 Open Mail App</button></a>', unsafe_allow_html=True)
        st.code(f"To: {email_target}\nSubject: Cyber Incident Report\n\n{body}", language="text")

    # AI Chat Advisor
    st.write("---")
    st.markdown("### 💬 AI Advisor Chat")
    for msg in st.session_state.messages:
        role_class = "row-user" if msg["role"] == "user" else "row-ai"
        bubble_class = "bubble-user" if msg["role"] == "user" else "bubble-ai"
        prefix = "" if msg["role"] == "user" else "<b>🛡️ Advisor:</b><br>"
        st.markdown(f'<div class="chat-row {role_class}"><div class="{bubble_class}">{prefix}{msg["content"]}</div></div>', unsafe_allow_html=True)

    if user_question := st.chat_input("E.g., What happens if I replied to them?"):
        st.markdown(f'<div class="chat-row row-user"><div class="bubble-user">{user_question}</div></div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": user_question})

        with st.spinner("Typing..."):
            chat_context = f"Context: Scam verdict is {data.get('threat_level')}. User asks: '{user_question}'. Reply in 2 sentences max. Be actionable."
            try:
                chat_response = client.models.generate_content(model='gemini-2.5-flash', contents=chat_context)
                reply = chat_response.text
            except:
                reply = "Connection error. Please try again."
                
        st.markdown(f'<div class="chat-row row-ai"><div class="bubble-ai"><b>🛡️ Advisor:</b><br>{reply}</div></div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ==========================================
# 5. MAIN APPLICATION UI
# ==========================================
st.markdown("<h1 style='text-align: center; color: #1E88E5; margin-bottom: 0px;'>🛡️ Scam Screener AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; margin-top: 5px;'>Proactive threat detection for digital communications.</p>", unsafe_allow_html=True)
st.write("---")

tab1, tab2 = st.tabs(["📸 Image Upload", "📝 Text Input"])

with tab1:
    uploaded_file = st.file_uploader("Upload screenshot of conversation:", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if st.button("Analyze Image", type="primary", use_container_width=True):
        if uploaded_file:
            reset_app()
            st.session_state.original_threat = "[Image Evidence Uploaded]"
            with st.spinner("Executing Optical Character Recognition & Threat Analysis..."):
                try:
                    img = Image.open(uploaded_file)
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=[JSON_PROMPT, img])
                    st.session_state.ai_json_data = extract_robust_json(response.text)
                    st.session_state.analysis_done = True
                    st.session_state.active_tab = "image"
                except Exception as e:
                    st.error("Analysis Failed. Ensure image contains readable text.")
        else:
            st.toast("Please upload an image first.", icon="⚠️")
            
    if st.session_state.analysis_done and st.session_state.active_tab == "image":
        st.image(uploaded_file, width=300)
        render_dashboard()

with tab2:
    user_text = st.text_area("Input message text:", height=120, placeholder="Paste suspicious SMS, Telegram, or WhatsApp message here...", label_visibility="collapsed")
    if st.button("Analyze Text", type="primary", use_container_width=True):
        if user_text.strip():
            reset_app()
            st.session_state.original_threat = user_text
            with st.spinner("Executing Linguistic Threat Analysis..."):
                try:
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=f"{JSON_PROMPT}\n\nTarget Text: {user_text}")
                    st.session_state.ai_json_data = extract_robust_json(response.text)
                    st.session_state.analysis_done = True
                    st.session_state.active_tab = "text"
                except Exception as e:
                    st.error("Analysis Failed. The AI returned an unexpected format.")
        else:
            st.toast("Please enter text first.", icon="⚠️")

    if st.session_state.analysis_done and st.session_state.active_tab == "text":
        render_dashboard()
