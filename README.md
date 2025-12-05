# Techfest-ASTRA-MurfAI
# ⚡ ASTRA — Advanced Speech-based Total Response Assistant

Astra is a **fully-featured desktop voice assistant** built in Python using PyQt6.  
It includes **real-time speech recognition, wake-word detection, Murf TTS, Gemini AI replies, animated neon UI, reminders, notes, command execution**, and more — all contained inside *one single file (`app.py`)*.

---

## ✨ Features

### 🎤 Speech & AI
- Real-time speech recognition (Google STT)
- Wake word detection (“hey astra”, “ok astra”, “computer”, etc.)
- Gemini 2.5 Flash powered AI responses
- Premium-quality Murf AI TTS output
- Optional pyttsx3 fallback

### 🧠 System Features
- Command execution (Chrome, Notepad, Calculator, etc.)
- Notes system (saved to file and memory)
- Reminder system (saved to file and memory)
- Web search commands
- Logs viewer (complete command history)

### 🌈 UI Features (PyQt6)
- Neon-themed animated interface  
- Typing animation for AI messages  
- Multiple themes:
  - Neon Blue
  - Neon Pink
  - Cyber Green
  - Holographic  
- Smooth hover/press animations on buttons
- Glowing indicators for wake-word detection
- Settings panel for:
  - Typing speed  
  - Theme  
  - Volume  
  - STT engine  
  - Animations toggle  
  - Murf API key / voice ID  

---

## 🚀 Installation

### 1. Clone the repo
git clone <your-repo-link>
cd astra

shell
Copy code

### 2. Install required libraries
pip install -r requirements.txt

shell
Copy code

### 3. Create a `.env` file
GEMINI_API_KEY=your_key
MURF_API_KEY=your_key
DEEPGRAM_API_KEY=optional
OPENWEATHER_API_KEY=optional
NEWSAPI_KEY=optional

shell
Copy code

### 4. Run ASTRA
python app.py

yaml
Copy code

---

## 🛠 Requirements

- Python 3.10+
- PyQt6
- speech_recognition  
- pyaudio  
- pyttsx3  
- pydub  
- requests  
- google-generativeai  
- dotenv  

*(Install using `pip install -r requirements.txt`)*

---

## 🗂 Project Structure

📦 astra
└── app.py # Entire assistant in one file

yaml
Copy code

---

## 🖥️ Usage Examples

### Voice:
- “Hey Astra, what's the time?”
- “Open Chrome”
- “Set a reminder to study at 7”
- “Write a note about my project”
- “Search for Python tutorials”

### Text:
Type into the input bar at the bottom.

---

## 🧩 What Makes ASTRA Unique?

- Everything is **self-contained**  
- No external UI files  
- Clean UI with **neon cyber aesthetics**  
- Real AI + real TTS + real STT  
- Built for **hackathons/projects/portfolio**  

---

## 🤝 Contributing

PRs, improvements, and feature ideas are welcome!

---

## 📝 License

MIT License

---

## 🔥 Author

Built by **Kartikeya Jagadale** 
& Ayush Kalambe
Feel free to connect on LinkedIn!
