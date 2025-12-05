import sys
import json
import base64
import io
import time
import threading
import requests
import queue
import subprocess
import platform
import datetime
import re
import os
from typing import Optional, Dict, List, Any
from collections import deque

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. .env file will not be loaded.")

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Gemini will not be available.")

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QScrollArea,
    QFrame, QDialog, QGridLayout, QSlider, QComboBox, QListWidget,
    QTabWidget, QMessageBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QThread, QPropertyAnimation,
    QEasingCurve, QRect, QPoint, QSize, pyqtProperty
)
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QLinearGradient, QPainter,
    QBrush, QPen, QRadialGradient
)

# Audio and speech imports
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Warning: speech_recognition not available")

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: pyaudio not available")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available")

try:
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available")


# ============================================================================
# CONFIGURATION - API KEYS LOADED FROM .env FILE
# ============================================================================

CONFIG = {
    "app_name": "ASTRA",
    "version": "2.0.0",
    "wake_words": ["astra", "hey astra", "ok astra", "computer"],
    "typing_speed": 30,  # milliseconds per character
    "animation_fps": 60,
    "theme": "neon_blue",

    # API KEYS FROM .env FILE
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "murf_api_key": os.getenv("MURF_API_KEY", ""),
    "deepgram_api_key": os.getenv("DEEPGRAM_API_KEY", ""),
    "openweather_api_key": os.getenv("OPENWEATHER_API_KEY", ""),
    "newsapi_key": os.getenv("NEWSAPI_KEY", ""),
    
    "murf_voice_id": "en-US-terrell",
    "murf_api_url": "https://api.murf.ai/v1/speech/generate",

    # TTS Settings - Murf only
    "use_murf_tts": True,  # Murf TTS is mandatory

    # STT Settings
    "stt_engine": "google",  # google, sphinx
    "listening_timeout": 5,
    "phrase_time_limit": 10,

    # Audio settings
    "volume": 0.8,
    "speech_rate": 150,

    # UI Settings
    "window_width": 1200,
    "window_height": 800,
    "enable_animations": True,
    "glow_intensity": 1.0,
}

# Validate API keys are loaded
if not CONFIG["gemini_api_key"]:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")
if not CONFIG["murf_api_key"]:
    print("⚠️  WARNING: MURF_API_KEY not found in .env file")

# Color themes
THEMES = {
    "neon_blue": {
        "primary": "#00FFFF",       # Neon blue for everything
        "secondary": "#00FFFF",     # Neon blue
        "accent": "#00FFFF",        # Neon blue
        "tertiary": "#00FFFF",      # Neon blue
        "quaternary": "#00FFFF",    # Neon blue
        "glow": "rgba(0, 255, 255, 0.6)",
        "background": "#0a0e27",
        "gradient_start": "#0a0e27",
        "gradient_end": "#1a1e3f",
        "chat_bg": "rgba(0, 20, 40, 0.7)",
        "input_border": "#00FFFF",  # Neon blue
        "button_border": "#00FFFF", # Neon blue
        "tab_active": "#00FFFF",    # Neon blue
        "header_color": "#00FFFF",  # Neon blue
    },
    "neon_pink": {
        "primary": "#FF00FF",
        "secondary": "#FF1493",
        "accent": "#FF69B4",
        "glow": "rgba(255, 0, 255, 0.6)",
        "background": "#1a0a1a",
        "gradient_start": "#1a0a1a",
        "gradient_end": "#3a1a3a",
    },
    "cyber_green": {
        "primary": "#00FF00",
        "secondary": "#00FF7F",
        "accent": "#7FFF00",
        "glow": "rgba(0, 255, 0, 0.6)",
        "background": "#0a1a0a",
        "gradient_start": "#0a1a0a",
        "gradient_end": "#1a3a1a",
    },
    "holographic": {
        "primary": "#00FFFF",      # Cyan - for main text/labels
        "secondary": "#FF00FF",    # Magenta - for buttons
        "accent": "#FFFF00",       # Yellow - for highlights
        "tertiary": "#00FF00",     # Green - for input fields
        "quaternary": "#FF6600",   # Orange - for status
        "glow": "rgba(0, 255, 255, 0.6)",
        "background": "#0a0a1a",
        "gradient_start": "#0a0a1a",
        "gradient_end": "#1a1a2a",
        "chat_bg": "#0d0d2b",
        "input_border": "#00FF00",
        "button_border": "#FF00FF",
        "tab_active": "#FFFF00",
        "header_color": "#FF6600",
    },
}

# In-memory data storage
MEMORY = {
    "conversation_history": [],
    "reminders": [],
    "logs": [],
    "notes": [],
    "commands_executed": 0,
}

def ask_ai(prompt):
    """
    Sends user input to Gemini AI and returns the reply text.
    Using Google Gemini API REST endpoint with key from .env file.
    """
    api_key = CONFIG.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "(Gemini API key not found. Add GEMINI_API_KEY to your .env file)"

    # Add system context for better responses
    system_prompt = """You are Astra, a helpful and friendly AI voice assistant. 
    Keep responses concise and conversational. Be helpful and informative."""
    
    full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAstra:"

    # Try using the google-generativeai library first
    if GEMINI_AVAILABLE:
        try:
            genai.configure(api_key=api_key)
            # Use gemini-2.5-flash model
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception:
            pass  # Fall through to REST API

    # Fallback to direct REST API call
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return "(No response from Gemini)"
        
        return f"(Gemini API Error: {response.status_code} - {response.text[:200]})"
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return "(Invalid Gemini API key. Please check your .env file)"
        elif "QUOTA" in error_msg.upper():
            return "(Gemini API quota exceeded. Please try again later)"
        return f"(Gemini AI Error: {error_msg})"

