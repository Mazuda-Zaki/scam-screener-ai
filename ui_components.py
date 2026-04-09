import streamlit as st
import uuid
import urllib.parse
from ai_engine import check_virustotal, get_gemini_client

# ==========================================
# 1. STATE MANAGEMENT
# ==========================================
def init_session_state():
    defaults = {
        "analysis_done": False, 
        "ai_json_data": {}, 
        "messages": [], 
        "original_threat": "", 
        "first_visit": True,
        "widget_key": str(uuid.uuid4()),
        "active_analysis_type": None # <--- THIS FIXES THE TAB BLEEDING BUG
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def reset_analysis():
    """Silently completely clears the dashboard so the app is ready for a new scan."""
    st.session_state.analysis_done = False
    st.session_state.ai_json_data = {}  # Keeps it as an empty dictionary to prevent crash errors
    st.session_state.messages = []
    st.session_state.original_threat = ""
    st.session_state.active_analysis_type = None

def hard_clear_data():
    reset_analysis()
    st.session_state.widget_key = str(uuid.uuid4()) 

# ==========================================
# 2. MODALS
# ==========================================
@st.dialog("Welcome to Scam Screener AI 🛡️")
def welcome_modal():
    st.markdown("""
    **Proactive Threat Interception & Analysis**
    
    **Standard Operating Procedure:**
    1. **📥 Ingest Evidence:** Upload a screenshot or paste raw text from any unverified digital communication.
    2. **🧠 Execute Scan:** Our zero-trust engine analyzes psychological manipulation vectors and cross-references URLs against global databases.
    3. **🚨 Review & Act:** Consult the AI Security Advisor or generate a standardized incident report for authorities.
    """)
    if st.button("Acknowledge & Proceed 🚀", type="primary", use_container_width=True):
        st.session_state.first_visit = False
        st.rerun()

@st.dialog("Data Privacy Policy 🔒")
def privacy_modal():
    st.markdown("""
    ### Data Protection & Zero-Retention Policy
    Strict adherence to user privacy and data security.
    
    * **No Data Logging:** We do not store, log, or persist user-uploaded evidence on our servers.
    * **Volatile Memory Only:** Clicking "Clear Session" or closing the browser permanently destroys the session cache.
    * **Encrypted Processing:** Payloads are transmitted via TLS encryption and are strictly excluded from public LLM training data.
    """)
    if st.button("Close"):
        st.rerun()

# ==========================================
# 3. DASHBOARD RENDERERS
# ==========================================
def render_metrics_and_flags():
    """Draws the Bento Box dashboard."""
    data = st.session_state.ai_json_data
    st.write("---")
    st.markdown("### 📊 Diagnostic Threat Assessment")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#FA5252" if data.get("threat_level") == "High" else "#FD7E14" if data.get("threat_level") == "Medium" else "#40C057"
        st.markdown(f"<div class='metric-box'><h4 style='color:{color}; margin:0;'>{data.get('threat_level')}</h4><p style='margin:0; font-size:12px; color:#888;'>Threat Level</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'><h4 style='color:#1E88E5; margin:0;'>{data.get('confidence_score')}%</h4><p style='margin:0; font-size:12px; color:#888;'>AI Confidence</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box'><h4 style='color:#1E88E5; margin:0;'>{data.get('scam_category')}</h4><p style='margin:0; font-size:12px; color:#888;'>Typology</p></div>", unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)

    links = data.get("links", [])
    if links:
        target_url = links[0]
        vt_stats = check_virustotal(target_url)
        if vt_stats and (vt_stats.get('malicious', 0) > 0 or vt_stats.get('suspicious', 0) > 0):
            st.error(f"☠️ **MALWARE DETECTED:** Security vendors flagged `{target_url}`.")
        elif vt_stats:
            st.info(f"🛡️ `{target_url}` is clean in databases, but rely on the AI behavioral analysis below.")

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
    st.success(f"**Recommended Action:** {data.get('action_plan')}")

def render_chat_advisor():
    """Draws the Chat UI and handles the conversation."""
    st.write("---")
    st.markdown("### 💬 AI Security Advisor")
    st.caption("Consult the AI regarding mitigation strategies for this specific threat.")
    
    data = st.session_state.ai_json_data
    client = get_gemini_client()

    for msg in st.session_state.messages:
        role_class = "row-user" if msg["role"] == "user" else "row-ai"
        bubble_class = "bubble-user" if msg["role"] == "user" else "bubble-ai"
        prefix = "" if msg["role"] == "user" else "<b>🛡️ Advisor:</b><br>"
        st.markdown(f'<div class="chat-row {role_class}"><div class="{bubble_class}">{prefix}{msg["content"]}</div></div>', unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_question = st.text_input("Query:", placeholder="E.g., What should I do if I clicked the link?", label_visibility="collapsed")
        with col_btn:
            submit_chat = st.form_submit_button("Send 💬", use_container_width=True)
            
        if submit_chat and user_question.strip():
            st.session_state.messages.append({"role": "user", "content": user_question})
            chat_context = f"You are an objective cybersecurity advisor. Context: Threat Level: {data.get('threat_level')}. Summary: {data.get('incident_summary')}. User asks: '{user_question}'. Reply in 2-3 sentences. Be clear and highly actionable."
            try:
                chat_response = client.models.generate_content(model='gemini-2.5-flash', contents=chat_context)
                reply = chat_response.text
            except:
                reply = "Connection error. Please try again."
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

def render_report_generator():
    """Draws the Email Drafting tool."""
    st.write("---")
    with st.expander("🚨 Generate Standardized Incident Report", expanded=False):
        st.markdown("Use this tool to auto-draft a formal incident report to cybersecurity authorities.")
        data = st.session_state.ai_json_data
        
        country = st.selectbox("Select Jurisdiction:", ["Malaysia (Cyber999)", "USA (CISA)", "UK (Action Fraud)", "Other"])
        email_map = {"Malaysia (Cyber999)": "cyber999@cybersecurity.my", "USA (CISA)": "report@cisa.gov", "UK (Action Fraud)": "action.fraud@police.uk", "Other": "local_police@example.com"}
        email_target = email_map[country]
        
        body = f"CONFIDENTIAL CYBER INCIDENT REPORT\n\nTo Whom It May Concern,\n\nI am submitting a formal report regarding a suspected digital threat.\n\n[*** ATTN: PLEASE SEE ATTACHED EVIDENCE FILE ***]\n\nTHREAT INTELLIGENCE SUMMARY:\n{data.get('incident_summary')}\n\nAI DIAGNOSTIC ASSESSMENT:\n- Severity Level: {data.get('threat_level')}\n- Identified Typology: {data.get('scam_category')}\n\nPlease advise on required mitigation steps or if further digital forensics are necessary to process this report.\n\nRegards,\n[Your Name]\n[Your Contact Number]"
        
        mailto_link = f"mailto:{email_target}?subject=Formal Cyber Incident Report&body={urllib.parse.quote(body)}"
        
        st.warning("⚠️ **Chain of Custody:** You MUST manually attach your original screenshot/evidence to the email before sending.")
        st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color:#FA5252; color:white; padding:10px 20px; border-radius:6px; border:none; width:100%; cursor:pointer; margin-bottom: 10px;">📨 Open Mail Client</button></a>', unsafe_allow_html=True)
        st.code(f"To: {email_target}\nSubject: Formal Cyber Incident Report\n\n{body}", language="text")