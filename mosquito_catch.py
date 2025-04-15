import cv2
import mediapipe as mp
import numpy as np
import random
import time
import screeninfo

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

# Get screen dimensions
try:
    screen = screeninfo.get_monitors()[0]
    GAME_WIDTH = screen.width
    GAME_HEIGHT = screen.height
except:
    # Fallback dimensions if screeninfo fails
    GAME_WIDTH = 1366
    GAME_HEIGHT = 768

# Calculate relative sizes based on screen dimensions
MOSQUITO_SIZE = max(40, int(min(GAME_WIDTH, GAME_HEIGHT) * 0.05))
HAND_SIZE = max(80, int(min(GAME_WIDTH, GAME_HEIGHT) * 0.1))

def load_image(path, resize=None):
    img = cv2.imread(path)
    if img is None:
        print(f"Error: Could not load image {path}")
        # Create colored placeholder depending on image type
        if "mosquito" in path:
            img = np.zeros((50, 50, 3), dtype=np.uint8)
            img[:] = (0, 0, 255)  # Red mosquito placeholder
        elif "hand" in path:
            img = np.zeros((80, 80, 3), dtype=np.uint8)
            img[:] = (0, 255, 0)  # Green hand placeholder
        else:
            img = np.zeros((GAME_HEIGHT, GAME_WIDTH, 3), dtype=np.uint8)
            img[:] = (135, 206, 235)  # Sky blue background
    
    if resize:
        img = cv2.resize(img, resize)
    return img

# Load images with dynamic sizing
background = load_image("images/bg.jpg", (GAME_WIDTH, GAME_HEIGHT))
mosquito_img = load_image("images/mosquito.jpg", (MOSQUITO_SIZE, MOSQUITO_SIZE))
hand_img = load_image("images/hand.jpg", (HAND_SIZE, HAND_SIZE))

