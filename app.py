import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from PIL import Image
import io
from utils.ml_models import WellnessPredictor
from utils.data_manager import DataManager
from utils.recommendations import RecommendationEngine

st.set_page_config(
    page_title="Student Wellness Tracker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
.stApp { background: linear-gradient(135deg, #f5ebe0 0%, #ede0d4 50%, #fdf8f0 100%); color: #4a3728; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #fdf8f0 0%, #f5ebe0 100%); border-right: 1px solid #d5b9a8; }
.metric-card { background: #fdf8f0; border: 1px solid #d5b9a8; border-radius: 14px; padding: 1.2rem; text-align: center; box-shadow: 0 2px 8px rgba(180,140,110,0.1); }
.recommendation-card { background: #fef9f5; border-left: 4px solid #c9956a; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.5rem 0; color: #4a3728; }
.alert-card { background: #fff5f0; border-left: 4px solid #e07a5f; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.5rem 0; color: #7a3b2e; }
.burnout-card { background: #fff0f0; border: 2px solid #e07a5f; border-radius: 14px; padding: 1.2rem; margin: 0.5rem 0; text-align: center; }
.login-box { background: #fdf8f0; border: 1px solid #d5b9a8; border-radius: 20px; padding: 2rem; text-align: center; box-shadow: 0 4px 16px rgba(180,140,110,0.15); }
.quote-card { background: linear-gradient(135deg, #fdf8f0, #f5ebe0); border: 1px solid #d5b9a8; border-radius: 14px; padding: 1.2rem 1.5rem; text-align: center; margin-bottom: 1.5rem; font-style: italic; color: #6b4c3b; }
.streak-card { background: linear-gradient(135deg, #fdf3e7, #fde8c8); border: 2px solid #c9956a; border-radius: 14px; padding: 1.2rem; text-align: center; }
.meditation-card { background: #fdf8f0; border: 1px solid #d5b9a8; border-radius: 14px; padding: 1.5rem; text-align: center; margin: 0.5rem 0; }
.contact-card { background: #fdf8f0; border: 1px solid #d5b9a8; border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0; }
.exam-card { background: linear-gradient(135deg, #fdf3e7, #fde8c8); border: 2px solid #c9956a; border-radius: 14px; padding: 1.2rem; margin: 0.5rem 0; }
.game-card { background: #fdf8f0; border: 2px solid #c9956a; border-radius: 14px; padding: 1.5rem; text-align: center; margin: 0.5rem 0; }
.badge-card { background: linear-gradient(135deg, #fdf3e7, #fde8c8); border: 2px solid #c9956a; border-radius: 12px; padding: 1rem; text-align: center; margin: 0.3rem; }
.profile-card { background: #fdf8f0; border: 1px solid #d5b9a8; border-radius: 20px; padding: 2rem; text-align: center; }
.stButton > button { background: linear-gradient(135deg, #c9956a, #b07d5a); color: white; border: none; border-radius: 10px; width: 100%; font-weight: 600; }
h1, h2, h3 { color: #4a3728; }
</style>
""", unsafe_allow_html=True)

QUOTES = [
    "Believe you can and you're halfway there. — Theodore Roosevelt",
    "It does not matter how slowly you go as long as you do not stop. — Confucius",
    "Your health is an investment, not an expense.",
    "Small daily improvements lead to stunning results.",
    "Take care of your body. It's the only place you have to live. — Jim Rohn",
    "You don't have to be perfect to be amazing.",
    "Every day is a second chance.", "Progress, not perfection.",
    "Your mental health is a priority.",
    "You are stronger than you think.",
    "Be patient with yourself. Nothing in nature blooms all year.",
    "Study hard, but don't forget to take care of yourself too.",
]

MOOD_EMOJIS = {
    "😄 Excellent": 10, "😊 Good": 8, "🙂 Okay": 6,
    "😐 Neutral": 5, "😕 Not Great": 4, "😢 Sad": 3,
    "😰 Anxious": 2, "😩 Terrible": 1,
}

EXAM_TIPS = [
    "📖 Use active recall — close your notes and write what you remember.",
    "⏰ Use Pomodoro: 25 min study + 5 min break.",
    "🧠 Teach the concept to yourself out loud.",
    "💤 Sleep is not optional — brain consolidates memory during sleep.",
    "🥤 Stay hydrated — dehydration reduces focus by 15%.",
    "📝 Make a priority list — tackle hardest subjects when freshest.",
    "🎯 Set small goals for each study session.",
    "📱 Put phone in another room during study.",
    "🌟 Trust your preparation!",
]

for key, val in {
    'logged_in': False, 'step': 'name', 'username': '', 'phone': '',
    'trusted_contacts': [], 'custom_checklist': [], 'checklist_status': {},
    'goals': {"sleep": 8, "study": 6, "water": 8, "exercise": 30},
    'exam_mode': False, 'profile_photo': None,
    'game_score': 0, 'math_question': None, 'math_answer': None,
    'math_score': 0, 'memory_sequence': [], 'memory_phase': 'idle',
    'scramble_word': None, 'scramble_score': 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

CORRECT_OTP = "12345"

def send_email_alert(contact_email, student_name, risk_level, wellness_score):
    try:
        sender = "your_app_email@gmail.com"
        password = "your_app_password"
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = contact_email
        msg['Subject'] = f"Wellness Alert for {student_name}"
        body = f"Student: {student_name}\nRisk: {risk_level}\nScore: {wellness_score}/100\nPlease reach out soon.\n— WellnessAI"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

def calculate_streak(history):
    if not history:
        return 0
    dates = sorted(set([e['date'] for e in history]), reverse=True)
    streak = 0
    for i, date in enumerate(dates):
        expected = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if date == expected:
            streak += 1
        else:
            break
    return streak

def check_burnout(history):
    if len(history) < 3:
        return False, []
    df = pd.DataFrame(history[-7:])
    alerts = []
    if 'stress' in df.columns and df['stress'].mean() >= 8:
        alerts.append("Stress critically high for past week!")
    if 'sleep_hours' in df.columns and df['sleep_hours'].mean() < 5:
        alerts.append("Severe sleep deprivation detected!")
    if 'mood' in df.columns and df['mood'].mean() < 3:
        alerts.append("Mood consistently very low!")
    if 'study_hours' in df.columns and df['study_hours'].mean() > 12:
        alerts.append("Over-studying detected — burnout risk!")
    return len(alerts) > 0, alerts

def get_badges(history, streak):
    badges = []
    if streak >= 3: badges.append(("🔥", "3-Day Streak"))
    if streak >= 7: badges.append(("⚡", "Week Warrior"))
    if streak >= 30: badges.append(("🏆", "Month Master"))
    if len(history) >= 1: badges.append(("🌱", "First Log"))
    if len(history) >= 10: badges.append(("📈", "10 Entries"))
    if len(history) >= 30: badges.append(("🌟", "30 Entries"))
    if history:
        df = pd.DataFrame(history)
        if 'exercise_done' in df.columns and df['exercise_done'].sum() >= 7:
            badges.append(("💪", "Exercise Hero"))
        if 'sleep_hours' in df.columns and df['sleep_hours'].mean() >= 7:
            badges.append(("😴", "Sleep Champion"))
        if 'mood' in df.columns and df['mood'].mean() >= 8:
            badges.append(("😊", "Happy Student"))
    return badges

def generate_weekly_pdf(student_name, history, goals):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "WellnessAI - Weekly Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Student: {student_name}", ln=True)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_data = [e for e in history if e['date'] >= week_ago]
    if week_data:
        df = pd.DataFrame(week_data)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "This Week's Summary", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for label, value in [
            ("Avg Mood", f"{df['mood'].mean():.1f}/10"),
            ("Avg Sleep", f"{df['sleep_hours'].mean():.1f}h"),
            ("Avg Study", f"{df['study_hours'].mean():.1f}h"),
            ("Exercise Days", f"{df['exercise_done'].sum()}"),
            ("Avg Water", f"{df['water_intake'].mean():.1f} glasses"),
            ("Avg Stress", f"{df['stress'].mean():.1f}/10"),
        ]:
            pdf.cell(0, 8, f"  {label}: {value}", ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Daily Log", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for entry in week_data:
            pdf.cell(0, 7, f"  {entry['date']} | Mood: {entry.get('mood')}/10 | Sleep: {entry.get('sleep_hours')}h | Stress: {entry.get('stress')}/10", ln=True)
    return pdf.output()

def generate_math_question():
    ops = ['+', '-', '*']
    op = random.choice(ops)
    if op == '+': a, b = random.randint(10, 99), random.randint(10, 99); ans = a + b
    elif op == '-': a, b = random.randint(20, 99), random.randint(10, 20); ans = a - b
    else: a, b = random.randint(2, 12), random.randint(2, 12); ans = a * b
    return f"{a} {op} {b}", ans

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;'><h1 style='color:#c9956a; font-size:2.5rem;'>🌿 WellnessAI</h1><p style='color:#b07d5a;'>Student Wellness Tracker</p></div>", unsafe_allow_html=True)
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.step == 'name':
            st.markdown("<div class='login-box'><h3 style='color:#c9956a;'>👤 Welcome!</h3><p style='color:#9a7060;'>Enter your name to get started</p></div>", unsafe_allow_html=True)
            st.markdown("")
            username = st.text_input("Your Name", placeholder="Enter your full name...")
            if st.button("Next →"):
                if username.strip() == "":
                    st.error("❌ Name cannot be empty!")
                else:
                    st.session_state.username = username.strip()
                    st.session_state.step = 'phone'
                    st.rerun()

        elif st.session_state.step == 'phone':
            st.markdown(f"<div class='login-box'><h3 style='color:#c9956a;'>📱 Contact Number</h3><p>Hello <b>{st.session_state.username}</b>! 👋</p></div>", unsafe_allow_html=True)
            st.markdown("")
            phone = st.text_input("Mobile Number", placeholder="10-digit number...", max_chars=10)
            if st.button("📱 Send OTP"):
                if len(phone.strip()) != 10:
                    st.error("❌ Please enter exactly 10 digits!")
                else:
                    st.session_state.phone = phone.strip()
                    st.session_state.step = 'otp'
                    st.success(f"✅ OTP sent to XXXXXXX{phone.strip()[-3:]}!")
                    st.rerun()
            if st.button("⬅️ Go Back"):
                st.session_state.step = 'name'
                st.rerun()

        elif st.session_state.step == 'otp':
            st.markdown(f"<div class='login-box'><h3 style='color:#c9956a;'>🔐 OTP Verification</h3><p>OTP sent to XXXXXXX{st.session_state.phone[-3:]}</p></div>", unsafe_allow_html=True)
            st.markdown("")
            otp_input = st.text_input("Enter OTP", placeholder="5-digit OTP...", max_chars=5)
            if st.button("✅ Verify & Login"):
                if otp_input == CORRECT_OTP:
                    st.session_state.logged_in = True
                    st.session_state.student_id = f"Student_{st.session_state.username}"
                    st.rerun()
                else:
                    st.error("❌ Incorrect OTP!")
            if st.button("⬅️ Go Back"):
                st.session_state.step = 'phone'
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
else:
    @st.cache_resource
    def init_services():
        dm = DataManager("data/wellness_data.json")
        predictor = WellnessPredictor()
        engine = RecommendationEngine()
        return dm, predictor, engine

    dm, predictor, rec_engine = init_services()
    student_id = st.session_state.student_id
    student_name = st.session_state.username
    today_quote = QUOTES[datetime.now().timetuple().tm_yday % len(QUOTES)]
    history = dm.get_history(student_id)
    streak = calculate_streak(history)
    burnout_detected, burnout_alerts = check_burnout(history)
    badges = get_badges(history, streak)

    st.markdown("<h1 style='text-align:center; color:#c9956a;'>🌿 Student Wellness Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#b07d5a;'>AI-powered mental & physical health monitoring</p>", unsafe_allow_html=True)
    st.markdown(f'<div class="quote-card">💬 <b>Today\'s Quote:</b> "{today_quote}"</div>', unsafe_allow_html=True)

    if burnout_detected:
        for alert in burnout_alerts:
            st.markdown(f'<div class="burnout-card">🔴 <b>BURNOUT ALERT:</b> {alert}</div>', unsafe_allow_html=True)

    if st.session_state.exam_mode:
        st.markdown(f'<div class="exam-card">🎯 <b>EXAM MODE ON</b> — {random.choice(EXAM_TIPS)}</div>', unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.profile_photo:
            st.image(st.session_state.profile_photo, width=80)
        st.markdown("### 🌿 WellnessAI")
        st.markdown(f"**👤 {student_name}**")
        st.markdown(f"🔥 Streak: **{streak} days**")
        if badges:
            st.markdown(" ".join([b[0] for b in badges]))
        exam_toggle = st.toggle("🎯 Exam Mode", value=st.session_state.exam_mode)
        if exam_toggle != st.session_state.exam_mode:
            st.session_state.exam_mode = exam_toggle
            st.rerun()
        st.markdown("---")
        page = st.radio("Navigation", [
            "📝 Daily Log",
            "📊 Dashboard",
            "🤖 AI & Insights",
            "🧘 Wellness Hub",
            "👥 My Space",
            "📞 Contacts",
        ])
        st.markdown("---")
        if history:
            df_side = pd.DataFrame(history)
            st.metric("Avg Mood", f"{df_side['mood'].mean():.1f}/10")
            st.metric("Entries", len(history))
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.step = 'name'
            st.session_state.username = ''
            st.session_state.phone = ''
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1: DAILY LOG
    # ══════════════════════════════════════════════════════════════════════════
    if page == "📝 Daily Log":
        st.markdown("## 📝 Daily Wellness Log")
        tab1, tab2, tab3 = st.tabs(["📋 Log Entry", "⏰ Reminders", "📔 Diary"])

        with tab1:
            today = datetime.now().strftime("%Y-%m-%d")
            if today in [e['date'] for e in history]:
                st.warning("⚠️ Already logged today! Saving will update today's entry.")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 😊 Mood & Mental Health")
                mood_emoji = st.selectbox("How are you feeling?", list(MOOD_EMOJIS.keys()))
                mood = MOOD_EMOJIS[mood_emoji]
                st.markdown(f"<div style='text-align:center; font-size:3rem;'>{mood_emoji.split()[0]}</div>", unsafe_allow_html=True)
                stress = st.slider("Stress Level", 1, 10, 5)
                anxiety = st.slider("Anxiety Level", 1, 10, 4)
                focus = st.slider("Focus", 1, 10, 6)
                energy = st.slider("Energy Level", 1, 10, 6)
                st.markdown("### 😴 Sleep")
                sleep_hours = st.number_input("Sleep Hours", 0.0, 12.0, 7.0, 0.5)
                sleep_quality = st.slider("Sleep Quality", 1, 10, 7)
                bedtime = st.selectbox("Bedtime", ["Before 10PM", "10-11PM", "11PM-12AM", "After 12AM"])
            with col2:
                st.markdown("### 📚 Study Habits")
                study_hours = st.number_input("Study Hours", 0.0, 16.0, 4.0, 0.5)
                breaks_taken = st.number_input("Breaks Taken", 0, 20, 3)
                productivity = st.slider("Productivity", 1, 10, 6)
                deadlines_stress = st.radio("Upcoming Deadlines?", ["None", "1-2 days", "This week", "Overdue"], horizontal=True)
                st.markdown("### 🏃 Physical Activity")
                exercise_done = st.checkbox("Exercised today?", value=True)
                exercise_mins = 0
                exercise_type = "None"
                if exercise_done:
                    exercise_mins = st.number_input("Exercise Duration (mins)", 0, 300, 30)
                    exercise_type = st.selectbox("Exercise Type", ["Walking", "Running", "Yoga", "Gym", "Sports", "Cycling"])
                water_intake = st.number_input("Water Intake (glasses)", 0, 20, 8)
                meals_proper = st.radio("Proper Meals?", ["All meals", "Skipped 1", "Skipped 2+"], horizontal=True)

            journal = st.text_area("Journal Entry (optional)", placeholder="How are you feeling today?", height=80)
            st.markdown("### 📔 3 Good Things Today")
            good1 = st.text_input("✨ Good thing #1", placeholder="Something positive...")
            good2 = st.text_input("✨ Good thing #2", placeholder="Something you're grateful for...")
            good3 = st.text_input("✨ Good thing #3", placeholder="Something that made you smile...")

            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                if st.button("🌿 Save & Analyze"):
                    entry = {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "time": datetime.now().strftime("%H:%M"),
                        "mood": mood, "mood_emoji": mood_emoji,
                        "stress": stress, "anxiety": anxiety,
                        "focus": focus, "energy": energy,
                        "sleep_hours": sleep_hours, "sleep_quality": sleep_quality, "bedtime": bedtime,
                        "study_hours": study_hours, "breaks_taken": breaks_taken,
                        "productivity": productivity, "deadlines_stress": deadlines_stress,
                        "exercise_done": exercise_done, "exercise_mins": exercise_mins,
                        "exercise_type": exercise_type, "water_intake": water_intake,
                        "meals_proper": meals_proper, "journal": journal,
                        "good_thing_1": good1, "good_thing_2": good2, "good_thing_3": good3
                    }
                    dm.save_entry(student_id, entry)
                    wellness_score, risk_level, predictions = predictor.analyze(entry)
                    st.success("✅ Data saved successfully!")
                    if risk_level == "High" and st.session_state.trusted_contacts:
                        st.error(f"⚠️ High risk! Alerting {len(st.session_state.trusted_contacts)} contact(s).")
                        for contact in st.session_state.trusted_contacts:
                            if contact.get('email'):
                                send_email_alert(contact['email'], student_name, risk_level, wellness_score)
                    r1, r2, r3, r4 = st.columns(4)
                    with r1: st.markdown(f'<div class="metric-card"><h3>🌡️</h3><p>Wellness</p><h2>{wellness_score}/100</h2></div>', unsafe_allow_html=True)
                    with r2: st.markdown(f'<div class="metric-card"><h3>⚠️</h3><p>Risk</p><h2>{risk_level}</h2></div>', unsafe_allow_html=True)
                    with r3: st.markdown(f'<div class="metric-card"><h3>🧠</h3><p>Mental</p><h2>{predictions["mental_score"]}/100</h2></div>', unsafe_allow_html=True)
                    with r4: st.markdown(f'<div class="metric-card"><h3>💪</h3><p>Physical</p><h2>{predictions["physical_score"]}/100</h2></div>', unsafe_allow_html=True)
                    st.markdown("### 🤖 AI Recommendations")
                    recs = rec_engine.get_recommendations(entry, wellness_score, risk_level)
                    for rec in recs:
                        css = "alert-card" if rec['type'] == 'alert' else "recommendation-card"
                        st.markdown(f'<div class="{css}">💡 <b>{rec["category"]}</b>: {rec["message"]}</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown("### ⏰ Reminders")
            c1, c2 = st.columns(2)
            with c1:
                study_enabled = st.toggle("📚 Study Reminder", value=True)
                study_time = st.time_input("Study Time", value=datetime.strptime("09:00", "%H:%M").time())
                if study_enabled and datetime.now().strftime("%H:%M") == study_time.strftime("%H:%M"):
                    st.success("📚 Time to Study!")
                sleep_enabled = st.toggle("😴 Sleep Reminder", value=True)
                sleep_time = st.time_input("Bedtime", value=datetime.strptime("22:00", "%H:%M").time())
                if sleep_enabled and datetime.now().strftime("%H:%M") == sleep_time.strftime("%H:%M"):
                    st.success("😴 Time to sleep!")
            with c2:
                water_enabled = st.toggle("💧 Water Reminder", value=True)
                water_interval = st.selectbox("Remind Every", ["1 hour", "2 hours", "3 hours"])
                if water_enabled:
                    h = datetime.now().hour
                    if water_interval == "1 hour" or (water_interval == "2 hours" and h % 2 == 0) or (water_interval == "3 hours" and h % 3 == 0):
                        st.info("💧 Drink water now!")
                exercise_enabled = st.toggle("🏃 Exercise Reminder", value=True)
                exercise_time = st.time_input("Exercise Time", value=datetime.strptime("07:00", "%H:%M").time())
                if exercise_enabled and datetime.now().strftime("%H:%M") == exercise_time.strftime("%H:%M"):
                    st.success("🏃 Time to exercise!")

            st.markdown("---\n### 📋 Today's Checklist")
            default_items = [
                {"id": "study", "label": "📚 Completed study session"},
                {"id": "water", "label": "💧 Drank 8 glasses of water"},
                {"id": "sleep", "label": "😴 Slept 7-8 hours last night"},
                {"id": "exercise", "label": "🏃 Exercised today"},
                {"id": "meals", "label": "🍽️ Had proper meals"},
                {"id": "meditation", "label": "🧘 Did meditation"},
            ]
            for item in default_items:
                key = f"check_{item['id']}"
                if key not in st.session_state.checklist_status:
                    st.session_state.checklist_status[key] = False
                st.session_state.checklist_status[key] = st.checkbox(item['label'], value=st.session_state.checklist_status.get(key, False), key=key)

            if st.session_state.custom_checklist:
                st.markdown("**My Custom Tasks:**")
                for i, item in enumerate(st.session_state.custom_checklist):
                    ca, cb = st.columns([5, 1])
                    with ca:
                        key = f"custom_check_{i}"
                        if key not in st.session_state.checklist_status:
                            st.session_state.checklist_status[key] = False
                        st.session_state.checklist_status[key] = st.checkbox(item, value=st.session_state.checklist_status.get(key, False), key=key)
                    with cb:
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state.custom_checklist.pop(i)
                            st.rerun()

            ca, cb = st.columns([4, 1])
            with ca:
                new_task = st.text_input("Add Task", placeholder="e.g. Read 20 pages...", label_visibility="collapsed")
            with cb:
                if st.button("Add ✓"):
                    if new_task.strip():
                        st.session_state.custom_checklist.append(new_task.strip())
                        st.rerun()

            total = len(default_items) + len(st.session_state.custom_checklist)
            done = min(sum(1 for k, v in st.session_state.checklist_status.items() if v), total)
            if total > 0:
                p = done / total
                st.markdown(f"### 🎯 Progress: {done}/{total}")
                st.progress(p)
                if p == 1.0: st.balloons(); st.success("🎉 All done!")
                elif p >= 0.7: st.success("💪 Great progress!")
                elif p >= 0.4: st.info("📈 Halfway there!")
                else: st.warning("🌱 Keep going!")

        with tab3:
            st.markdown("### 📔 Gratitude Diary")
            if not history:
                st.info("No entries yet! Start logging.")
            else:
                diary_entries = sorted([e for e in history if e.get('good_thing_1') or e.get('good_thing_2') or e.get('good_thing_3')], key=lambda x: x['date'], reverse=True)
                if not diary_entries:
                    st.info("Fill '3 Good Things' in Log Entry tab!")
                else:
                    for entry in diary_entries:
                        with st.expander(f"📅 {entry['date']}"):
                            for k in ['good_thing_1', 'good_thing_2', 'good_thing_3']:
                                if entry.get(k): st.markdown(f"✨ {entry[k]}")
                            if entry.get('journal'): st.markdown(f"📝 *{entry['journal']}*")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2: DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "📊 Dashboard":
        st.markdown("## 📊 Dashboard")
        tab1, tab2 = st.tabs(["📊 Overview", "📈 Analytics & Progress"])

        with tab1:
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="streak-card"><h2>🔥 {streak}</h2><p>Day Streak</p></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="streak-card"><h2>📅 {len(history)}</h2><p>Total Entries</p></div>', unsafe_allow_html=True)
            with c3:
                if history:
                    avg_s = predictor.batch_analyze(history)[1]
                    avg = int(np.mean(avg_s)) if avg_s else 0
                    st.markdown(f'<div class="streak-card"><h2>⭐ {avg}</h2><p>Avg Wellness</p></div>', unsafe_allow_html=True)

            if badges:
                st.markdown("### 🏅 Badges")
                cols = st.columns(min(len(badges), 5))
                for i, (emoji, name) in enumerate(badges):
                    with cols[i % 5]:
                        st.markdown(f'<div class="badge-card"><h2>{emoji}</h2><p style="font-size:0.7rem;">{name}</p></div>', unsafe_allow_html=True)

            if not history:
                st.info("No data yet! Go to Daily Log to start tracking.")
            else:
                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Avg Mood", f"{df['mood'].mean():.1f}/10")
                with c2: st.metric("Avg Sleep", f"{df['sleep_hours'].mean():.1f}h")
                with c3: st.metric("Avg Study", f"{df['study_hours'].mean():.1f}h")
                with c4: st.metric("Exercise Days", f"{df['exercise_done'].sum()}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['date'], y=df['mood'], name='Mood', line=dict(color='#c9956a', width=2.5)))
                fig.add_trace(go.Scatter(x=df['date'], y=df['stress'], name='Stress', line=dict(color='#e07a5f', width=2.5)))
                fig.add_trace(go.Scatter(x=df['date'], y=df['energy'], name='Energy', line=dict(color='#b5a99a', width=2.5)))
                fig.update_layout(title="Mood, Stress & Energy", paper_bgcolor='rgba(253,248,240,0.9)', plot_bgcolor='rgba(245,235,224,0.5)', font=dict(color='#4a3728'), height=350)
                st.plotly_chart(fig, use_container_width=True)

                ca, cb = st.columns(2)
                with ca:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(x=df['date'], y=df['sleep_hours'], name='Sleep', marker_color='#c9956a'))
                    fig2.add_trace(go.Bar(x=df['date'], y=df['study_hours'], name='Study', marker_color='#b5a99a'))
                    fig2.update_layout(title="Sleep vs Study", paper_bgcolor='rgba(253,248,240,0.9)', plot_bgcolor='rgba(245,235,224,0.5)', font=dict(color='#4a3728'), height=300, barmode='group')
                    st.plotly_chart(fig2, use_container_width=True)
                with cb:
                    categories = ['Mood', 'Sleep', 'Study', 'Exercise', 'Hydration', 'Focus']
                    values = [df['mood'].mean()*10, min(df['sleep_hours'].mean()/8*100,100), min(df['study_hours'].mean()/8*100,100), (df['exercise_done'].sum()/len(df))*100, min(df['water_intake'].mean()/8*100,100), df['focus'].mean()*10]
                    fig3 = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#c9956a', fillcolor='rgba(201,149,106,0.2)'))
                    fig3.update_layout(title="Wellness Radar", paper_bgcolor='rgba(253,248,240,0.9)', font=dict(color='#4a3728'), height=300)
                    st.plotly_chart(fig3, use_container_width=True)

        with tab2:
            col_l, col_c = st.columns([2, 1])
            with col_l:
                if st.button("🎲 Load Sample Data (30 days)"):
                    dm.generate_sample_data(student_id, days=30)
                    st.success("Sample data loaded!")
                    st.rerun()
            with col_c:
                if st.button("🗑️ Clear Data"):
                    dm.clear_data(student_id)
                    st.rerun()

            history = dm.get_history(student_id)
            if not history:
                st.info("No data yet!")
            else:
                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')

                corr_vars = ['mood', 'stress', 'anxiety', 'sleep_hours', 'study_hours', 'focus', 'energy']
                available = [v for v in corr_vars if v in df.columns]
                fig_corr = px.imshow(df[available].corr(), text_auto=True,
                                      color_continuous_scale=[[0,'#e07a5f'],[0.5,'#f5ebe0'],[1,'#c9956a']],
                                      title="Correlation Heatmap")
                fig_corr.update_layout(paper_bgcolor='rgba(253,248,240,0.9)', font=dict(color='#4a3728'), height=400)
                st.plotly_chart(fig_corr, use_container_width=True)

                features, scores, labels = predictor.batch_analyze(history)
                if scores:
                    df['wellness_score'] = scores[:len(df)]
                    colors = ['#c9956a' if s >= 70 else '#d4b896' if s >= 50 else '#e07a5f' for s in scores]
                    fig_pred = go.Figure()
                    fig_pred.add_trace(go.Bar(x=df['date'], y=df['wellness_score'], marker_color=colors))
                    fig_pred.add_hline(y=70, line_dash="dash", line_color="#c9956a", annotation_text="Good")
                    fig_pred.add_hline(y=50, line_dash="dash", line_color="#d4b896", annotation_text="Fair")
                    fig_pred.update_layout(title="Daily Wellness Scores", paper_bgcolor='rgba(253,248,240,0.9)', plot_bgcolor='rgba(245,235,224,0.5)', font=dict(color='#4a3728'), height=300)
                    st.plotly_chart(fig_pred, use_container_width=True)

                    st.markdown("### 📈 Progress Trend")
                    fig_prog = go.Figure()
                    fig_prog.add_trace(go.Scatter(x=df['date'], y=df['wellness_score'], mode='lines+markers', name='Wellness', line=dict(color='#c9956a', width=3)))
                    z = np.polyfit(range(len(df)), df['wellness_score'], 1)
                    p_trend = np.poly1d(z)
                    fig_prog.add_trace(go.Scatter(x=df['date'], y=p_trend(range(len(df))), mode='lines', name='Trend', line=dict(color='#e07a5f', width=2, dash='dash')))
                    fig_prog.update_layout(title="Wellness Trend", paper_bgcolor='rgba(253,248,240,0.9)', plot_bgcolor='rgba(245,235,224,0.5)', font=dict(color='#4a3728'), height=300)
                    st.plotly_chart(fig_prog, use_container_width=True)

                    if len(history) >= 7:
                        first_half = df.head(len(df)//2)['wellness_score'].mean()
                        second_half = df.tail(len(df)//2)['wellness_score'].mean()
                        if second_half > first_half:
                            st.success(f"📈 Your wellness improved by {second_half-first_half:.1f} points!")
                        else:
                            st.warning(f"📉 Wellness dropped by {first_half-second_half:.1f} points. Let's work on it!")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3: AI & INSIGHTS
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "🤖 AI & Insights":
        st.markdown("## 🤖 AI & Insights")
        tab1, tab2 = st.tabs(["🤖 AI Insights", "🎯 Goals"])

        with tab1:
            if not history:
                st.info("No data yet!")
            else:
                latest = history[-1]
                _, risk_level, predictions = predictor.analyze(latest)
                all_scores = predictor.batch_analyze(history)[1]
                overall_avg = int(np.mean(all_scores)) if all_scores else 50
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("Mental Score", f"{predictions['mental_score']}/100")
                with c2: st.metric("Physical Score", f"{predictions['physical_score']}/100")
                with c3: st.metric("7-Day Average", f"{overall_avg}/100")

                if burnout_detected:
                    st.markdown("### 🔥 Burnout Alerts")
                    for alert in burnout_alerts:
                        st.markdown(f'<div class="burnout-card">🔴 {alert}</div>', unsafe_allow_html=True)

                st.markdown("### 📌 Personalized Recommendations")
                recs = rec_engine.get_recommendations(latest, overall_avg, risk_level)
                for rec in recs:
                    css = "alert-card" if rec['type'] == 'alert' else "recommendation-card"
                    st.markdown(f'<div class="{css}">💡 <b>{rec["category"]}</b>: {rec["message"]}</div>', unsafe_allow_html=True)

                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['date'])
                insights = []
                if df['stress'].tail(5).mean() > 7: insights.append("⚠️ High stress in last 5 days.")
                if df['sleep_hours'].tail(5).mean() < 6: insights.append("😴 Chronic sleep deprivation!")
                if df['exercise_done'].tail(7).sum() < 2: insights.append("🏃 Low exercise frequency.")
                if df['mood'].tail(3).mean() < 4: insights.append("💙 Mood consistently low. Talk to someone.")
                if not insights: insights.append("🌟 You are doing great!")
                st.markdown("### 📊 Key Insights")
                for insight in insights:
                    st.markdown(f'<div class="recommendation-card">{insight}</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown("### 🎯 Weekly Goals")
            c1, c2 = st.columns(2)
            with c1:
                sleep_goal = st.number_input("😴 Sleep (h/night)", 4.0, 12.0, float(st.session_state.goals['sleep']), 0.5)
                study_goal = st.number_input("📚 Study (h/day)", 1.0, 16.0, float(st.session_state.goals['study']), 0.5)
            with c2:
                water_goal = st.number_input("💧 Water (glasses)", 4, 15, st.session_state.goals['water'])
                exercise_goal = st.number_input("🏃 Exercise (mins)", 10, 120, st.session_state.goals['exercise'])
            if st.button("💾 Save Goals"):
                st.session_state.goals = {"sleep": sleep_goal, "study": study_goal, "water": water_goal, "exercise": exercise_goal}
                st.success("✅ Goals saved!")
            if history:
                st.markdown("---\n### 📊 This Week's Progress")
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                week_data = [e for e in history if e['date'] >= week_ago]
                if week_data:
                    df_w = pd.DataFrame(week_data)
                    for label, col, goal, unit in [
                        ("😴 Sleep", 'sleep_hours', sleep_goal, "h"),
                        ("📚 Study", 'study_hours', study_goal, "h"),
                        ("💧 Water", 'water_intake', water_goal, " glasses"),
                        ("🏃 Exercise", 'exercise_mins', exercise_goal, " mins")
                    ]:
                        if col in df_w.columns:
                            actual = df_w[col].mean()
                            prog = min(actual / goal, 1.0)
                            color = "🟢" if prog >= 0.8 else "🟡" if prog >= 0.5 else "🔴"
                            st.markdown(f"**{label}** — {actual:.1f}{unit} / {goal}{unit} {color}")
                            st.progress(prog)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4: WELLNESS HUB
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "🧘 Wellness Hub":
        st.markdown("## 🧘 Wellness Hub")
        tab1, tab2, tab3 = st.tabs(["🧘 Meditation", "🧠 Brain Games", "🎯 Exam Mode"])

        with tab1:
            tracks = [
                {"name": "5-Min Morning Calm", "duration": "5 min", "emoji": "🌅", "url": "https://www.youtube.com/embed/inpok4MKVLM", "desc": "Start your day with peace."},
                {"name": "Focus & Study Music", "duration": "30 min", "emoji": "📚", "url": "https://www.youtube.com/embed/WPni755-Krg", "desc": "Deep focus for study."},
                {"name": "Stress Relief", "duration": "10 min", "emoji": "🌿", "url": "https://www.youtube.com/embed/z6X5oEIg6Ak", "desc": "Release stress."},
                {"name": "Sleep Meditation", "duration": "20 min", "emoji": "🌙", "url": "https://www.youtube.com/embed/aEqlQvczMJQ", "desc": "Prepare for deep sleep."},
                {"name": "Anxiety Relief", "duration": "8 min", "emoji": "💆", "url": "https://www.youtube.com/embed/O-6f5wQXSu8", "desc": "Quick anxiety relief."},
                {"name": "Body Scan", "duration": "15 min", "emoji": "✨", "url": "https://www.youtube.com/embed/QS2yDmWk0vs", "desc": "Full body relaxation."},
            ]
            c1, c2 = st.columns(2)
            for i, track in enumerate(tracks):
                with c1 if i % 2 == 0 else c2:
                    st.markdown(f'<div class="meditation-card"><h3>{track["emoji"]} {track["name"]}</h3><p style="color:#9a7060;">⏱️ {track["duration"]}</p><p style="color:#6b4c3b; font-size:0.85rem;">{track["desc"]}</p></div>', unsafe_allow_html=True)
                    if st.button(f"▶️ Play", key=f"play_{i}"):
                        st.video(track['url'])
            st.markdown("---")
            st.markdown('<div class="recommendation-card"><b>🌬️ Box Breathing:</b> 1. 🫁 Inhale 4s → 2. ⏸️ Hold 4s → 3. 💨 Exhale 4s → 4. ⏸️ Hold 4s — Repeat 4 times!</div>', unsafe_allow_html=True)

        with tab2:
            game = st.selectbox("Choose a Game", ["🔢 Math Challenge", "🧠 Memory Sequence", "📝 Word Scramble"])

            if game == "🔢 Math Challenge":
                st.markdown("### 🔢 Math Challenge")
                if st.session_state.math_question is None:
                    q, a = generate_math_question()
                    st.session_state.math_question = q
                    st.session_state.math_answer = a
                st.markdown(f"<div class='game-card'><h2>{st.session_state.math_question} = ?</h2></div>", unsafe_allow_html=True)
                user_ans = st.number_input("Your Answer", value=0, step=1)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Submit"):
                        if user_ans == st.session_state.math_answer:
                            st.success("🎉 Correct!")
                            st.session_state.math_score += 1
                            st.session_state.math_question = None
                            st.rerun()
                        else:
                            st.error(f"❌ Wrong! Answer was {st.session_state.math_answer}")
                            st.session_state.math_question = None
                with c2:
                    if st.button("⏭️ Skip"):
                        st.session_state.math_question = None
                        st.rerun()
                st.markdown(f"### 🏆 Score: {st.session_state.math_score}")
                if st.button("🔄 Reset"):
                    st.session_state.math_score = 0
                    st.rerun()

            elif game == "🧠 Memory Sequence":
                st.markdown("### 🧠 Memory Sequence")
                if st.session_state.memory_phase == 'idle':
                    level = st.slider("Difficulty", 3, 9, 4)
                    if st.button("▶️ Start"):
                        st.session_state.memory_sequence = [random.randint(1, 9) for _ in range(level)]
                        st.session_state.memory_phase = 'show'
                        st.rerun()
                elif st.session_state.memory_phase == 'show':
                    seq = st.session_state.memory_sequence
                    st.markdown(f"<div class='game-card'><h2>{' → '.join(map(str, seq))}</h2></div>", unsafe_allow_html=True)
                    if st.button("✅ I Remember!"):
                        st.session_state.memory_phase = 'input'
                        st.rerun()
                elif st.session_state.memory_phase == 'input':
                    user_input = st.text_input("Enter sequence (space separated)", placeholder="e.g. 3 7 2 5")
                    if st.button("✅ Check"):
                        try:
                            user_seq = list(map(int, user_input.split()))
                            if user_seq == st.session_state.memory_sequence:
                                st.success("🎉 Perfect!")
                                st.session_state.game_score += len(st.session_state.memory_sequence)
                            else:
                                st.error(f"❌ Wrong! Correct: {' → '.join(map(str, st.session_state.memory_sequence))}")
                        except:
                            st.error("❌ Enter numbers separated by spaces!")
                        st.session_state.memory_phase = 'idle'
                st.markdown(f"### 🏆 Score: {st.session_state.game_score}")

            elif game == "📝 Word Scramble":
                st.markdown("### 📝 Word Scramble")
                words = ["MEDITATION", "WELLNESS", "EXERCISE", "SLEEPING", "BREATHING", "HYDRATION", "NUTRITION", "MINDFULNESS", "RELAXATION", "STUDYING"]
                if st.session_state.scramble_word is None:
                    word = random.choice(words)
                    scrambled = list(word)
                    random.shuffle(scrambled)
                    st.session_state.scramble_word = word
                    st.session_state.scrambled = ''.join(scrambled)
                st.markdown(f"<div class='game-card'><h2>{'  '.join(list(st.session_state.scrambled))}</h2></div>", unsafe_allow_html=True)
                user_word = st.text_input("Unscrambled Word", placeholder="Type the word...").upper()
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Submit"):
                        if user_word == st.session_state.scramble_word:
                            st.success(f"🎉 Correct! It was {st.session_state.scramble_word}")
                            st.session_state.scramble_score += 1
                        else:
                            st.error(f"❌ Wrong! It was {st.session_state.scramble_word}")
                        st.session_state.scramble_word = None
                        st.rerun()
                with c2:
                    if st.button("⏭️ Next"):
                        st.session_state.scramble_word = None
                        st.rerun()
                st.markdown(f"### 🏆 Score: {st.session_state.scramble_score}")

        with tab3:
            st.markdown("### 🎯 Exam Stress Mode")
            exam_toggle2 = st.toggle("Enable Exam Mode", value=st.session_state.exam_mode)
            if exam_toggle2 != st.session_state.exam_mode:
                st.session_state.exam_mode = exam_toggle2
                st.rerun()
            if st.session_state.exam_mode:
                st.success("✅ Exam Mode is ON!")
            st.markdown("### 📚 Exam Tips")
            for tip in EXAM_TIPS:
                st.markdown(f'<div class="exam-card">{tip}</div>', unsafe_allow_html=True)
            st.markdown("---\n### ⏱️ Pomodoro Timer")
            c1, c2 = st.columns(2)
            with c1: study_mins = st.number_input("Study (mins)", 10, 60, 25)
            with c2: break_mins = st.number_input("Break (mins)", 5, 30, 5)
            st.info(f"📚 Study **{study_mins} mins** → 🌿 Break **{break_mins} mins** → Repeat!")
            st.markdown('<div class="recommendation-card"><b>5-4-3-2-1 Grounding:</b><br>👀 5 see | 🤚 4 touch | 👂 3 hear | 👃 2 smell | 👅 1 taste</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5: MY SPACE
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "👥 My Space":
        st.markdown("## 👥 My Space")
        tab1, tab2, tab3 = st.tabs(["👤 Profile", "📅 Calendar", "📄 Weekly Report"])

        with tab1:
            c1, c2 = st.columns([1, 2])
            with c1:
                if st.session_state.profile_photo:
                    st.image(st.session_state.profile_photo, width=150)
                else:
                    st.markdown("<div style='font-size:5rem; text-align:center;'>👤</div>", unsafe_allow_html=True)
                uploaded = st.file_uploader("Upload Photo", type=['jpg', 'jpeg', 'png'])
                if uploaded:
                    img = Image.open(uploaded)
                    img = img.resize((200, 200))
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    st.session_state.profile_photo = buf.getvalue()
                    st.success("✅ Photo updated!")
                    st.rerun()
                if st.session_state.profile_photo and st.button("🗑️ Remove Photo"):
                    st.session_state.profile_photo = None
                    st.rerun()
            with c2:
                st.markdown(f"### 👤 {student_name}")
                st.markdown(f"📱 XXXXXXX{st.session_state.phone[-3:]}")
                st.markdown(f"🔥 Streak: **{streak} days**")
                st.markdown(f"📅 Total Entries: **{len(history)}**")
                if history:
                    df_p = pd.DataFrame(history)
                    st.markdown(f"😊 Avg Mood: **{df_p['mood'].mean():.1f}/10**")
                    st.markdown(f"😴 Avg Sleep: **{df_p['sleep_hours'].mean():.1f}h**")
                    st.markdown(f"📚 Avg Study: **{df_p['study_hours'].mean():.1f}h**")
                    st.markdown(f"🏃 Exercise Days: **{df_p['exercise_done'].sum()}**")
                st.markdown("### 🏅 Badges")
                if badges:
                    cols = st.columns(min(len(badges), 4))
                    for i, (emoji, name) in enumerate(badges):
                        with cols[i % 4]:
                            st.markdown(f'<div class="badge-card"><h3>{emoji}</h3><p style="font-size:0.7rem;">{name}</p></div>', unsafe_allow_html=True)
                else:
                    st.info("Start logging to earn badges!")
                if streak < 3: st.info(f"🔥 Log {3-streak} more days for '3-Day Streak'!")
                elif streak < 7: st.info(f"⚡ Log {7-streak} more days for 'Week Warrior'!")
                else: st.success("🌟 You're doing amazing!")

        with tab2:
            st.markdown("### 📅 Wellness Calendar")
            if not history:
                st.info("No data yet!")
            else:
                features, scores, labels = predictor.batch_analyze(history)
                date_scores = {entry['date']: scores[i] for i, entry in enumerate(history) if i < len(scores)}
                df_hist = pd.DataFrame(history)
                df_hist['date'] = pd.to_datetime(df_hist['date'])
                df_hist = df_hist.sort_values('date', ascending=False)
                for _, row in df_hist.iterrows():
                    date_str = row['date'].strftime("%Y-%m-%d")
                    score = date_scores.get(date_str, 0)
                    color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                    with st.expander(f"{color} {date_str} — Score: {score:.0f}/100"):
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("😊 Mood", f"{row.get('mood', '-')}/10")
                            st.metric("😰 Stress", f"{row.get('stress', '-')}/10")
                        with c2:
                            st.metric("😴 Sleep", f"{row.get('sleep_hours', '-')}h")
                            st.metric("📚 Study", f"{row.get('study_hours', '-')}h")
                        with c3:
                            st.metric("🏃 Exercise", f"{row.get('exercise_mins', 0)}m")
                            st.metric("💧 Water", f"{row.get('water_intake', '-')}g")
                        with c4:
                            st.metric("🧠 Focus", f"{row.get('focus', '-')}/10")
                            st.metric("⚡ Energy", f"{row.get('energy', '-')}/10")
                        for k in ['good_thing_1', 'good_thing_2', 'good_thing_3']:
                            if row.get(k): st.markdown(f"✨ {row[k]}")
                        if row.get('journal'): st.markdown(f"📝 *{row['journal']}*")

        with tab3:
            st.markdown("### 📄 Weekly Report")
            if not history:
                st.info("No data yet!")
            else:
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                week_data = [e for e in history if e['date'] >= week_ago]
                if not week_data:
                    st.warning("No data this week. Load sample data first.")
                else:
                    df_w = pd.DataFrame(week_data)
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Avg Mood", f"{df_w['mood'].mean():.1f}/10")
                    with c2: st.metric("Avg Sleep", f"{df_w['sleep_hours'].mean():.1f}h")
                    with c3: st.metric("Avg Study", f"{df_w['study_hours'].mean():.1f}h")
                    with c4: st.metric("Exercise Days", f"{df_w['exercise_done'].sum()}")
                    if st.button("📥 Generate PDF"):
                        pdf_bytes = generate_weekly_pdf(student_name, history, st.session_state.goals)
                        st.download_button("⬇️ Download PDF", data=bytes(pdf_bytes),
                                           file_name=f"wellness_{datetime.now().strftime('%Y%m%d')}.pdf",
                                           mime="application/pdf")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6: CONTACTS
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "📞 Contacts":
        st.markdown("## 📞 Trusted Contacts")
        st.markdown("Add people who will be notified if your wellness drops critically.")
        c1, c2 = st.columns(2)
        with c1:
            contact_name = st.text_input("Contact Name", placeholder="e.g. Mom...")
            contact_phone = st.text_input("Phone Number", placeholder="10-digit...", max_chars=10)
        with c2:
            contact_email = st.text_input("Email Address", placeholder="email@gmail.com...")
            contact_relation = st.selectbox("Relation", ["Parent", "Friend", "Sibling", "Counselor", "Teacher", "Other"])
        if st.button("➕ Add Contact"):
            if contact_name.strip() == "":
                st.error("❌ Name cannot be empty!")
            elif len(contact_phone.strip()) != 10:
                st.error("❌ Enter exactly 10 digits!")
            elif "@" not in contact_email:
                st.error("❌ Enter valid email!")
            else:
                st.session_state.trusted_contacts.append({
                    "name": contact_name.strip(), "phone": contact_phone.strip(),
                    "email": contact_email.strip(), "relation": contact_relation
                })
                st.success(f"✅ {contact_name} added!")
                st.rerun()

        st.markdown(f"### 📋 Your Contacts ({len(st.session_state.trusted_contacts)})")
        if not st.session_state.trusted_contacts:
            st.info("No contacts added yet!")
        else:
            for i, contact in enumerate(st.session_state.trusted_contacts):
                ca, cb = st.columns([4, 1])
                with ca:
                    st.markdown(f'<div class="contact-card"><b>👤 {contact["name"]}</b> | 🔗 {contact["relation"]} | 📱 XXXXXXX{contact["phone"][-3:]} | 📧 {contact["email"]}</div>', unsafe_allow_html=True)
                with cb:
                    if st.button("🗑️", key=f"rem_{i}"):
                        st.session_state.trusted_contacts.pop(i)
                        st.rerun()

        st.markdown('<div class="recommendation-card" style="margin-top:1rem;">⚠️ <b>Alert Triggers:</b> Score below 30 | Low mood 3+ days | Stress 9-10 | Sleep less than 4h</div>', unsafe_allow_html=True)

        if history and st.session_state.trusted_contacts:
            latest = history[-1]
            _, risk_level, _ = predictor.analyze(latest)
            if risk_level == "High":
                st.error(f"⚠️ Current risk is HIGH! Alert sent to {len(st.session_state.trusted_contacts)} contact(s).")
            else:
                st.success("✅ Wellness looks okay. No alerts sent.")