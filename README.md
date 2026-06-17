# 🌿 WellnessAI — Student Wellness Tracker

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-success)

**An AI-powered web application that helps students track and improve their mental & physical wellness using Machine Learning.**

🚀 [Live Demo](https://wellness-tracker-fzdw8ca8gz5f6uxc4uahy2.streamlit.app) · 📂 [Report Bug](https://github.com/Aarti-1209/wellness-tracker/issues)

## 📸 Screenshots

### 🔐 Login Page
<img src="screenshots/login.png" alt="Login Page" width="700"/>

### 📝 Daily Wellness Log
<img src="screenshots/daily-log.png" alt="Daily Log" width="700"/>

### 📊 Dashboard
<img src="screenshots/dashboard.png" alt="Dashboard" width="700"/>

### 🤖 AI Insights
<img src="screenshots/ai-insights.png" alt="AI Insights" width="700"/>

### 🧘 Wellness Hub
<img src="screenshots/wellness-hub.png" alt="Wellness Hub" width="700"/>

## ✨ Features

| Category | Features |
|----------|----------|
| 🔐 Authentication | Secure OTP-based login system |
| 📝 Daily Tracking | Mood, sleep, stress, study hours, exercise, hydration |
| 🤖 AI/ML | Gradient Boosting (wellness score) + Random Forest (burnout risk) |
| ⚠️ Safety | Automatic burnout detection + email alerts to trusted contacts |
| 📊 Analytics | Interactive dashboards, correlation heatmaps, trend analysis |
| 🧘 Wellness Hub | Meditation player, brain games, exam stress mode |
| 📔 Journaling | Gratitude diary, daily reflections |
| 🎯 Goals | Weekly goal setting with progress tracking |
| 🏅 Gamification | Streak system, achievement badges |
| 📄 Reports | Auto-generated PDF weekly wellness reports |

## 🛠️ Tech Stack

- Frontend: Streamlit
- Machine Learning: Scikit-learn (Gradient Boosting Regressor, Random Forest Classifier)
- Data Processing: Pandas, NumPy
- Visualization: Plotly
- PDF Generation: FPDF2
- Image Processing: Pillow
- Deployment: Streamlit Cloud
- Version Control: Git & GitHub

## 🚀 Live Demo

🔗 [Try WellnessAI Live](https://wellness-tracker-fzdw8ca8gz5f6uxc4uahy2.streamlit.app)

## ⚙️ Run Locally

```bash
git clone https://github.com/Aarti-1209/wellness-tracker.git
cd wellness-tracker
pip install -r requirements.txt
streamlit run app.py
```

Open your browser at http://localhost:8501

## 📁 Project Structure
wellness-tracker/

├── app.py

├── requirements.txt

├── utils/

│   ├── ml_models.py

│   ├── data_manager.py

│   └── recommendations.py

└── screenshots/

## 🧠 Machine Learning Models

| Model | Purpose |
|-------|---------|
| GradientBoostingRegressor | Predicts daily wellness score (0-100) |
| RandomForestClassifier | Classifies burnout risk (Low/Medium/High) |
| MinMaxScaler | Feature normalization |

## 👩‍💻 Author

Aarti Yadav
- GitHub: [@Aarti-1209](https://github.com/Aarti-1209)

⭐ If you found this project helpful, give it a star!
