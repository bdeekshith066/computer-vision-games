import cv2
import mediapipe as mp
import pygame
import sys

# ========== INIT ==========
pygame.init()
WIDTH, HEIGHT = 640, 480
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🙂 Easy Head Tilt Maze")

WHITE, BLUE, RED, GREEN, BLACK = (255, 255, 255), (100, 100, 255), (255, 50, 50), (50, 200, 100), (0, 0, 0)
clock = pygame.time.Clock()
FPS = 30

# ========== DOT SETUP ==========
dot_radius = 12
dot_x, dot_y = 60, 60
start_pos = (60, 60)
dot_speed = 2


# ======= New Simpler Maze =======
walls = [
    pygame.Rect(100, 120, 440, 20),    # First horizontal wall
    pygame.Rect(100, 120, 20, 150),    # Down vertical wall
    pygame.Rect(100, 250, 440, 20),    # Middle horizontal
    pygame.Rect(520, 250, 20, 130),    # Up vertical near finish
    pygame.Rect(100, 380, 440, 20),    # Bottom wall
]

finish_zone = pygame.Rect(540, 360, 60, 40)

# ========== MEDIAPIPE ==========
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(0)

# ========== STATE ==========
calibrated = False
calib_x = 0
calib_y = 0
tilt_sensitivity = 20
font = pygame.font.SysFont("arial", 20)
win_message = ""

# ========== MAIN GAME LOOP ==========
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                calibrated = False
                win_message = ""
                dot_x, dot_y = start_pos

    # Get nose tip
    if results.multi_face_landmarks:
        nose = results.multi_face_landmarks[0].landmark[1]
        nose_x = int(nose.x * WIDTH)
        nose_y = int(nose.y * HEIGHT)

        # Calibrate head center
        if not calibrated:
            calib_x, calib_y = nose_x, nose_y
            calibrated = True
        else:
            dx = nose_x - calib_x
            dy = nose_y - calib_y

            if dx > tilt_sensitivity:
                dot_x += dot_speed
            elif dx < -tilt_sensitivity:
                dot_x -= dot_speed
            if dy > tilt_sensitivity:
                dot_y += dot_speed
            elif dy < -tilt_sensitivity:
                dot_y -= dot_speed

    # Stay in bounds
    dot_x = max(dot_radius, min(WIDTH - dot_radius, dot_x))
    dot_y = max(dot_radius, min(HEIGHT - dot_radius, dot_y))

    # Collision detection
    dot_rect = pygame.Rect(dot_x - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2)
    for wall in walls:
        if dot_rect.colliderect(wall):
            dot_x, dot_y = start_pos
            win_message = ""

    # Check finish
    if dot_rect.colliderect(finish_zone):
        win_message = "🎉 You made it!"
        dot_x, dot_y = start_pos
        calibrated = False

    # ========== DRAW ==========
    win.fill(WHITE)
    for wall in walls:
        pygame.draw.rect(win, BLUE, wall)
    pygame.draw.circle(win, RED, (dot_x, dot_y), dot_radius)
    pygame.draw.rect(win, GREEN, finish_zone)

    if not calibrated:
        text = font.render("Look straight to calibrate...", True, BLACK)
    else:
        text = font.render("Tilt your head to move. Press R to reset.", True, BLACK)

    win.blit(text, (WIDTH // 2 - text.get_width() // 2, 10))

    if win_message:
        win.blit(font.render(win_message, True, (0, 150, 0)), (WIDTH // 2 - 80, HEIGHT - 40))

    pygame.display.update()
    clock.tick(FPS)