# ============================================================================
# SIGNAL MANAGER (Thread-safe communication)
# ============================================================================

class SignalManager(QObject):
    """Thread-safe signal emitter for cross-thread communication"""
    text_update = pyqtSignal(str, str)  # role, text
    status_update = pyqtSignal(str)
    wake_word_detected = pyqtSignal()
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    reminder_alert = pyqtSignal(str)
    typing_complete = pyqtSignal()
    ai_response_ready = pyqtSignal(str)  # AI response text for thread-safe UI update


# ============================================================================
# AUDIO & TTS ENGINE
# ============================================================================

class AudioEngine:
    """Handles all audio playback and TTS operations"""

    def __init__(self, config: Dict):
        self.config = config
        self.is_speaking = False
        self.audio_queue = queue.Queue()
        self.tts_engine = None

        # Initialize pyttsx3 as fallback TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', config.get('speech_rate', 150))
                self.tts_engine.setProperty('volume', config.get('volume', 0.8))
                print("TTS Engine (pyttsx3) initialized successfully")
            except Exception as e:
                print(f"TTS engine initialization failed: {e}")
        else:
            print("Warning: pyttsx3 not available. Install with: pip install pyttsx3")

    def speak_murf(self, text: str) -> bool:
        """Use Murf AI for TTS (premium voice) - REQUIRED"""
        if not REQUESTS_AVAILABLE:
            print("ERROR: Requests library not available for Murf TTS")
            return False

        # Get API key from config (loaded from .env)
        api_key = self.config.get('murf_api_key') or os.getenv('MURF_API_KEY')
        if not api_key:
            print("ERROR: Murf API key not found in .env file")
            return False

        try:
            # Murf API endpoint for text-to-speech
            url = "https://api.murf.ai/v1/speech/generate"
            
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Payload - request WAV format in payload, not header
            payload = {
                "voiceId": "en-US-natalie",
                "text": text,
                "format": "WAV",
                "sampleRate": 24000,
                "channelType": "MONO"
            }

            print(f"Murf TTS: Generating speech...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"Murf API status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                
                # Get audio URL from response
                audio_url = result.get('audioFile')
                
                if audio_url:
                    print(f"Murf TTS: Downloading audio...")
                    audio_response = requests.get(audio_url, timeout=30)
                    
                    if audio_response.status_code == 200 and PYDUB_AVAILABLE:
                        # Try WAV first, then MP3
                        try:
                            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_response.content))
                        except Exception:
                            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_response.content))
                        print("Murf TTS: Playing...")
                        play(audio_segment)
                        return True
                
                # Try encoded audio
                encoded_audio = result.get('encodedAudio')
                if encoded_audio and PYDUB_AVAILABLE:
                    audio_bytes = base64.b64decode(encoded_audio)
                    try:
                        audio_segment = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                    except Exception:
                        audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                    play(audio_segment)
                    return True
            
            # Handle errors
            print(f"Murf API error {response.status_code}: {response.text[:500]}")
            return False

        except Exception as e:
            print(f"Murf TTS error: {e}")
            return False

    def speak_fallback(self, text: str):
        """Fallback TTS using pyttsx3"""
        if self.tts_engine:
            try:
                self.is_speaking = True
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.is_speaking = False
                return True
            except Exception as e:
                print(f"Fallback TTS error: {e}")
                self.is_speaking = False
        return False

    def speak(self, text: str):
        """Main speak method - Uses Murf TTS only"""
        if not text or not text.strip():
            return
            
        # Clean text for TTS
        clean_text = text.strip()
        
        def _speak_thread():
            print(f"TTS: Speaking '{clean_text[:50]}...'")
            
            # Use Murf TTS only
            success = self.speak_murf(clean_text)
            if success:
                print("TTS: Murf succeeded")
            else:
                print("TTS: Murf failed - check API key and connection")

        # Run in separate thread to not block UI
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()


# ============================================================================
# SPEECH RECOGNITION ENGINE
# ============================================================================

