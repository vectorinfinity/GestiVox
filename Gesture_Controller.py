import cv2
import mediapipe as mp
import pyautogui
import math
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google.protobuf.json_format import MessageToDict
import screen_brightness_control as sbcontrol
from mediapipe.python.solutions import drawing_utils as mp_drawing
from mediapipe.python.solutions import hands as mp_hands

# Configuration
pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16    
    SHAKA = 17  # NEW: Thumb (16) + Pinky (1) for Brightness
    L_SIGN = 24 # Volume Control
    PALM = 31
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36

class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label
    
    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_dist(self, point):
        """Calculates Euclidean distance between two landmarks."""
        p1 = self.hand_result.landmark[point[0]]
        p2 = self.hand_result.landmark[point[1]]
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def set_finger_state(self):
        """Determines which fingers are open based purely on Y-coordinates."""
        if not self.hand_result:
            return

        self.finger = 0
        
        # Check thumb (Horizontal distance check)
        thumb_tip = self.hand_result.landmark[4]
        index_base = self.hand_result.landmark[5]
        if abs(thumb_tip.x - index_base.x) > 0.05: 
            self.finger |= Gest.THUMB

        # Finger tip and PIP joint landmarks [Tip, PIP]
        points = [[8, 6], [12, 10], [16, 14], [20, 18]]

        for idx, point in enumerate(points):
            # If the Tip is higher up on the screen than the PIP joint, it is open.
            if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
                self.finger |= (1 << (3 - idx))

    def get_gesture(self):
        if not self.hand_result:
            return Gest.PALM

        current_gesture = Gest.PALM
        
        # 1. Check for exact full-hand shapes FIRST
        if self.finger == Gest.L_SIGN:
            current_gesture = Gest.L_SIGN
        elif self.finger == Gest.SHAKA:
            current_gesture = Gest.SHAKA
        elif self.finger == Gest.PALM:
            current_gesture = Gest.PALM  # All 5 fingers open (Stops actions)
        else:
            # 2. Mask out the thumb state for the remaining gestures
            fingers_only = self.finger & 15 
            
            if fingers_only == Gest.FIRST2:
                current_gesture = Gest.V_GEST # Move Mouse
            elif fingers_only == Gest.INDEX:
                current_gesture = Gest.INDEX  # Left Click
            elif fingers_only == Gest.MID:
                current_gesture = Gest.MID    # Double Click
            elif fingers_only == Gest.PINKY:
                current_gesture = Gest.PINKY  # Right Click
            elif fingers_only == Gest.LAST4:
                current_gesture = Gest.LAST4  # Scroll Mode
            elif fingers_only == 0:
                current_gesture = Gest.FIST   # Drag Mouse
            else:
                current_gesture = self.finger
        
        # Debounce logic to prevent flickering gestures
        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
            self.prev_gesture = current_gesture

        if self.frame_count > 3: 
            self.ori_gesture = current_gesture
            
        return self.ori_gesture

