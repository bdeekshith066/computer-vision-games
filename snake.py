import math
import random
import cv2
import numpy as np
import time
import pygame
from cvzone.HandTrackingModule import HandDetector
import cvzone

# Init pygame for sound
pygame.init()
try:
    food_sound = pygame.mixer.Sound("pop.wav")
except:
    food_sound = None

# Hand detector
detector = HandDetector(detectionCon=0.7, maxHands=1)

# Snake game class
class SnakeGameClass:
    def __init__(self, pathFood):
        self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
        if self.imgFood.shape[2] == 3:
            self.imgFood = cv2.cvtColor(self.imgFood, cv2.COLOR_BGR2BGRA)
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.reset()

    def randomFoodLocation(self):
        self.foodPoint = random.randint(100, 1000), random.randint(100, 600)

    def reset(self):
        self.points = []
        self.lengths = []
        self.currentLength = 0
        self.allowedLength = 150
        self.previousHead = (0, 0)
        self.foodPoint = (0, 0)
        self.score = 0
        self.gameOver = False
        self.randomFoodLocation()

    def update(self, imgMain, currentHead):
        if self.gameOver:
            return imgMain

        px, py = self.previousHead
        cx, cy = currentHead
        self.points.append([cx, cy])
        distance = math.hypot(cx - px, cy - py)
        self.lengths.append(distance)
        self.currentLength += distance
        self.previousHead = cx, cy

        # Reduce tail
        if self.currentLength > self.allowedLength:
            for i, length in enumerate(self.lengths):
                self.currentLength -= length
                self.lengths.pop(i)
                self.points.pop(i)
                if self.currentLength < self.allowedLength:
                    break

        # Draw snake
        if self.points:
            for i in range(1, len(self.points)):
                cv2.line(imgMain, tuple(self.points[i - 1]), tuple(self.points[i]), (50, 0, 255), 20)
            cv2.circle(imgMain, tuple(self.points[-1]), 22, (0, 255, 100), cv2.FILLED)

        # Draw food
        rx, ry = self.foodPoint
        imgMain = cvzone.overlayPNG(imgMain, self.imgFood, (rx - self.wFood // 2, ry - self.hFood // 2))

        # Check collision
        if rx - self.wFood // 2 < cx < rx + self.wFood // 2 and ry - self.hFood // 2 < cy < ry + self.hFood // 2:
            self.randomFoodLocation()
            self.allowedLength += 50
            self.score += 1
            if food_sound:
                food_sound.play()

        # Show score
        cv2.putText(imgMain, f"Score: {self.score}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
        return imgMain

# Setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
game = SnakeGameClass("images/Donut.png")
start_game = False
game_duration = 40

def show_intro_screen(img):
    cv2.putText(img, "SNAKE GAME - HAND TRACKING", (150, 150), cv2.FONT_HERSHEY_COMPLEX, 1.7, (255, 255, 0), 4)
    cv2.putText(img, "Raise your index finger to control the snake", (250, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 255, 200), 3)
    cv2.putText(img, "Collect the food to grow!", (420, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 255, 255), 3)
    cv2.putText(img, "Game starts in...", (480, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 100, 100), 3)

def run_countdown():
    for i in range(5, 0, -1):
        success, frame = cap.read()
        if not success:
            break
        img = cv2.flip(frame, 1)
        show_intro_screen(img)
        cv2.putText(img, f"{i}", (620, 500), cv2.FONT_HERSHEY_DUPLEX, 4, (0, 255, 0), 5)
        cv2.imshow("Snake Game", img)
        cv2.waitKey(1000)

def show_game_over(img, score):
    cv2.putText(img, "GAME OVER", (420, 300), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 255), 6)
    cv2.putText(img, f"Final Score: {score}", (460, 370), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 255, 0), 4)
    cv2.putText(img, "Press 'r' to Restart or 'q' to Quit", (300, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 255, 200), 2)

def reset_and_start_game():
    global start_game, start_time, end_time
    run_countdown()
    game.reset()
    start_time = time.time()
    end_time = start_time + game_duration
    start_game = True

# Main Game Loop
while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)

    if not start_game:
        show_intro_screen(img)
        cv2.imshow("Snake Game", img)
        cv2.waitKey(1)
        reset_and_start_game()
        continue

    current_time = time.time()
    if current_time < end_time:
        hands, img = detector.findHands(img, flipType=False)
        if hands:
            pointIndex = hands[0]['lmList'][8][0:2]
            img = game.update(img, pointIndex)

        # Show time remaining
        cv2.putText(img, f"Time Left: {int(end_time - current_time)}s", (950, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
    else:
        game.gameOver = True
        show_game_over(img, game.score)

    cv2.imshow("Snake Game", img)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('r') and game.gameOver:
        start_game = False  # Triggers countdown again

cap.release()
cv2.destroyAllWindows()
