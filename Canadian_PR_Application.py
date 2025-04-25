import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
# email_alert.py
import smtplib
# email_alert.py
import smtplib
from email.message import EmailMessage

# Send alert email using Gmail (App password required)
def send_alert_email(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = 'sk.sukrit.kapoor@gmail.com'  # Replace with your email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('sk.sukrit.kapoor@gmail.com', 'gbjwdemnyddulwht')  # Replace with your app password
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

def get_latest_draw():
    url = "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    service = Service(service = Service("C:/Users/sukri/Desktop/PR Predictive model/chromedriver.exe"))  # Replace if needed with full path
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        # ✅ Wait until the draw table is loaded
        WebDriverWait(driver, 10).until(
           EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )

        # Now the table should be present
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table")

        if not table:
            return None, "⚠️ Table not found, draw might not be available yet."

        rows = table.find_all("tr")
        if len(rows) < 2:
            return None, "⚠️ No rows found in draw table."

        first_row = rows[1].find_all("td")
        if len(first_row) < 4:
            return None, "⚠️ Incomplete data for the latest draw."

        date = first_row[1].text.strip()
        round_type = first_row[2].text.strip()
        invitations = first_row[3].text.strip()
        crs = first_row[4].text.strip()

        result = f"""📅 Date: {date}
📄 Type: {round_type}
📨 Invitations: {invitations}
🎯 CRS Score: {crs}"""

        return result, None  # ✅ draw data + no error

    except Exception as e:
        return None, f"⚠️ An error occurred: {e}"
    finally:
        driver.quit()

def check_for_new_draw(draw_text):
    last_seen = ""  # always define first

    try:
        with open("last_draw.txt", "r", encoding="utf-8") as f:
            last_seen = f.read().strip()
    except FileNotFoundError:
        pass  # file will be created after first draw

    is_new = draw_text.strip() != last_seen

    if is_new:
        try:
            with open("last_draw.txt", "w", encoding="utf-8") as f:
                f.write(draw_text.strip())
        except Exception as e:
            print(f"❗ Failed to update draw file: {e}")

    return is_new
    
# ------------------------
# Simulated cutoff data (based on 2023 IRCC reports)
# ------------------------
cutoffs = {
    "PNP": 748,
    "CEC-General": 541,
    "CEC-STEM": 486,
    "CEC-Healthcare": 450,
    "CEC-French": 422,
    "CEC-Trades": 420,
    "CEC-Education": 435,
    "CEC-Agriculture": 392,
    "FSWP-General": 541,
    "FSWP-STEM": 486,
    "FSWP-Healthcare": 450,
    "FSWP-French": 422,
    "FSWP-Trades": 420,
    "FSWP-Education": 435,
    "FSWP-Agriculture": 392,
    "FSTP-General": 541,
    "FSTP-Trades": 420
}

# ------------------------
# Train Model Once
# ------------------------
sim_data = []
for key, cutoff in cutoffs.items():
    for crs in range(300, 801, 5):
        sim_data.append({
            "CRS_Score": crs,
            "Scenario": key,
            "Received_ITA": int(crs >= cutoff)
        })

df = pd.DataFrame(sim_data)
df_encoded = pd.get_dummies(df, columns=["Scenario"])
X = df_encoded.drop(columns=["Received_ITA"])
y = df_encoded["Received_ITA"]

model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# ------------------------
# Streamlit Dashboard Setup
# ------------------------
st.set_page_config(page_title="Express Entry ITA Estimator", page_icon="🍁", layout="centered")
st.markdown("""
    <style>
        body {
            background-color: #f0f8ff;
            color: #003366;
        }
        .stButton>button {
            background-color: #d72d35;
            color: white;
        }
        .stSlider>div>div>div>div {
            background: #003366;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🍁 Express Entry ITA Probability Estimator")
st.markdown("Estimate your chances of receiving an ITA based on your CRS score, program, and category.")

# Language Toggle
lang = st.sidebar.radio("Language / Langue:", ["English", "Français"])

# Sidebar for input
st.sidebar.header("Your Profile")
program = st.sidebar.selectbox("Select Express Entry Program:", ["PNP", "CEC", "FSWP", "FSTP"])
category = "General"
if program != "PNP":
    category = st.sidebar.selectbox("Select Category:", ["General", "STEM", "Healthcare", "French", "Trades", "Education", "Agriculture"])
crs_score = st.sidebar.slider("Your CRS Score:", 300, 800, 475)

# Predict
scenario_key = f"{program}-{category}" if program != "PNP" else "PNP"
if f"Scenario_{scenario_key}" not in X.columns:
    st.error(f"Sorry, we don't have data for this combination: {scenario_key}")
else:
    input_data = {col: 0 for col in X.columns}
    input_data["CRS_Score"] = crs_score
    input_data[f"Scenario_{scenario_key}"] = 1
    input_df = pd.DataFrame([input_data])
    probability = model.predict_proba(input_df)[0][1]

    # Custom color box for probability display
    prob_color = "#e63946" if probability < 0.85 else "#007f5f"
    st.markdown(f"""
        <div style='background-color: {prob_color}; padding: 1em; border-radius: 8px; text-align: center;'>
            <h3 style='color: white;'>Estimated ITA Probability under '{scenario_key}' with CRS {crs_score}: {probability:.2%}</h3>
        </div>
    """, unsafe_allow_html=True)

    # Customized guidance
    st.subheader("📌 What To Do Next")
    if probability >= 0.85:
        st.markdown("""
        <div style='font-size: 16px;'>
        <strong>✅ You’re in a strong position for an ITA!</strong><br><br>
        🇨🇦 Here’s what you can do next:
        <ul>
            <li>🗂️ Prepare your documents: <a href='https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents.html' target='_blank'>Check Required Documents</a></li>
            <li>🩺 Book your medical exam and gather police certificates</li>
            <li>📬 Monitor recent draws: <a href='https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html' target='_blank'>Express Entry Rounds</a></li>
            <li>🖥️ Log in to your IRCC profile and begin your PR application</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-size: 16px;'>
        <strong>📉 Your CRS score might need a boost to secure an ITA.</strong><br><br>
        🍁 Here are some ways you can improve it:
        <ul>
            <li>📖 Improve language scores (IELTS/CELPIP or TEF Canada)</li>
            <li>🎓 Consider additional education or ECA for previous degrees</li>
            <li>👨‍💼 Gain more work experience (especially Canadian experience)</li>
            <li>🌍 Explore <a href='https://www.canada.ca/en/immigration-refugees-citizenship/services/provincial-nominees.html' target='_blank'>Provincial Nominee Programs (PNPs)</a></li>
            <li>👩‍❤️‍👨 Check if your spouse can contribute CRS points</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Latest IRCC draw info
    st.subheader("📅 Latest IRCC Draw Info")
  
    
    # Step 1: Scrape latest draw (your working function)
draw_info, error = get_latest_draw()

if error:
    st.error(error)
    st.stop()  # Prevents app from falsely updating or sending alerts

# If new draw is detected — notify all subscribers
if check_for_new_draw(draw_info):
    st.warning("🚨 New Express Entry Draw Detected!")
    st.info(draw_info)

    try:
        with open("subscribers.txt", "r", encoding="utf-8") as f:
            subscribers = [email.strip() for email in f.readlines()]
    except FileNotFoundError:
        subscribers = []

    for email in subscribers:
        subject = "🚨 New Express Entry Draw Published"
        message = f"A new Express Entry draw has just been released:\n\n{draw_info}"
        send_alert_email(email, subject, message)
else:
    st.success("✅ You're up to date. No new draw yet.")
    st.info(draw_info)
    
st.subheader("📬 Sign Up for Email Alerts")
user_email = st.text_input("Enter your email for draw alerts:")


cleaned_email = user_email.strip().lower()

if cleaned_email == "":
        st.warning("Please enter your email address.")
elif "@" not in cleaned_email or "." not in cleaned_email:
        st.warning("Please enter a valid email format.")
else:
        # ✅ Continue with safe subscription check
        try:
            with open("subscribers.txt", "r", encoding="utf-8") as f:
                subscribers = [line.strip().lower() for line in f.readlines()]
        except FileNotFoundError:
            subscribers = []

        if cleaned_email in subscribers:
            st.info("📌 You're already subscribed.")
        else:
            with open("subscribers.txt", "a", encoding="utf-8") as f:
                f.write(cleaned_email + "\\n")

            welcome_message = (
                "Welcome to Express Entry Alerts!\n\n"
                "You'll now get an email every time a new draw is released by IRCC.\n\n"
                "📊 Current Draw:\n\n" + draw_info +
                f"\n\nTo unsubscribe, click here:\nhttp://localhost:8501?unsubscribe={cleaned_email}"
            )

            sent = send_alert_email(
                to_email=cleaned_email,
                subject="✅ You're Subscribed to Express Entry Alerts",
                body=welcome_message
            )

            if sent:
                st.success("✅ You're subscribed! A welcome email has been sent.")
            else:
                st.error("❌ Email failed to send.")
st.markdown("---")
st.caption("🍁 Built for future Canadians. Based on historic IRCC draw data. Educational use only.")