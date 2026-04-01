import streamlit as st
import google.generativeai as genai
from PIL import Image
import re          
import requests    
import base64      

# Setup the APIs
genai.configure(api_key= st.secrets["GEMINI_API_KEY"]) 
VT_API_KEY = st.secrets["VIRUSTOTAL_API_KEY"]

model = genai.GenerativeModel('gemini-2.5-flash') 

st.title("🚨 Scam Screener AI")
st.write("Analyze suspicious text messages, emails, or screenshots.")

user_text = st.text_area("Option 1: Paste suspicious text here:", height=150)
st.write("--- OR ---")
uploaded_file = st.file_uploader("Option 2: Upload a screenshot of the scam:", type=["jpg", "jpeg", "png"])

if st.button("Analyze Threat"):
    
    ai_response_text = ""
    
    # 1. Image Logic
    if uploaded_file is not None:
        st.info("Analyzing image... please wait.")
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Screenshot", use_container_width=True)
        
        # --- NEW: Added line 5 to force the AI to extract URLs from the image ---
        prompt = """
        Act as a cybersecurity expert. Read the text inside this image and tell me if it is a scam.
        Format your response exactly like this:
        1. Threat Level: (Choose only: Low, Medium, or High)
        2. Verdict: (Scam or Safe)
        3. Red Flags: (Give 3 bullet points explaining why)
        4. Action Plan: (Give 1 sentence on what the user should do next)
        5. Extracted Links: (List any URLs found in the image starting with http:// or https://. If none, write 'None')
        """
        response = model.generate_content([prompt, image])
        ai_response_text = response.text 

    # 2. Text Logic
    elif user_text:
        st.info("Analyzing text... please wait.")
        
        # --- NEW: Added line 5 here too for consistency ---
        prompt = f"""
        Act as a cybersecurity expert. Analyze the following text and tell me if it is a scam.
        Format your response exactly like this:
        1. Threat Level: (Choose only: Low, Medium, or High)
        2. Verdict: (Scam or Safe)
        3. Red Flags: (Give 3 bullet points explaining why)
        4. Action Plan: (Give 1 sentence on what the user should do next)
        5. Extracted Links: (List any URLs found in the text starting with http:// or https://. If none, write 'None')
        
        Text to analyze: {user_text}
        """
        response = model.generate_content(prompt)
        ai_response_text = response.text 
        
    else:
        st.warning("Please paste some text or upload an image first!")

    # --- VISUAL DASHBOARD LOGIC ---
    if ai_response_text:
        st.write("---")
        st.subheader("📊 Threat Analysis Dashboard")
        
        if "High" in ai_response_text:
            st.error("🚨 CRITICAL ALERT: HIGH PROBABILITY OF SCAM")
            st.progress(0.95) 
        elif "Medium" in ai_response_text:
            st.warning("⚠️ WARNING: SUSPICIOUS ELEMENTS DETECTED (MEDIUM RISK)")
            st.progress(0.50) 
        elif "Low" in ai_response_text:
            st.success("✅ SAFE: LOW RISK DETECTED")
            st.progress(0.10) 

        # ==========================================
        # VIRUSTOTAL URL CHECKING LOGIC
        # ==========================================
        # --- NEW: We now search for links inside the user's text AND the AI's response ---
        text_to_search = str(user_text) + " " + ai_response_text
        urls_found = re.findall(r'(https?://[^\s]+)', text_to_search)
        
        # We also want to clean up any weird punctuation the AI might have added to the end of the URL
        clean_urls = [url.rstrip(").,!'\"") for url in urls_found]

        if clean_urls:
            st.write("---")
            st.subheader("🛡️ Database Check (VirusTotal)")
            
            target_url = clean_urls[0] # Check the first link found
            st.write(f"Checking link: `{target_url}`")
            
            url_id = base64.urlsafe_b64encode(target_url.encode()).decode().strip("=")
            headers = {"x-apikey": VT_API_KEY}
            vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            
            try:
                vt_response = requests.get(vt_url, headers=headers)
                vt_data = vt_response.json()
                
                if "data" in vt_data:
                    stats = vt_data['data']['attributes']['last_analysis_stats']
                    malicious_count = stats['malicious']
                    suspicious_count = stats['suspicious']
                    total_scans = malicious_count + suspicious_count + stats['harmless'] + stats['undetected']
                    
                    if malicious_count > 0 or suspicious_count > 0:
                        st.error(f"☠️ **DANGER:** {malicious_count + suspicious_count} out of {total_scans} security vendors flagged this link as malicious!")
                    else:
                        st.success(f"✅ **CLEAN:** 0 out of {total_scans} security vendors flagged this link. (Always trust the AI behavioral analysis if it found red flags!)")
                else:
                    st.info("Link not found in VirusTotal database (It might be too new, which is highly suspicious!)")
            
            except Exception as e:
                st.warning("Could not connect to VirusTotal at this time.")
        # ==========================================

        # Print the AI's full detailed explanation at the very end
        st.write("---")
        st.subheader("🧠 AI Behavioral Analysis")
        st.write(ai_response_text)