class SpeechEngine:
    """Handles speech recognition and wake word detection"""

    def __init__(self, config: Dict, signals: SignalManager):
        self.config = config
        self.signals = signals
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.microphone = sr.Microphone() if SPEECH_AVAILABLE else None
        self.is_listening = False
        self.wake_word_active = True

        # Adjust for ambient noise
        if self.recognizer and self.microphone:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen_once(self) -> Optional[str]:
        """Listen for a single phrase"""
        if not self.recognizer or not self.microphone:
            return None

        try:
            with self.microphone as source:
                self.signals.listening_started.emit()
                audio = self.recognizer.listen(
                    source,
                    timeout=self.config['listening_timeout'],
                    phrase_time_limit=self.config['phrase_time_limit']
                )
                self.signals.listening_stopped.emit()

                # Recognize speech
                text = self.recognizer.recognize_google(audio)
                return text.lower()

        except sr.WaitTimeoutError:
            self.signals.listening_stopped.emit()
            return None
        except sr.UnknownValueError:
            self.signals.listening_stopped.emit()
            return None
        except sr.RequestError as e:
            self.signals.error_occurred.emit(f"Speech recognition error: {e}")
            self.signals.listening_stopped.emit()
            return None
        except Exception as e:
            self.signals.error_occurred.emit(f"Unexpected error: {e}")
            self.signals.listening_stopped.emit()
            return None

    def check_wake_word(self, text: str) -> bool:
        """Check if text contains wake word"""
        text_lower = text.lower()
        for wake_word in self.config['wake_words']:
            if wake_word in text_lower:
                return True
        return False

    def continuous_listen(self):
        """Continuous listening loop for wake word detection"""
        self.is_listening = True

        while self.is_listening:
            text = self.listen_once()

            if text:
                self.signals.text_update.emit("user", text)

                # Check for wake word
                if self.wake_word_active and self.check_wake_word(text):
                    self.signals.wake_word_detected.emit()
                    self.signals.status_update.emit("Wake word detected!")

            time.sleep(0.1)  # Small delay to prevent CPU overuse

    def stop_listening(self):
        """Stop the listening loop"""
        self.is_listening = False


# ============================================================================
# COMMAND PROCESSOR
# ============================================================================

