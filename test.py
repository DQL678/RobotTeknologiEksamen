import pygame
import serial
import math
import winsound
import threading
import time
from collections import deque

# ---------------- SERIAL ----------------
ser = serial.Serial('COM4', 9600, timeout=0.1)

# ---------------- PYGAME ----------------
pygame.init()
WIDTH, HEIGHT = 900, 550
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar")

font_big = pygame.font.SysFont("Consolas", 28)
font_small = pygame.font.SysFont("Consolas", 18)

cx = WIDTH // 2
cy = HEIGHT - int(HEIGHT * 0.10)

RADAR_RADIUS = min(WIDTH, HEIGHT) * 0.60
MAX_DISTANCE = 100

angle = 0
distance = 0
last_valid_distance = 0

clock = pygame.time.Clock()
smooth_buffer = deque(maxlen=5)

# ---------------- SOUND ----------------
object_detected = False
sound_running = True

def sound_loop():
    while sound_running:
        if object_detected:
            winsound.Beep(1200, 50)
            time.sleep(0.005)
        else:
            time.sleep(0.05)

sound_thread = threading.Thread(target=sound_loop, daemon=True)
sound_thread.start()

# ---------------- TRAIL ----------------
trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# ---------------- COLOR ----------------
def get_color(dist):
    ratio = min(dist / MAX_DISTANCE, 1)
    return (int(255 * (1 - ratio)), int(255 * ratio), 0)

# ---------------- BACKGROUND ----------------
def create_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    for i in range(HEIGHT):
        shade = int(10 + i * 0.05)
        pygame.draw.line(bg, (0, shade, 0), (0, i), (WIDTH, i))
    return bg

# ---------------- RADAR GRID ----------------
def create_radar():
    radar = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    steps = [25, 50, 75, 100]

    for d in steps:
        r = (d / MAX_DISTANCE) * RADAR_RADIUS
        pygame.draw.circle(radar, (0, 120, 0), (cx, cy), int(r), 1)

        label = font_small.render(f"{d} cm", True, (0, 200, 0))
        radar.blit(label, (cx + r - 30, cy - 10))

    for a in range(0, 181, 30):
        x = cx + RADAR_RADIUS * math.cos(math.radians(a))
        y = cy - RADAR_RADIUS * math.sin(math.radians(a))
        pygame.draw.aaline(radar, (0, 200, 0), (cx, cy), (x, y))

    return radar

bg = create_background()
radar = create_radar()

# ---------------- DRAW FUNCTIONS ----------------
def draw_sweep(a):
    x = cx + RADAR_RADIUS * math.cos(math.radians(a))
    y = cy - RADAR_RADIUS * math.sin(math.radians(a))

    pygame.draw.line(screen, (30, 255, 60), (cx, cy), (x, y), 2)

    label = font_small.render(f"{a}°", True, (0, 255, 120))

    offset = 20
    lx = cx + (RADAR_RADIUS + offset) * math.cos(math.radians(a))
    ly = cy - (RADAR_RADIUS + offset) * math.sin(math.radians(a))

    screen.blit(label, (lx - 10, ly - 10))

def add_trail_point(a, dist):
    if dist <= 0 or dist > MAX_DISTANCE:
        return

    px = dist * (RADAR_RADIUS / MAX_DISTANCE)
    x = cx + px * math.cos(math.radians(a))
    y = cy - px * math.sin(math.radians(a))

    # tydelig rød plet
    pygame.draw.circle(trail_surface, (255, 0, 0, 255), (int(x), int(y)), 14)

    # ekstra glød
    pygame.draw.circle(trail_surface, (255, 80, 80, 120), (int(x), int(y)), 24)

def fade_trail():
    fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fade.fill((0, 0, 0, 3))  # lav værdi = længere trail
    trail_surface.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

def draw_text():
    color = get_color(distance)

    screen.blit(font_big.render(
        f"Angle: {angle}°",
        True,
        (98, 245, 31)
    ), (20, 20))

    screen.blit(font_big.render(
        f"Distance: {distance:.1f} cm",
        True,
        color
    ), (20, 60))

    screen.blit(font_small.render(
        "Range: 0 - 100 cm (1 meter)",
        True,
        (0, 180, 0)
    ), (20, 100))

# ---------------- MAIN LOOP ----------------
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ---------------- SERIAL ----------------
    if ser.in_waiting:
        raw = ser.readline().decode(errors='ignore').strip()

        try:
            raw = raw.replace('.', '')

            if ',' in raw:
                a, d = raw.split(',')

                angle = int(a)
                d = int(d)

                if 0 < d <= MAX_DISTANCE:
                    last_valid_distance = d
                else:
                    last_valid_distance = 0

                smooth_buffer.append(last_valid_distance)

                if len(smooth_buffer) > 0:
                    distance = sum(smooth_buffer) / len(smooth_buffer)

        except:
            pass

    # ---------------- SOUND ----------------
    object_detected = (0 < distance <= MAX_DISTANCE)

    # ---------------- TRAIL ----------------
    fade_trail()

    if object_detected:
        add_trail_point(angle, distance)

    # ---------------- DRAW ----------------
    screen.blit(bg, (0, 0))
    screen.blit(radar, (0, 0))

    draw_sweep(angle)

    screen.blit(trail_surface, (0, 0))  

    draw_text()

    pygame.display.flip()
    clock.tick(120)

# ---------------- CLEANUP ----------------
sound_running = False
pygame.quit()