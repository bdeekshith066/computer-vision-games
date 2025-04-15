import cv2
import mediapipe as mp
import random
import time
import numpy as np

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Detect hand gesture from landmarks
def get_hand_gesture(hand_landmarks):
    finger_tips_ids = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb
    if hand_landmarks.landmark[finger_tips_ids[0]].x < hand_landmarks.landmark[finger_tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other fingers
    for tip_id in finger_tips_ids[1:]:
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    # Match gesture
    if fingers == [0, 0, 0, 0, 0]:
        return "Rock"
    elif fingers == [1, 1, 1, 1, 1]:
        return "Paper"
    elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
        return "Scissors"
    else:
        return "Unknown"

# Init
cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

player_move = "None"
comp_move = "None"
result = "Press R to Start"

player_score = 0
comp_score = 0

game_running = False
countdown_start = 0
gesture_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    current_time = time.time()

    # Countdown overlay
    if game_running:
        elapsed = current_time - countdown_start
        if elapsed < 1:
            countdown_text = "Rock..."
        elif elapsed < 2:
            countdown_text = "Paper..."
        elif elapsed < 3:
            countdown_text = "Scissors..."
        elif elapsed < 4:
            countdown_text = "Show your move!"
        else:
            # After countdown, detect gesture
            gesture = "Unknown"
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    gesture = get_hand_gesture(hand_landmarks)
                    break

            if gesture != "Unknown":
                player_move = gesture
                comp_move = random.choice(["Rock", "Paper", "Scissors"])

                # Determine winner
                if player_move == comp_move:
                    result = "It's a Tie!"
                elif (player_move == "Rock" and comp_move == "Scissors") or \
                     (player_move == "Scissors" and comp_move == "Paper") or \
                     (player_move == "Paper" and comp_move == "Rock"):
                    result = "You Win!"
                    player_score += 1
                else:
                    result = "Computer Wins!"
                    comp_score += 1
            else:
                result = "Gesture not detected"

            game_running = False  # Reset game flag

        if game_running:
            # Draw countdown
            cv2.putText(frame, countdown_text, (w // 2 - 150, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 4)

    # Transparent scoreboard header
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    alpha = 0.4
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Score and Moves
    cv2.putText(frame, f"Player: {player_score}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f"Computer: {comp_score}", (w - 250, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Result in center
    cv2.putText(frame, f"Result: {result}", (w // 2 - 150, h - 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

    # Moves
    cv2.putText(frame, f"Your Move: {player_move}", (10, h - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    cv2.putText(frame, f"Computer: {comp_move}", (10, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

    # Instructions
    cv2.putText(frame, "Press R to play, Q to quit", (w - 300, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 255, 150), 2)

    cv2.imshow("Rock Paper Scissors - Hand Gesture", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r') and not game_running:
        # Reset for next round
        countdown_start = time.time()
        game_running = True
        player_move = "None"
        comp_move = "None"
        result = "Get ready!"

cap.release()
cv2.destroyAllWindows()