class CommandProcessor:
    """Processes voice commands and executes actions"""

    def __init__(self, config: Dict, signals: SignalManager, audio_engine: AudioEngine):
        self.config = config
        self.signals = signals
        self.audio = audio_engine
        self.os_name = platform.system()

    def process_command(self, text: str) -> str:
        """Process command and return response"""
        text_lower = text.lower()

        # Time commands
        if any(word in text_lower for word in ["time", "clock"]):
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            response = f"The current time is {current_time}"
            MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
            return response

        # Date commands
        if any(word in text_lower for word in ["date", "today"]):
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            response = f"Today is {current_date}"
            MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
            return response

        # Open applications
        if "open" in text_lower:
            app = self._extract_app_name(text_lower)
            if app:
                success = self._open_application(app)
                response = f"Opening {app}" if success else f"Could not open {app}"
                MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
                return response

        # Reminder commands
        if "remind" in text_lower or "reminder" in text_lower:
            reminder_text = self._extract_reminder(text)
            if reminder_text:
                MEMORY['reminders'].append({
                    "text": reminder_text,
                    "time": datetime.datetime.now().isoformat(),
                    "status": "active"
                })
                
                # Save to file in same directory
                reminders_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astra_reminders.txt")
                try:
                    with open(reminders_file, "a", encoding="utf-8") as f:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {reminder_text}\n")
                except Exception:
                    pass
                
                response = f"Reminder set: {reminder_text}"
                MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
                return response

        # Note commands
        if "note" in text_lower or "write" in text_lower:
            note_text = self._extract_note(text)
            if note_text:
                # Save to memory
                MEMORY['notes'].append({
                    "text": note_text,
                    "time": datetime.datetime.now().isoformat()
                })
                
                # Save to file in same folder
                notes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astra_notes.txt")
                try:
                    with open(notes_file, "a", encoding="utf-8") as f:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {note_text}\n")
                    response = f"Note saved: {note_text}"
                except Exception as e:
                    response = f"Note saved to memory but file save failed: {e}"
                
                MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
                return response

        # Search commands
        if "search" in text_lower or "google" in text_lower:
            query = self._extract_search_query(text)
            if query:
                self._search_web(query)
                response = f"Searching for {query}"
                MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
                return response

        # Default response
        response = "I'm processing your request. How else can I help you?"
        MEMORY['logs'].append({"time": datetime.datetime.now().isoformat(), "command": text, "response": response})
        return response

    def _extract_app_name(self, text: str) -> Optional[str]:
        """Extract application name from command"""
        # Extended list of apps with aliases
        app_aliases = {
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox", "mozilla"],
            "edge": ["edge", "microsoft edge"],
            "notepad": ["notepad", "text editor"],
            "calculator": ["calculator", "calc"],
            "terminal": ["terminal", "command prompt", "cmd", "powershell"],
            "explorer": ["explorer", "file explorer", "files", "folder"],
            "vscode": ["vscode", "vs code", "visual studio code", "code editor"],
            "spotify": ["spotify", "music"],
            "settings": ["settings", "control panel"],
            "mail": ["mail", "email", "outlook"],
            "browser": ["browser", "internet"],
            "word": ["word", "microsoft word"],
            "excel": ["excel", "microsoft excel"],
            "powerpoint": ["powerpoint", "ppt"],
            "discord": ["discord"],
            "slack": ["slack"],
            "teams": ["teams", "microsoft teams"],
            "zoom": ["zoom"],
            "paint": ["paint", "mspaint"],
            "photos": ["photos"],
            "camera": ["camera"],
            "store": ["store", "microsoft store"],
        }
        
        for app, aliases in app_aliases.items():
            for alias in aliases:
                if alias in text:
                    return app
        return None

    def _open_application(self, app: str) -> bool:
        """Open application based on OS"""
        try:
            if self.os_name == "Windows":
                # Windows app paths and commands
                app_map = {
                    "chrome": "start chrome",
                    "firefox": "start firefox",
                    "edge": "start msedge",
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "browser": "start chrome",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "terminal": "start wt",  # Windows Terminal
                    "vscode": "code",
                    "spotify": "start spotify:",
                    "settings": "start ms-settings:",
                    "mail": "start outlookmail:",
                    "word": "start winword",
                    "excel": "start excel",
                    "powerpoint": "start powerpnt",
                    "discord": "start discord:",
                    "slack": "start slack:",
                    "teams": "start msteams:",
                    "zoom": "start zoommtg:",
                    "paint": "mspaint.exe",
                    "photos": "start ms-photos:",
                    "camera": "start microsoft.windows.camera:",
                    "store": "start ms-windows-store:",
                }
                cmd = app_map.get(app, f"start {app}")
                print(f"Opening app with command: {cmd}")
                subprocess.Popen(cmd, shell=True)
                return True

            elif self.os_name == "Darwin":  # macOS
                app_map = {
                    "chrome": "Google Chrome",
                    "firefox": "Firefox",
                    "terminal": "Terminal",
                    "music": "Music",
                    "browser": "Safari",
                }
                app_name = app_map.get(app, app)
                subprocess.Popen(["open", "-a", app_name])
                return True

            elif self.os_name == "Linux":
                app_map = {
                    "chrome": "google-chrome",
                    "firefox": "firefox",
                    "terminal": "gnome-terminal",
                    "browser": "firefox",
                }
                cmd = app_map.get(app, app)
                subprocess.Popen(cmd, shell=True)
                return True

        except Exception as e:
            print(f"Error opening app: {e}")
            return False

        return False

    def _extract_reminder(self, text: str) -> Optional[str]:
        """Extract reminder text from command"""
        patterns = [
            r"remind me to (.+)",
            r"reminder to (.+)",
            r"set a reminder (.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_note(self, text: str) -> Optional[str]:
        """Extract note text from command"""
        patterns = [
            r"write (?:a )?note (.+)",
            r"note (.+)",
            r"take (?:a )?note (.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract search query from command"""
        patterns = [
            r"search for (.+)",
            r"google (.+)",
            r"search (.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _search_web(self, query: str):
        """Open web browser with search query"""
        import webbrowser
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)


# ============================================================================
# ANIMATED WIDGETS
# ============================================================================

class GlowingLabel(QLabel):
    """Label with animated glow effect"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.glow_intensity = 0.0
        self.glow_direction = 1

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_glow)
        self.animation_timer.start(50)

    def update_glow(self):
        """Update glow animation"""
        self.glow_intensity += 0.05 * self.glow_direction
        if self.glow_intensity >= 1.0:
            self.glow_direction = -1
        elif self.glow_intensity <= 0.0:
            self.glow_direction = 1

        self.update()


class NeonButton(QPushButton):
    """Button with neon glow effect"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.is_glowing = False

    def set_glow(self, enabled: bool):
        """Enable/disable glow effect"""
        self.is_glowing = enabled
        self.update()


class TypingTextEdit(QTextEdit):
    """Text edit with typing animation effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.typing_queue = deque()
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._type_next_char)
        self.is_typing = False
        self.typing_speed = 30  # ms per character
        self.on_complete_callback = None

    def type_text(self, text: str, callback=None):
        """Add text to typing queue"""
        self.on_complete_callback = callback
        for char in text:
            self.typing_queue.append(char)

        if not self.is_typing:
            self.is_typing = True
            self.typing_timer.start(self.typing_speed)

    def _type_next_char(self):
        """Type next character"""
        if self.typing_queue:
            char = self.typing_queue.popleft()
            self.insertPlainText(char)
            self.ensureCursorVisible()
        else:
            self.is_typing = False
            self.typing_timer.stop()
            if self.on_complete_callback:
                self.on_complete_callback()
                self.on_complete_callback = None

    def set_typing_speed(self, speed: int):
        """Set typing speed in ms"""
        self.typing_speed = speed


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class AstraWindow(QMainWindow):
    """Main Astra application window"""

    def __init__(self):
        super().__init__()
        self.config = CONFIG
        self.current_theme = THEMES[self.config['theme']]

        # Initialize engines
        self.signals = SignalManager()
        self.audio_engine = AudioEngine(self.config)
        self.speech_engine = SpeechEngine(self.config, self.signals) if SPEECH_AVAILABLE else None
        self.command_processor = CommandProcessor(self.config, self.signals, self.audio_engine)

        # Connect signals
        self.signals.text_update.connect(self.on_text_update)
        self.signals.status_update.connect(self.on_status_update)
        self.signals.wake_word_detected.connect(self.on_wake_word)
        self.signals.listening_started.connect(self.on_listening_started)
        self.signals.listening_stopped.connect(self.on_listening_stopped)
        self.signals.error_occurred.connect(self.on_error)
        self.signals.ai_response_ready.connect(self.on_ai_response)

        # UI state
        self.speak_mode = False
        self.is_listening = False

        # Setup UI
        self.init_ui()
        self.apply_theme()

        # Start background animations
        self.start_animations()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(f"{self.config['app_name']} - Voice Assistant")
        self.setGeometry(100, 100, self.config['window_width'], self.config['window_height'])

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Content area
        content = self.create_content()
        main_layout.addWidget(content, stretch=1)

        # Footer controls
        footer = self.create_footer()
        main_layout.addWidget(footer)

    def create_header(self) -> QWidget:
        """Create header with logo and status"""
        header = QFrame()
        header.setFixedHeight(100)
        layout = QHBoxLayout()
        header.setLayout(layout)

        # Logo
        self.logo_label = QLabel("⚡ ASTRA")
        self.logo_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        layout.addWidget(self.logo_label)

        layout.addStretch()

        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.status_label)

        # Wake word indicator
        self.wake_indicator = QLabel("●")
        self.wake_indicator.setFont(QFont("Arial", 24))
        layout.addWidget(self.wake_indicator)

        return header

    def create_content(self) -> QWidget:
        """Create main content area"""
        content = QFrame()
        layout = QVBoxLayout()
        content.setLayout(layout)

        # Conversation display
        conv_label = QLabel("Conversation")
        conv_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(conv_label)

        self.conversation_display = TypingTextEdit()
        self.conversation_display.setFont(QFont("Consolas", 12))
        self.conversation_display.setMinimumHeight(400)
        layout.addWidget(self.conversation_display)

        # Input area
        input_layout = QHBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a command or use voice...")
        self.text_input.setFont(QFont("Arial", 12))
        self.text_input.returnPressed.connect(self.on_text_submit)
        input_layout.addWidget(self.text_input)

        self.send_button = NeonButton("Send")
        self.send_button.clicked.connect(self.on_text_submit)
        self.send_button.setFixedWidth(100)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        return content

    def create_footer(self) -> QWidget:
        """Create footer with controls"""
        footer = QFrame()
        footer.setFixedHeight(80)
        layout = QHBoxLayout()
        footer.setLayout(layout)

        # Listen button
        self.listen_button = NeonButton("🎤 Start Listening")
        self.listen_button.clicked.connect(self.toggle_listening)
        self.listen_button.setFixedSize(180, 50)
        layout.addWidget(self.listen_button)

        # Speak mode toggle
        self.speak_button = NeonButton("🔊 Speak Mode: OFF")
        self.speak_button.clicked.connect(self.toggle_speak_mode)
        self.speak_button.setFixedSize(180, 50)
        layout.addWidget(self.speak_button)

        layout.addStretch()

        # Additional buttons
        self.reminders_button = NeonButton("⏰ Reminders")
        self.reminders_button.clicked.connect(self.show_reminders)
        self.reminders_button.setFixedSize(140, 50)
        layout.addWidget(self.reminders_button)

        self.logs_button = NeonButton("📋 Logs")
        self.logs_button.clicked.connect(self.show_logs)
        self.logs_button.setFixedSize(140, 50)
        layout.addWidget(self.logs_button)

        self.settings_button = NeonButton("⚙️ Settings")
        self.settings_button.clicked.connect(self.show_settings)
        self.settings_button.setFixedSize(140, 50)
        layout.addWidget(self.settings_button)

        return footer

    def apply_theme(self):
        """Apply current theme to UI with smooth animations and hover effects"""
        theme = self.current_theme
        
        # Get theme-specific colors or fallback to primary
        input_border = theme.get('input_border', theme['primary'])
        button_border = theme.get('button_border', theme['secondary'])
        tab_active = theme.get('tab_active', theme['accent'])
        header_color = theme.get('header_color', theme['primary'])
        chat_bg = theme.get('chat_bg', 'rgba(0, 0, 0, 0.5)')
        tertiary = theme.get('tertiary', theme['primary'])

        # Main window style with smooth animations
        self.setStyleSheet(f"""
            /* Main Window */
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']},
                    stop:0.5 #1a0a2a,
                    stop:1 {theme['gradient_end']});
            }}
            
            /* Frames */
            QFrame {{
                background: transparent;
                border: 2px solid {theme['primary']};
                border-radius: 10px;
                padding: 10px;
            }}
            
            /* Labels */
            QLabel {{
                color: {theme['primary']};
                background: transparent;
            }}
            
            /* Text Edit (Chat) */
            QTextEdit {{
                background-color: {chat_bg};
                color: {tertiary};
                border: 2px solid {theme['primary']};
                border-radius: 8px;
                padding: 10px;
                selection-background-color: {theme['secondary']};
            }}
            
            /* Line Edit (Input) with hover */
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0.5);
                color: {tertiary};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:hover {{
                border: 3px solid {theme['accent']};
                background-color: rgba(0, 0, 0, 0.7);
            }}
            QLineEdit:focus {{
                border: 3px solid {theme['primary']};
                background-color: rgba(0, 0, 0, 0.8);
            }}
            
            /* Buttons with smooth hover effects */
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.7);
                color: {theme['secondary']};
                border: 2px solid {button_border};
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {theme['secondary']};
                color: {theme['background']};
                border: 3px solid {theme['accent']};
                padding: 9px 14px;
            }}
            QPushButton:pressed {{
                background-color: {theme['accent']};
                color: {theme['background']};
                border: 3px solid {theme['primary']};
                padding: 11px 16px;
            }}
            QPushButton:disabled {{
                background-color: rgba(50, 50, 50, 0.5);
                color: rgba(100, 100, 100, 0.7);
                border: 2px solid rgba(100, 100, 100, 0.5);
            }}
            
            /* List Widget with hover */
            QListWidget {{
                background-color: rgba(0, 0, 0, 0.5);
                color: {tertiary};
                border: 2px solid {theme['accent']};
                border-radius: 8px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {theme['secondary']};
                color: {theme['background']};
            }}
            
            /* ComboBox with hover */
            QComboBox {{
                background-color: rgba(0, 0, 0, 0.5);
                color: {theme['accent']};
                border: 2px solid {theme['accent']};
                border-radius: 8px;
                padding: 5px 10px;
                min-height: 25px;
            }}
            QComboBox:hover {{
                border: 3px solid {theme['primary']};
                background-color: rgba(0, 0, 0, 0.7);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['background']};
                color: {theme['primary']};
                border: 2px solid {theme['primary']};
                selection-background-color: {theme['secondary']};
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 2px solid {theme['primary']};
                border-radius: 8px;
                background: rgba(0, 0, 0, 0.3);
            }}
            QTabBar::tab {{
                background: rgba(0, 0, 0, 0.5);
                color: {theme['primary']};
                border: 2px solid {theme['secondary']};
                padding: 10px 20px;
                margin: 2px;
                border-radius: 5px;
            }}
            QTabBar::tab:hover {{
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid {theme['accent']};
            }}
            QTabBar::tab:selected {{
                background: {tab_active};
                color: {theme['background']};
                border: 2px solid {tab_active};
            }}
            
            /* Slider with hover */
            QSlider::groove:horizontal {{
                background: rgba(0, 0, 0, 0.5);
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {theme['primary']};
                width: 22px;
                height: 22px;
                margin: -7px 0;
                border-radius: 11px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme['secondary']};
                border-radius: 4px;
            }}
            
            /* SpinBox with hover */
            QSpinBox {{
                background-color: rgba(0, 0, 0, 0.5);
                color: {theme['accent']};
                border: 2px solid {theme['accent']};
                border-radius: 5px;
                padding: 5px;
                min-height: 25px;
            }}
            QSpinBox:hover {{
                border: 3px solid {theme['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {theme['secondary']};
                border-radius: 3px;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: {theme['primary']};
            }}
            
            /* Scrollbar styling */
            QScrollBar:vertical {{
                background: rgba(0, 0, 0, 0.3);
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['secondary']};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: rgba(0, 0, 0, 0.3);
                height: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme['secondary']};
                border-radius: 6px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme['primary']};
            }}
            
            /* CheckBox with hover */
            QCheckBox {{
                color: {theme['primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {theme['secondary']};
                border-radius: 4px;
                background: rgba(0, 0, 0, 0.5);
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {theme['primary']};
            }}
            QCheckBox::indicator:checked {{
                background: {theme['accent']};
                border: 2px solid {theme['accent']};
            }}
        """)

        # Update logo with header color
        self.logo_label.setStyleSheet(f"""
            QLabel {{
                color: {header_color};
                font-weight: bold;
            }}
        """)
        
        # Update status label
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {theme['accent']};
            }}
        """)

    def start_animations(self):
        """Start background animations"""
        # Wake indicator pulse
        self.wake_timer = QTimer()
        self.wake_timer.timeout.connect(self.animate_wake_indicator)
        self.wake_timer.start(500)

    def animate_wake_indicator(self):
        """Animate wake word indicator"""
        if self.is_listening:
            current = self.wake_indicator.styleSheet()
            if "font-size: 28px" in current:
                self.wake_indicator.setStyleSheet(f"color: {self.current_theme['primary']}; font-size: 24px;")
            else:
                self.wake_indicator.setStyleSheet(f"color: {self.current_theme['accent']}; font-size: 28px;")

    def toggle_listening(self):
        """Toggle voice listening"""
        if not SPEECH_AVAILABLE:
            QMessageBox.warning(self, "Error", "Speech recognition not available. Please install speech_recognition.")
            return

        if not self.is_listening:
            self.is_listening = True
            self.listen_button.setText("🎤 Stop Listening")
            self.status_label.setText("Listening...")

            # Start listening in background thread
            listen_thread = threading.Thread(
                target=self.speech_engine.continuous_listen,
                daemon=True
            )
            listen_thread.start()
        else:
            self.is_listening = False
            self.listen_button.setText("🎤 Start Listening")
            self.status_label.setText("Ready")

            if self.speech_engine:
                self.speech_engine.stop_listening()

    def toggle_speak_mode(self):
        """Toggle speak mode"""
        self.speak_mode = not self.speak_mode
        if self.speak_mode:
            self.speak_button.setText("🔊 Speak Mode: ON")
        else:
            self.speak_button.setText("🔊 Speak Mode: OFF")

    def on_text_submit(self):
        """Handle text input submission"""
        text = self.text_input.text().strip()
        if not text:
            return

        self.text_input.clear()
        self.process_user_input(text)

    def process_user_input(self, text: str):
        """Process user input and generate response"""

        # Display user input
        self.conversation_display.append(f"\n{'='*60}\n")
        self.conversation_display.append(f"You said: {text}\n")

        # First try to process it as a command
        response = self.command_processor.process_command(text)

        # If the response is a default placeholder, treat it as an AI query
        if response.strip() in [
            "I'm processing your request. How else can I help you?",
            "",
            None
        ]:
            self.conversation_display.append("Astra: (Thinking...)\n")

            # Ask AI in background thread so UI doesn't freeze
            def fetch_ai():
                try:
                    ai_reply = ask_ai(text)
                except Exception as e:
                    ai_reply = f"(AI Error: {str(e)})"

                # Emit signal to update UI from main thread (thread-safe)
                self.signals.ai_response_ready.emit(ai_reply)

            threading.Thread(target=fetch_ai, daemon=True).start()
            MEMORY['commands_executed'] += 1
            return

        # If it WAS a command: display normal response
        self.conversation_display.append("Astra: ")
        self.conversation_display.type_text(response + "\n")

        # Speak command response if mode enabled
        if self.speak_mode:
            self.audio_engine.speak(response)

        MEMORY['commands_executed'] += 1

    def on_text_update(self, role: str, text: str):
        """Handle text update signal"""
        if role == "user":
            self.process_user_input(text)

    def on_status_update(self, status: str):
        """Handle status update signal"""
        self.status_label.setText(status)

    def on_wake_word(self):
        """Handle wake word detection"""
        self.wake_indicator.setStyleSheet(f"color: {self.current_theme['accent']}; font-size: 32px;")
        # Reset after delay
        QTimer.singleShot(1000, lambda: self.wake_indicator.setStyleSheet(
            f"color: {self.current_theme['primary']}; font-size: 24px;"
        ))

    def on_listening_started(self):
        """Handle listening started"""
        pass

    def on_listening_stopped(self):
        """Handle listening stopped"""
        pass

    def on_error(self, error: str):
        """Handle error"""
        QMessageBox.warning(self, "Error", error)

    def on_ai_response(self, ai_reply: str):
        """Handle AI response from background thread (thread-safe UI update)"""
        self.conversation_display.append("Astra: ")
        self.conversation_display.type_text(ai_reply + "\n")

        # Speak response if speak mode is ON
        if self.speak_mode:
            self.audio_engine.speak(ai_reply)

    def show_reminders(self):
        """Show reminders dialog"""
        dialog = RemindersDialog(self)
        dialog.exec()

    def show_logs(self):
        """Show logs dialog"""
        dialog = LogsDialog(self)
        dialog.exec()

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.config, self.current_theme)
        if dialog.exec():
            # Apply new settings
            new_config = dialog.get_config()
            self.config.update(new_config)

            # Change theme if needed
            if dialog.theme_changed:
                self.current_theme = THEMES[self.config['theme']]
                self.apply_theme()

            # Update typing speed
            self.conversation_display.set_typing_speed(self.config['typing_speed'])