# Game variables
score = 0
mosquitoes = []
hand_pos = (GAME_WIDTH // 2 - HAND_SIZE//2, GAME_HEIGHT // 2 - HAND_SIZE//2)
game_duration = 30  # seconds
start_time = None
game_active = False

def spawn_mosquito():
    x = random.randint(0, GAME_WIDTH - MOSQUITO_SIZE)
    y = random.randint(0, GAME_HEIGHT - MOSQUITO_SIZE)
    # Adjust speed based on screen size
    base_speed = max(1, int(min(GAME_WIDTH, GAME_HEIGHT) * 0.005))
    speed_x = random.choice([-3, -2, -1, 1, 2, 3]) * base_speed
    speed_y = random.choice([-3, -2, -1, 1, 2, 3]) * base_speed
    mosquitoes.append({
        "x": x,
        "y": y,
        "speed_x": speed_x,
        "speed_y": speed_y,
        "lifetime": random.randint(100, 200)
    })

def reset_game():
    global score, mosquitoes, start_time, game_active
    score = 0
    mosquitoes.clear()
    start_time = time.time()
    game_active = True

# Main game loop
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Set up full-screen window
cv2.namedWindow("Mosquito Catcher Game", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Mosquito Catcher Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

reset_game()  # Start the game

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
            
        # Flip horizontally and resize frame to match game dimensions
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (GAME_WIDTH, GAME_HEIGHT))
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Update hand position (using landmark index 9 for a stable central point)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                cx = int(hand_landmarks.landmark[9].x * GAME_WIDTH)
                cy = int(hand_landmarks.landmark[9].y * GAME_HEIGHT)
                # Clamp hand position to remain within screen bounds
                hand_pos = (max(0, min(cx - HAND_SIZE//2, GAME_WIDTH - HAND_SIZE)), 
                            max(0, min(cy - HAND_SIZE//2, GAME_HEIGHT - HAND_SIZE)))
        
        # Update the game timer
        current_time = time.time()
        elapsed_time = current_time - start_time
        remaining_time = max(0, game_duration - int(elapsed_time))
        if remaining_time <= 0 and game_active:
            game_active = False
        
        # Game logic only runs when active
        if game_active:
            # Adjust spawn rate based on screen size
            if random.random() < 0.04 * (1366/GAME_WIDTH):
                spawn_mosquito()
            
            for mosquito in mosquitoes[:]:
                mosquito["x"] += mosquito["speed_x"]
                mosquito["y"] += mosquito["speed_y"]
                mosquito["lifetime"] -= 1
                
                # Remove mosquito if lifetime is over or if it goes too far off screen
                if (mosquito["lifetime"] <= 0 or 
                    mosquito["x"] < -100 or mosquito["x"] > GAME_WIDTH + 100 or
                    mosquito["y"] < -100 or mosquito["y"] > GAME_HEIGHT + 100):
                    mosquitoes.remove(mosquito)
                    continue
                
                # Bounce off the edges
                if mosquito["x"] <= 0 or mosquito["x"] >= GAME_WIDTH - MOSQUITO_SIZE:
                    mosquito["speed_x"] *= -1
                if mosquito["y"] <= 0 or mosquito["y"] >= GAME_HEIGHT - MOSQUITO_SIZE:
                    mosquito["speed_y"] *= -1
                
                # Collision check
                if (hand_pos[0] < mosquito["x"] + MOSQUITO_SIZE and
                    hand_pos[0] + HAND_SIZE > mosquito["x"] and
                    hand_pos[1] < mosquito["y"] + MOSQUITO_SIZE and
                    hand_pos[1] + HAND_SIZE > mosquito["y"]):
                    mosquitoes.remove(mosquito)
                    score += 1
        
        # Start drawing to the display image based on the background
        display_img = background.copy()
        
        # Draw mosquitoes with boundary checking
        if game_active:
            for mosquito in mosquitoes:
                x = mosquito["x"]
                y = mosquito["y"]
                
                # Compute the overlapping region between mosquito image and display
                x1 = max(x, 0)
                y1 = max(y, 0)
                x2 = min(x + MOSQUITO_SIZE, GAME_WIDTH)
                y2 = min(y + MOSQUITO_SIZE, GAME_HEIGHT)
                
                # If the mosquito is completely off-screen, skip drawing
                if x1 >= x2 or y1 >= y2:
                    continue
                
                # Calculate the corresponding region within the mosquito image
                crop_x_start = 0 if x >= 0 else -x
                crop_y_start = 0 if y >= 0 else -y
                crop_x_end = crop_x_start + (x2 - x1)
                crop_y_end = crop_y_start + (y2 - y1)
                
                display_img[y1:y2, x1:x2] = mosquito_img[crop_y_start:crop_y_end, crop_x_start:crop_x_end]
        
        # Draw hand image at updated hand position
        hand_x, hand_y = hand_pos
        display_img[hand_y:hand_y+HAND_SIZE, hand_x:hand_x+HAND_SIZE] = hand_img
        
        # Display score and timer with dynamic font size
        font_scale = max(0.8, min(GAME_WIDTH, GAME_HEIGHT) / 1000)
        thickness = max(1, int(font_scale * 2))
        
        cv2.putText(display_img, f"Score: {score}", 
                    (int(GAME_WIDTH * 0.02), int(GAME_HEIGHT * 0.05)), 
                    cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 0), thickness)
        cv2.putText(display_img, f"Time: {remaining_time}s", 
                    (int(GAME_WIDTH * 0.02), int(GAME_HEIGHT * 0.10)), 
                    cv2.FONT_HERSHEY_DUPLEX, font_scale, (0, 255, 255), thickness)
        
        # Game Over overlay when game is not active due to timeout
        if not game_active:
            overlay = display_img.copy()
            cv2.rectangle(overlay, (0, 0), (GAME_WIDTH, GAME_HEIGHT), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, display_img, 0.3, 0, display_img)
            
            game_over_font_scale = max(1.5, min(GAME_WIDTH, GAME_HEIGHT) / 500)
            game_over_thickness = max(3, int(game_over_font_scale * 2))
            
            cv2.putText(display_img, "GAME OVER", 
                        (int(GAME_WIDTH // 2 - 120 * game_over_font_scale), 
                         int(GAME_HEIGHT // 2 - 30 * game_over_font_scale)), 
                        cv2.FONT_HERSHEY_SIMPLEX, game_over_font_scale, (0, 0, 255), game_over_thickness)
            cv2.putText(display_img, f"Final Score: {score}", 
                        (int(GAME_WIDTH // 2 - 120 * game_over_font_scale), 
                         int(GAME_HEIGHT // 2 + 20 * game_over_font_scale)), 
                        cv2.FONT_HERSHEY_SIMPLEX, game_over_font_scale * 0.7, (255, 255, 255), game_over_thickness)
            cv2.putText(display_img, "Press R to restart, Q to quit", 
                        (int(GAME_WIDTH // 2 - 150 * game_over_font_scale), 
                         int(GAME_HEIGHT // 2 + 70 * game_over_font_scale)), 
                        cv2.FONT_HERSHEY_SIMPLEX, game_over_font_scale * 0.5, (255, 255, 255), game_over_thickness)
        
        cv2.imshow("Mosquito Catcher Game", display_img)
        
        # Handle key events
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            time.sleep(0.5)  # Optional delay for restart
            reset_game()

finally:
    cap.release()
    cv2.destroyAllWindows()
