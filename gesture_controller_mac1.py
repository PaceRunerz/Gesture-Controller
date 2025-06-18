import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer, QRect, QBuffer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage
from AppKit import NSPasteboard  # macOS clipboard
from io import BytesIO
import sys
import Quartz

class GestureController:
    def __init__(self):
        # MediaPipe initialization
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Gesture control parameters
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.0  # seconds
        self.is_drawing = False
        self.palm_open = False  # Track palm state for screenshot gesture
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Initialize overlay UI
        self.app = QApplication(sys.argv)
        self.overlay = OverlayWindow()
        self.overlay.show()
        
    def run(self):
        prev_time = 0
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                continue
                
            # Flip and convert frame
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe
            results = self.hands.process(frame_rgb)
            
            # Draw hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    self._detect_gestures(hand_landmarks, frame)
            
            # Calculate FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow('Gesture Controller', frame)
            self._update_overlay(frame)
            
            # Handle key presses
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()
        sys.exit(self.app.exec_())
    
    def _detect_gestures(self, landmarks, frame):
        landmarks_list = []
        for lm in landmarks.landmark:
            h, w = frame.shape[:2]
            landmarks_list.append((int(lm.x * w), int(lm.y * h)))
        
        # Check for palm open/close gesture first
        current_palm_state = self._is_palm_open(landmarks_list)
        
        # If palm was open and now is closed, take screenshot
        if self.palm_open and not current_palm_state:
            current_time = time.time()
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                self._take_active_window_screenshot()
                self.last_gesture_time = current_time
                self.overlay.show_notification("Screenshot taken")
        
        self.palm_open = current_palm_state
        
        # Other gesture detections
        if self._is_fist(landmarks_list):
            current_time = time.time()
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                pyautogui.press('space')
                self.last_gesture_time = current_time
                self.overlay.show_notification("Play/Pause")
        
        elif self._is_peace_sign(landmarks_list):
            if not self.is_drawing:
                self.is_drawing = True
                self.overlay.set_drawing_mode(True)
                self.overlay.show_notification("Drawing Mode")
        
        elif self._is_thumbs_up(landmarks_list):
            current_time = time.time()
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                pyautogui.hotkey('option', 'up')
                self.last_gesture_time = current_time
                self.overlay.show_notification("Volume Up")
        
        elif self._is_thumbs_down(landmarks_list):
            current_time = time.time()
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                pyautogui.hotkey('option', 'down')
                self.last_gesture_time = current_time
                self.overlay.show_notification("Volume Down")
    
    def _is_palm_open(self, landmarks):
        # Check if all fingers are extended (palm open)
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_mcp = [6, 10, 14, 18]   # Middle joints
        
        for tip, mcp in zip(finger_tips, finger_mcp):
            if landmarks[tip][1] > landmarks[mcp][1]:  # If tip is below mcp, finger is closed
                return False
        
        # Also check thumb (optional)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        if thumb_tip[1] > thumb_ip[1]:  # If thumb tip is below IP joint
            return False
            
        return True
    
    def _take_active_window_screenshot(self):
        # Get the active window
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
        
        active_window = None
        for window in window_list:
            if window.get('kCGWindowIsOnscreen', False) and window.get('kCGWindowOwnerName', '') != 'Window Server':
                active_window = window
                break
        
        if active_window:
            window_id = active_window['kCGWindowNumber']
            window_rect = active_window['kCGWindowBounds']
            
            # Create a screen rect
            rect = Quartz.CGRectMake(
                window_rect['X'],
                window_rect['Y'],
                window_rect['Width'],
                window_rect['Height']
            )
            
            # Create the screenshot
            image_ref = Quartz.CGWindowListCreateImage(
                rect,
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id,
                Quartz.kCGWindowImageDefault)
            
            # Convert to QPixmap
            bitmap = Quartz.CGImageGetBitmapInfo(image_ref)
            width = Quartz.CGImageGetWidth(image_ref)
            height = Quartz.CGImageGetHeight(image_ref)
            bytes_per_row = Quartz.CGImageGetBytesPerRow(image_ref)
            
            provider = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image_ref))
            buffer = Quartz.CFDataGetBytePtr(provider)
            
            # Create QImage from the buffer
            q_image = QImage(buffer, width, height, bytes_per_row, QImage.Format_ARGB32)
            screenshot = QPixmap.fromImage(q_image)
            
            # Save to clipboard
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            screenshot.save(buffer, "PNG")
            pasteboard.setData_forType_(buffer.data(), 'public.png')
            buffer.close()
            
            # Save to file
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot.save(f"window_screenshot_{timestamp}.png", "PNG")
    
    def _is_fist(self, landmarks):
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        return (np.linalg.norm(np.array(thumb_tip) - np.array(index_tip)) < 50 and
                np.linalg.norm(np.array(thumb_tip) - np.array(middle_tip)) < 50)
    
    def _is_peace_sign(self, landmarks):
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        return (index_tip[1] < landmarks[6][1] and  # Index extended
                middle_tip[1] < landmarks[10][1] and  # Middle extended
                ring_tip[1] > landmarks[14][1] and  # Ring closed
                pinky_tip[1] > landmarks[18][1])  # Pinky closed
    
    def _is_thumbs_up(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        return thumb_tip[1] < thumb_mcp[1]
    
    def _is_thumbs_down(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        return thumb_tip[1] > thumb_mcp[1]
    
    def _update_overlay(self, frame):
        h, w = frame.shape[:2]
        q_img = QImage(frame.data, w, h, QImage.Format_RGB888)
        self.overlay.update_frame(q_img)
        self.overlay.set_drawing_mode(self.is_drawing)

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Controller Overlay")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.main_widget = QLabel(self)
        self.setCentralWidget(self.main_widget)
        
        self.drawing = False
        self.last_point = None
        self.pen_color = QColor(255, 0, 0, 180)
        self.pen_width = 5
        self.image = QPixmap(2560, 1600)
        self.image.fill(Qt.transparent)
        
        self.setup_ui()
        
        self.notification_label = QLabel(self)
        self.notification_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 150); color: white; font-size: 16px;")
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.notification_label.hide()
        
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.hide_notification)
        
    def setup_ui(self):
        self.screenshot_btn = QPushButton("Screenshot", self)
        self.screenshot_btn.setGeometry(10, 10, 100, 40)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        self.draw_btn = QPushButton("Draw", self)
        self.draw_btn.setGeometry(120, 10, 100, 40)
        self.draw_btn.clicked.connect(self.toggle_drawing)
        
        self.clear_btn = QPushButton("Clear", self)
        self.clear_btn.setGeometry(230, 10, 100, 40)
        self.clear_btn.clicked.connect(self.clear_drawing)
    
    def update_frame(self, q_img):
        self.current_frame = q_img
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, 'current_frame'):
            painter.drawPixmap(0, 0, QPixmap.fromImage(self.current_frame))
        painter.drawPixmap(0, 0, self.image)
        
    def mousePressEvent(self, event):
        if self.drawing and event.button() == Qt.LeftButton:
            self.last_point = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.LeftButton and self.last_point:
            painter = QPainter(self.image)
            painter.setPen(QPen(self.pen_color, self.pen_width))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = None
            
    def toggle_drawing(self):
        self.drawing = not self.drawing
        self.draw_btn.setStyleSheet("background-color: green; color: white;" if self.drawing else "")
            
    def set_drawing_mode(self, enabled):
        self.drawing = enabled
        self.draw_btn.setStyleSheet("background-color: green; color: white;" if enabled else "")
            
    def clear_drawing(self):
        self.image.fill(Qt.transparent)
        self.update()
        
    def take_screenshot(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        painter = QPainter(screenshot)
        painter.drawPixmap(0, 0, self.image)
        painter.end()
        
        # Save to clipboard (macOS)
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        screenshot.save(buffer, "PNG")
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setData_forType_(buffer.data(), 'public.png')
        buffer.close()
        
        # Save to file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot.save(f"screenshot_{timestamp}.png", "PNG")
        
        self.show_notification("Screenshot captured!")
        
    def show_notification(self, message, duration=2000):
        self.notification_label.setText(message)
        self.notification_label.adjustSize()
        self.notification_label.move(
            self.width() // 2 - self.notification_label.width() // 2,
            self.height() - 100)
        self.notification_label.show()
        self.notification_timer.start(duration)
        
    def hide_notification(self):
        self.notification_timer.stop()
        self.notification_label.hide()

if __name__ == "__main__":
    controller = GestureController()
    controller.run()