# ============================================================================
# DIALOG WINDOWS
# ============================================================================

class RemindersDialog(QDialog):
    """Reminders management dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reminders")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Your Reminders")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Reminders list
        self.reminders_list = QListWidget()
        self.load_reminders()
        layout.addWidget(self.reminders_list)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_reminders)
        button_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_reminders)
        button_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_reminders(self):
        """Load reminders from memory"""
        self.reminders_list.clear()
        for reminder in MEMORY['reminders']:
            time_str = reminder['time'][:19]  # Format timestamp
            text = reminder['text']
            status = reminder['status']
            self.reminders_list.addItem(f"[{status}] {time_str} - {text}")

    def clear_reminders(self):
        """Clear all reminders"""
        MEMORY['reminders'].clear()
        self.load_reminders()


class LogsDialog(QDialog):
    """Logs viewer dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Logs")
        self.setModal(True)
        self.setMinimumSize(800, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Command Execution Logs")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Stats
        stats = QLabel(f"Total commands: {MEMORY['commands_executed']}")
        stats.setFont(QFont("Arial", 12))
        layout.addWidget(stats)

        # Logs display
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Consolas", 10))
        self.load_logs()
        layout.addWidget(self.logs_display)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_logs)
        button_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_logs(self):
        """Load logs from memory"""
        self.logs_display.clear()
        for log in MEMORY['logs']:
            time_str = log['time'][:19]
            command = log['command']
            response = log['response']
            self.logs_display.append(f"[{time_str}]")
            self.logs_display.append(f"  Command: {command}")
            self.logs_display.append(f"  Response: {response}")
            self.logs_display.append("-" * 80)

    def clear_logs(self):
        """Clear all logs"""
        MEMORY['logs'].clear()
        self.load_logs()


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    def __init__(self, parent=None, config=None, theme=None):
        super().__init__(parent)
        self.config = config or {}
        self.theme = theme or {}
        self.theme_changed = False

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()

        # General tab
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")

        # Voice tab
        voice_tab = self.create_voice_tab()
        tabs.addTab(voice_tab, "Voice")

        # API Keys tab
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API Keys")

        # Appearance tab
        appearance_tab = self.create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        row = 0

        # App name
        layout.addWidget(QLabel("Application Name:"), row, 0)
        self.app_name_input = QLineEdit(self.config.get('app_name', 'ASTRA'))
        layout.addWidget(self.app_name_input, row, 1)
        row += 1

        # Wake words
        layout.addWidget(QLabel("Wake Words (comma-separated):"), row, 0)
        wake_words_str = ", ".join(self.config.get('wake_words', []))
        self.wake_words_input = QLineEdit(wake_words_str)
        layout.addWidget(self.wake_words_input, row, 1)
        row += 1

        # Animations
        layout.addWidget(QLabel("Enable Animations:"), row, 0)
        self.animations_checkbox = QCheckBox()
        self.animations_checkbox.setChecked(self.config.get('enable_animations', True))
        layout.addWidget(self.animations_checkbox, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return widget

    def create_voice_tab(self) -> QWidget:
        """Create voice settings tab"""
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        row = 0

        # STT Engine
        layout.addWidget(QLabel("Speech Recognition Engine:"), row, 0)
        self.stt_combo = QComboBox()
        self.stt_combo.addItems(["google", "sphinx"])
        self.stt_combo.setCurrentText(self.config.get('stt_engine', 'google'))
        layout.addWidget(self.stt_combo, row, 1)
        row += 1

        # Volume
        layout.addWidget(QLabel("Volume:"), row, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.config.get('volume', 0.8) * 100))
        layout.addWidget(self.volume_slider, row, 1)
        row += 1

        # Speech rate
        layout.addWidget(QLabel("Speech Rate:"), row, 0)
        self.rate_spinner = QSpinBox()
        self.rate_spinner.setMinimum(50)
        self.rate_spinner.setMaximum(300)
        self.rate_spinner.setValue(self.config.get('speech_rate', 150))
        layout.addWidget(self.rate_spinner, row, 1)
        row += 1

        # Listening timeout
        layout.addWidget(QLabel("Listening Timeout (seconds):"), row, 0)
        self.timeout_spinner = QSpinBox()
        self.timeout_spinner.setMinimum(1)
        self.timeout_spinner.setMaximum(30)
        self.timeout_spinner.setValue(self.config.get('listening_timeout', 5))
        layout.addWidget(self.timeout_spinner, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return widget

    def create_api_tab(self) -> QWidget:
        """Create API keys tab"""
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        row = 0

        # Murf API Key
        layout.addWidget(QLabel("Murf AI API Key:"), row, 0)
        self.murf_key_input = QLineEdit(self.config.get('murf_api_key', ''))
        self.murf_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.murf_key_input, row, 1)
        row += 1

        # Show key button
        show_key_btn = QPushButton("Show/Hide Key")
        show_key_btn.clicked.connect(self.toggle_key_visibility)
        layout.addWidget(show_key_btn, row, 1)
        row += 1

        # Murf Voice ID
        layout.addWidget(QLabel("Murf Voice ID:"), row, 0)
        self.murf_voice_input = QLineEdit(self.config.get('murf_voice_id', 'en-US-falcon'))
        layout.addWidget(self.murf_voice_input, row, 1)
        row += 1

        # Info label
        info = QLabel("Note: API keys are stored in-memory only")
        info.setStyleSheet("color: yellow; font-size: 10px;")
        layout.addWidget(info, row, 0, 1, 2)
        row += 1

        layout.setRowStretch(row, 1)
        return widget

    def create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        row = 0

        # Theme selection
        layout.addWidget(QLabel("Color Theme:"), row, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.config.get('theme', 'neon_blue'))
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        layout.addWidget(self.theme_combo, row, 1)
        row += 1

        # Typing speed
        layout.addWidget(QLabel("Typing Speed (ms per char):"), row, 0)
        self.typing_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.typing_speed_slider.setMinimum(10)
        self.typing_speed_slider.setMaximum(200)
        self.typing_speed_slider.setValue(self.config.get('typing_speed', 30))
        layout.addWidget(self.typing_speed_slider, row, 1)
        row += 1

        # Glow intensity
        layout.addWidget(QLabel("Glow Intensity:"), row, 0)
        self.glow_slider = QSlider(Qt.Orientation.Horizontal)
        self.glow_slider.setMinimum(0)
        self.glow_slider.setMaximum(100)
        self.glow_slider.setValue(int(self.config.get('glow_intensity', 1.0) * 100))
        layout.addWidget(self.glow_slider, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return widget

    def toggle_key_visibility(self):
        """Toggle API key visibility"""
        if self.murf_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.murf_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.murf_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self.theme_changed = True

    def save_settings(self):
        """Save settings and close"""
        self.config['app_name'] = self.app_name_input.text()
        self.config['wake_words'] = [w.strip() for w in self.wake_words_input.text().split(',')]
        self.config['enable_animations'] = self.animations_checkbox.isChecked()
        self.config['stt_engine'] = self.stt_combo.currentText()
        self.config['volume'] = self.volume_slider.value() / 100.0
        self.config['speech_rate'] = self.rate_spinner.value()
        self.config['listening_timeout'] = self.timeout_spinner.value()
        self.config['murf_api_key'] = self.murf_key_input.text()
        self.config['murf_voice_id'] = self.murf_voice_input.text()
        self.config['theme'] = self.theme_combo.currentText()
        self.config['typing_speed'] = self.typing_speed_slider.value()
        self.config['glow_intensity'] = self.glow_slider.value() / 100.0

        self.accept()

    def get_config(self) -> Dict:
        """Get updated configuration"""
        return self.config


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("ASTRA")
    app.setOrganizationName("VoiceAI")
    app.setApplicationVersion("2.0.0")

    # Create and show main window
    window = AstraWindow()
    window.show()

    # Display welcome message
    welcome = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║⚡ ASTRA - Advanced Speech-based Total Response Assistant ⚡ ║
║                                                              ║
║   Welcome! I'm ready to assist you!!                         ║
║                                                              ║
║   Available Commands:                                        ║
║   • "What's the time?"                                       ║
║   • "Open Chrome"                                            ║
║   • "Set a reminder to..."                                   ║
║   • "Search for..."                                          ║
║   • "Write a note..."                                        ║
║                                                              ║
║   Enable listening to use wake words like "Hey Astra"        ║
║   Toggle Speak Mode for voice responses                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    window.conversation_display.insertPlainText(welcome)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":

    main()