class Controller:
    prev_hand = None
    flag = False # For Click-Ready state
    drag_flag = False # NEW: Tracks if we are currently holding an item
    scroll_prev_y = None 
    scroll_prev_x = None # NEW: Tracks X movement for sideways scrolling
    
    # Initialize Windows Audio Control
    devices = AudioUtilities.GetSpeakers()
    try:
        volume = devices.EndpointVolume
    except AttributeError:
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
    volRange = volume.GetVolumeRange()
    minVol = volRange[0]
    maxVol = volRange[1]

    @staticmethod
    def interp(val, in_min, in_max, out_min, out_max):
        """Custom math interpolation for mapping ranges"""
        return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    @staticmethod
    def get_position(hand_result):
        """Maps hand landmarks to screen coordinates with smoothing."""
        x = hand_result.landmark[9].x
        y = hand_result.landmark[9].y
        
        sw, sh = pyautogui.size()
        target_x, target_y = int(x * sw), int(y * sh)
        
        if Controller.prev_hand is None:
            Controller.prev_hand = (target_x, target_y)
        
        damping = 0.25 
        
        smooth_x = Controller.prev_hand[0] + (target_x - Controller.prev_hand[0]) * damping
        smooth_y = Controller.prev_hand[1] + (target_y - Controller.prev_hand[1]) * damping
        
        Controller.prev_hand = (smooth_x, smooth_y)
        return smooth_x, smooth_y

    @staticmethod
    def handle_controls(gesture, hand_result):
        if not hand_result: return
        
        x, y = Controller.get_position(hand_result)
        
        # --- SCROLL TRACKING ---
        if Controller.scroll_prev_y is None: Controller.scroll_prev_y = y
        if Controller.scroll_prev_x is None: Controller.scroll_prev_x = x
        dy = y - Controller.scroll_prev_y
        dx = x - Controller.scroll_prev_x
        Controller.scroll_prev_y = y
        Controller.scroll_prev_x = x

        # --- DRAG AND DROP LOGIC ---
        # If we are making a fist, press the mouse down and move it.
        if gesture == Gest.FIST:
            if not Controller.drag_flag:
                pyautogui.mouseDown(button='left')
                Controller.drag_flag = True
            pyautogui.moveTo(x, y)
        else:
            # The moment we stop making a fist, release the mouse to "drop" the item.
            if Controller.drag_flag:
                pyautogui.mouseUp(button='left')
                Controller.drag_flag = False

            # --- STANDARD CONTROLS ---
            if gesture == Gest.V_GEST:
                Controller.flag = True
                pyautogui.moveTo(x, y)
                
            elif gesture == Gest.INDEX and Controller.flag:
                pyautogui.click()
                Controller.flag = False
                
            elif gesture == Gest.MID and Controller.flag:
                pyautogui.doubleClick()
                Controller.flag = False
                
            elif gesture == Gest.PINKY and Controller.flag:
                pyautogui.click(button='right')
                Controller.flag = False
                
            elif gesture == Gest.LAST4:
                # Decide whether to scroll Vertical or Horizontal
                if abs(dx) > abs(dy):
                    if abs(dx) > 2: # Horizontal scroll
                        # EXCEL FIX: Hold Shift and do a normal scroll
                        pyautogui.keyDown('shift')
                        pyautogui.scroll(int(dx * 10))
                        pyautogui.keyUp('shift')
                else:
                    if abs(dy) > 2: # Vertical scroll
                        pyautogui.scroll(int(-dy * 10))
                    
            elif gesture == Gest.L_SIGN:
                p1 = hand_result.landmark[4] # Thumb Tip
                p2 = hand_result.landmark[8] # Index Tip
                dist = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
                
                vol = Controller.interp(dist, 0.05, 0.25, Controller.minVol, Controller.maxVol)
                vol = max(Controller.minVol, min(Controller.maxVol, vol))
                Controller.volume.SetMasterVolumeLevel(vol, None)

            elif gesture == Gest.SHAKA:
                p1 = hand_result.landmark[4] # Thumb Tip
                p2 = hand_result.landmark[20] # Pinky Tip
                dist = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
                
                # Map distance to Brightness percentage (0 to 100)
                bright = Controller.interp(dist, 0.05, 0.25, 0, 100)
                bright = max(0, min(100, bright))
                sbcontrol.set_brightness(int(bright))
                
            elif gesture == Gest.PALM:
                Controller.flag = False

class GestureController:
    gc_mode=1
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.hr_major = HandRecog(HLabel.MAJOR)
        self.hr_minor = HandRecog(HLabel.MINOR)

    def start(self):
        GestureController.gc_mode = 1
        with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
            while self.cap.isOpened() and GestureController.gc_mode: 
                success, frame = self.cap.read()
                if not success: break
                
                frame = cv2.flip(frame, 1)
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(img_rgb)
                
                gesture_name = "None"
                
                if results.multi_hand_landmarks:
                    for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                        self.hr_major.update_hand_result(hand_landmarks)
                        self.hr_major.set_finger_state()
                        gesture = self.hr_major.get_gesture()
                        
                        try:
                            gesture_name = Gest(gesture).name
                        except ValueError:
                            gesture_name = "Unknown"
                            
                        Controller.handle_controls(gesture, hand_landmarks)
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Draw Data & Updated Instructions
                cv2.putText(frame, f'Status: {gesture_name}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, 'Move: Peace | L-Click: Index | R-Click: Pinky | D-Click: Mid', (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, 'Scroll: 4-Fingers | Vol: L-Shape | Bright: Shaka | Drag: Fist', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                cv2.imshow('Gesture Controller', frame)
                if cv2.waitKey(1) & 0xFF == 27: # ESC to quit
                    break
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gc = GestureController()
    gc.start()