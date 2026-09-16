import os
import sys
import time
import threading
import webview

class JsAPI:
    def __init__(self):
        self.assistant = None

    def set_assistant(self, assistant):
        self.assistant = assistant

    def trigger_listen(self):
        """Called from JavaScript when user clicks '🎤 GAPIRISH' button"""
        if self.assistant:
            threading.Thread(target=self.assistant.listen_and_process, kwargs={'record_duration': 6}, daemon=True).start()
            return "listening_started"
        return "assistant_not_ready"

class JarvisWebUI:
    def __init__(self):
        self.window = None
        self._is_ready = False
        self.api = JsAPI()
        
        # Path to local index.html
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.html_path = os.path.join(base_dir, 'web', 'index.html')

    def start_window(self):
        """Must be called on the main thread"""
        self.window = webview.create_window(
            title="JARVIS HUD - Stark Industries",
            url=self.html_path,
            width=850,
            height=650,
            resizable=True,
            frameless=False,
            easy_drag=True,
            background_color='#040814',
            js_api=self.api
        )
        self._is_ready = True
        webview.start(debug=False)

    def set_state(self, state, transcript="", response=""):
        """Thread-safe UI state updater"""
        if not self.window:
            return
        
        # Escape string quotes for JS execution safety
        safe_transcript = transcript.replace('"', '\\"').replace('\n', ' ')
        safe_response = response.replace('"', '\\"').replace('\n', ' ')
        
        js_code = f'if (window.jarvisUI) window.jarvisUI.setState("{state}", "{safe_transcript}", "{safe_response}");'
        try:
            self.window.evaluate_js(js_code)
        except Exception:
            pass

    def set_audio_level(self, level):
        """Thread-safe audio visualizer level updater (0.0 to 1.0)"""
        if not self.window:
            return
        js_code = f'if (window.jarvisUI) window.jarvisUI.setAudioLevel({level});'
        try:
            self.window.evaluate_js(js_code)
        except Exception:
            pass

# Global Singleton UI Instance
gui = JarvisWebUI()
