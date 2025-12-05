# Techfest-ASTRA-MurfAI
# ⚡ ASTRA – Conversational Voice Assistant  
### Built for Techfest 2025-26 • Murf Voice Agent Hackathon  
----------------------------
Astra is a **fully-functional desktop voice AI** built using:

- **Murf Falcon TTS API** (ultra-fast, natural voice output)  
- **ASR (Speech Recognition)** for real-time conversation  
- **Gemini AI** for intelligent responses  
- **PyQt6** for a neon cyber-themed UI  
- **Wake-word detection** (“Hey Astra”)  
- **Reminders, notes, logs, command execution & more**  

Everything is packed inside **one single Python file (`app.py`)**, making it portable, easy to review, and perfect for hackathons.

----------------------------

## 🎯 Objective

This project was built to demonstrate **how effectively Murf Falcon can power a responsive, natural, and interactive voice agent** in a real desktop environment.

Astra uniquely combines:
- Fast input → response loop  
- Real-time speech output  
- Functional utilities (apps, reminders, notes)  
- Dynamic UI + animations  

----------------------------

## 🎤 Features

### 🔊 Voice Interaction
- Real-time STT (ASR)
- Wake-word detection (“hey astra”, “ok astra”, “computer”)
- Gemini AI conversational responses
- **Murf Falcon TTS output** (primary speaking engine)
- Fallback TTS via pyttsx3

### 🧠 Functional Skills
- Open apps (Chrome, Notepad, VS Code, etc.)
- Web search (Google)
- Create / view reminders
- Notes system
- Logs for all commands
- Secure API keys via `.env`

### 🎨 UI & UX
- PyQt6 neon interface  
- Smooth animations  
- Typing effect for AI replies  
- Three themes:
  - Neon Blue
  - Cyber Green
  - Holographic  
- Settings panel for:
  - Speech rate
  - Volume
  - Typing speed
  - STT engine
  - Theme  

----------------------------
## 🛠️ Installation

### 1. Clone the repo
git clone <your-repo-link>
### 2. Install dependencies
Copy code
pip install -r requirements.txt
### 3. Add your .env file
Create a .env file in the same folder:

GEMINI_API_KEY=your_key_here

MURF_API_KEY=your_key_here

DEEPGRAM_API_KEY=optional

OPENWEATHER_API_KEY=optional

NEWSAPI_KEY=optional

4. Run ASTRA
Copy code
python app.py.

🏆 Why ASTRA stands out
Entire application in one optimized Python file

Neon animated UI (rare in voice agents)

Wake-word based continuous listening

Robust skill system (reminders, notes, apps)

Smooth Falcon-powered speech pipeline

Practical, real-world desktop assistant design

----------------------------

👤 Author
Built by Kartikeya Jagadale & Ayush Kalambe

LinkedIn: 

@MurfAI

Built using Murf Falcon – the consistently fastest TTS API.
