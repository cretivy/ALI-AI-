import os
import time
import subprocess
import threading
import numpy as np

# Prevent matplotlib font cache delay
os.environ["MPLBACKEND"] = "Agg"

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class GestureController:
    """Background Hand Gesture Recognition for macOS Desktop Switching"""
    def __init__(self, callback=None):
        self.running = False
        self.thread = None
        self.callback = callback
        self.last_gesture_time = 0
        self.cooldown = 1.2  # Cooldown between gestures in seconds

    def _switch_desktop(self, direction):
        """Switches macOS Desktop spaces using AppleScript key codes"""
        try:
            if direction == "left":
                # Control + Left Arrow (Previous Desktop)
                cmd = 'tell application "System Events" to key code 123 using {control down}'
                subprocess.run(["osascript", "-e", cmd], check=False)
            elif direction == "right":
                # Control + Right Arrow (Next Desktop)
                cmd = 'tell application "System Events" to key code 124 using {control down}'
                subprocess.run(["osascript", "-e", cmd], check=False)
            elif direction == "mission_control":
                # Control + Up Arrow
                cmd = 'tell application "System Events" to key code 126 using {control down}'
                subprocess.run(["osascript", "-e", cmd], check=False)
        except Exception as e:
            print(f"⚠️ Gesture AppleScript Error: {e}")

    def _loop(self):
        if not HAS_CV2:
            print("⚠️ OpenCV o'rnatilmagan. Imo-ishora (Gesture) boshqaruvi o'chirildi.")
            return

        # Open webcam using macOS native AVFoundation
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
            
        if not cap.isOpened():
            print("⚠️ Veb-kamera ochilmadi! Mac Maxfiylik sozlamalaridan kameraga ruxsat berilganini tekshiring.")
            return

        print("📸 Veb-kamera muvaffaqiyatli yoqildi va qo'lingizni kuzatmoqda!")
        print("👈 Qo'lni chapga surish (Swipe Left) -> Keyingi Desktop")
        print("👉 Qo'lni o'ngga surish (Swipe Right) -> Oldingi Desktop")

        prev_gray = None
        motion_history = []

        while self.running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            # Flip image horizontally for intuitive mirror interaction
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if prev_gray is None:
                prev_gray = gray
                continue

            # Compute frame difference to detect motion center
            frame_delta = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            now = time.time()
            large_contours = [c for c in contours if cv2.contourArea(c) > 3000]

            if large_contours:
                # Find center of main motion (hand/arm)
                c = max(large_contours, key=cv2.contourArea)
                (x, y, w, h) = cv2.boundingRect(c)
                center_x = (x + w / 2) / frame.shape[1]  # Normalized [0.0 - 1.0]

                motion_history.append((now, center_x))

                # Keep history within last 0.4 seconds
                motion_history = [m for m in motion_history if now - m[0] <= 0.4]

                if len(motion_history) >= 4 and (now - self.last_gesture_time) > self.cooldown:
                    start_x = motion_history[0][1]
                    end_x = motion_history[-1][1]
                    dx = end_x - start_x

                    # Swipe Right -> Switch Desktop Right (dx > 0.20)
                    if dx > 0.20:
                        print(f"👉 O'ngga swipe aniqlandi (dx={dx:.2f})! Desktop o'ngga surilmoqda...")
                        self._switch_desktop("right")
                        self.last_gesture_time = now
                        motion_history.clear()
                        if self.callback:
                            self.callback("swipe_right")

                    # Swipe Left -> Switch Desktop Left (dx < -0.20)
                    elif dx < -0.20:
                        print(f"👈 Chapga swipe aniqlandi (dx={dx:.2f})! Desktop chapga surilmoqda...")
                        self._switch_desktop("left")
                        self.last_gesture_time = now
                        motion_history.clear()
                        if self.callback:
                            self.callback("swipe_left")

            prev_gray = gray
            time.sleep(0.03)

        cap.release()
        print("🛑 Gesture Controller to'xtatildi. Veb-kamera o'chirildi.")

    def start(self):
        """Start gesture detection in a background daemon thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    controller = GestureController()
    controller.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()
