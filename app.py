import streamlit as st
import os
from PIL import Image
from google.genai import types
import time

# Import our custom modules (Separation of Concerns)
from ai_engine import get_gemini_client, extract_robust_json, JSON_PROMPT
from ui_components import (
    init_session_state, reset_analysis, hard_clear_data, 
    welcome_modal, privacy_modal, render_metrics_and_flags, 
    render_chat_advisor, render_report_generator
)

# ==========================================
# 1. INITIALIZATION & CONFIG
# ==========================================
st.set_page_config(page_title="Scam Screener AI", page_icon="🛡️", layout="centered", initial_sidebar_state="expanded")

def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css("style.css")

init_session_state()
client = get_gemini_client()

if st.session_state.first_visit:
    welcome_modal()

# ==========================================
# 2. SIDEBAR MENU
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color: #1E88E5; margin-bottom: 0px;'>🛡️ Info Menu</h3>", unsafe_allow_html=True)
    st.write("---")
    if st.button("💡 How it Works", use_container_width=True):
        welcome_modal()
    if st.button("🔒 Privacy Policy", use_container_width=True):
        privacy_modal()
    st.write("---")
    if st.button("🗑️ Clear Session Data", type="primary", use_container_width=True):
        hard_clear_data()
        st.rerun()

# ==========================================
# 3. HEADER & TITLE
# ==========================================
st.markdown("""
    <div style='text-align: center; margin-top: 20px;'>
        <span style='font-size: 3.5em; vertical-align: middle;'>🛡️</span>
        <span style='color: #1E88E5; font-size: 3.5em; font-weight: 600; margin-left: 10px; vertical-align: middle;'>Scam Screener AI</span>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; font-size: 16px; margin-top: 0px; margin-bottom: 40px;'>Proactive threat detection for digital communications.</p>", unsafe_allow_html=True)

# ==========================================
# 4. INPUT ZONE & TAB ISOLATION
# ==========================================
tab_img, tab_txt = st.tabs(["📸 Visual Evidence", "📝 Raw Text Evidence"])

with tab_img:
    uploaded_file = st.file_uploader("Upload visual evidence", type=["jpg", "png", "jpeg"], label_visibility="collapsed", key=f"file_{st.session_state.widget_key}", on_change=reset_analysis)
    
    if st.button("Execute Threat Scan (Image)", type="primary", use_container_width=True):
        if uploaded_file:
            reset_analysis()
            st.session_state.original_threat = "[Visual Evidence Uploaded]"
            
            with st.spinner("Executing Optical Character Recognition & Threat Analysis..."):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        uploaded_file.seek(0)
                        img = Image.open(uploaded_file)
                        img.thumbnail((1024, 1024)) # Shrinks the image to a max of 1024 pixels
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', 
                            contents=[JSON_PROMPT, img],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                safety_settings=[
                                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE")
                                ]
                            )
                        )
                        st.session_state.ai_json_data = extract_robust_json(response.text)
                        st.session_state.analysis_done = True
                        st.session_state.active_analysis_type = "image"
                        break # Success! Exit the loop.

                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            st.toast(f"Google Server busy. Retrying... (Attempt {attempt+2}/{max_retries})", icon="⏳")
                            time.sleep(3) # Wait 3 seconds before trying again
                        else:
                            st.toast(f"System Log: {str(e)}", icon="⚠️")
                            st.session_state.ai_json_data = extract_robust_json("FAIL")
                            st.session_state.analysis_done = True
                            st.session_state.active_analysis_type = "image"
                            break
        else:
            st.warning("Please upload an image first.")
            
    if st.session_state.analysis_done and st.session_state.active_analysis_type == "image":
        with st.expander("🖼️ View Uploaded Evidence", expanded=False):
            if uploaded_file is not None:
                uploaded_file.seek(0)
                st.image(uploaded_file, use_container_width=True)
        render_metrics_and_flags()
        render_chat_advisor()
        render_report_generator()

with tab_txt:
    user_text = st.text_area("Paste raw text data:", height=120, placeholder="Paste suspicious SMS, email, or message here...", label_visibility="collapsed", key=f"text_{st.session_state.widget_key}", on_change=reset_analysis)
    
    if st.button("Execute Threat Scan (Text)", type="primary", use_container_width=True):
        if user_text.strip():
            reset_analysis()
            st.session_state.original_threat = user_text
            
            with st.spinner("Executing Linguistic Threat Analysis..."):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', 
                            contents=f"{JSON_PROMPT}\n\nTarget Text: {user_text}",
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                safety_settings=[
                                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE")
                                ]
                            )
                        )
                        st.session_state.ai_json_data = extract_robust_json(response.text)
                        st.session_state.analysis_done = True
                        st.session_state.active_analysis_type = "text"
                        break # Success!

                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            st.toast(f"Google Server busy. Retrying... (Attempt {attempt+2}/{max_retries})", icon="⏳")
                            time.sleep(3)
                        else:
                            st.toast(f"System Log: {str(e)}", icon="⚠️")
                            st.session_state.ai_json_data = extract_robust_json("FAIL")
                            st.session_state.analysis_done = True
                            st.session_state.active_analysis_type = "text"
                            break
        else:
            st.warning("Please enter text first.")

    if st.session_state.analysis_done and st.session_state.active_analysis_type == "text":
        render_metrics_and_flags()
        render_chat_advisor()
        render_report_generator()
