# 🛡️ Scam Screener AI  
**The Digital X-Ray for Suspicious Communications**

Scam Screener AI is a proactive, zero-trust threat analysis web application designed to assist users in identifying and mitigating potential cyber threats. The system functions as an on-demand cybersecurity analysis tool, enabling users to safely upload suspicious screenshots or text messages to detect psychological manipulation techniques and malicious links *before* any harm occurs.

---

## 📖 Project Explanation

Modern cyber threats increasingly rely on social engineering techniques—such as phishing, false urgency, and authority bias—rather than solely on technical malware exploits. Traditional antivirus solutions are insufficient in such scenarios, as they cannot prevent users from voluntarily disclosing sensitive information due to psychological manipulation.

**Scam Screener AI addresses these limitations through the following features:**

* **Multimodal Threat Ingestion:**  
  Supports the analysis of both textual data and visual content (e.g., screenshots), enabling comprehensive threat evaluation.

* **Dual-Engine Diagnostics:**  
  Integrates advanced analytical capabilities by detecting psychological red flags using Google Gemini Flash, while simultaneously identifying malicious URLs through the VirusTotal API.

* **Zero-Retention Privacy Model:**  
  Ensures user privacy by maintaining no databases or logs. All session data is permanently deleted once the user clears the session or exits the application.

* **Actionable Output:**  
  Translates complex diagnostic results into a structured, color-coded dashboard, complemented by an AI Security Advisor and an automatically generated formal cyber incident report.

---

### 🛑 Advantages Over Public AI Chatbots

During high-stress situations, users may resort to external AI chat platforms, which introduces friction and potential risks related to data exposure. In contrast, **Scam Screener AI incorporates a built-in Contextual Security Advisor**, which operates within a secure environment and possesses full awareness of the analyzed content. This enables the system to deliver immediate, context-specific, and actionable guidance without requiring users to leave the platform.

---

### 🏛️ Transforming Users from Victims to Active Defenders

In many cases, detected scams are simply ignored or deleted, resulting in a lack of reporting and continued threat propagation. To address this issue, the system automatically generates a formal cyber incident report aligned with relevant authorities (e.g., Cyber999 for Malaysia).  

By eliminating the complexity of report preparation, users are provided with a ready-to-send, professionally structured email. This feature encourages active reporting and contributes to broader cybersecurity awareness and prevention efforts within the community.

---

## 🛠️ Tech Stack & Architecture

* **Frontend / User Interface:** Streamlit (Python)  
* **AI Engine:** Google Gemini 2.5 Flash (with strict JSON output formatting)  
* **Threat Intelligence Integration:** VirusTotal API v3  
* **Image Processing:** Pillow (PIL)  

*(Refer to `flowchart.md` for detailed system architecture and workflow design.)*

---

## ⚙️ Setup Instructions

### 1. Prerequisites
Ensure that the following software is installed on your system:

* Python 3.9 or higher  
* Git  

---

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/scam-screener-ai.git
cd scam-screener-ai
```

---

### 3. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows:**
```bash
venv\Scripts\activate
```

- **macOS / Linux:**
```bash
source venv/bin/activate
```

---

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 5. Configure API Keys (Secrets)

This application requires API keys for **Google Gemini** and **VirusTotal**.

#### Steps:
1. Create a folder named:
```
.streamlit
```

2. Inside the folder, create a file named:
```
secrets.toml
```

3. Add your API keys as follows:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_google_gemini_key_here"
VIRUSTOTAL_API_KEY = "your_virustotal_key_here"
```

⚠️ **Security Notice:**  
Do not commit the `secrets.toml` file to version control.  
Ensure that `.streamlit/` or `.streamlit/secrets.toml` is included in your `.gitignore` file.

---

## 🚀 How to Run the Application

After completing the setup, execute the following command:

```bash
streamlit run app.py
```

The application will automatically launch in your default web browser at:  
👉 http://localhost:8501  

---

## 📂 File Structure

- `app.py`  
  Main entry point responsible for routing, tab management, and overall application state.

- `ai_engine.py`  
  Contains backend logic, including prompt engineering, JSON parsing, and error-handling mechanisms.

- `ui_components.py`  
  Handles user interface rendering, including dashboards, modals, chat features, and report generation.

- `style.css`  
  Defines custom styling for the frontend interface.
