import pygame
import serial
import math
from collections import deque

# --- Serial setup ---
ser = serial.Serial('COM5', 9600)

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 900, 550
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Radar")

font_big = pygame.font.SysFont("Consolas", 28)
font_small = pygame.font.SysFont("Consolas", 18)

# Radar center
cx = WIDTH // 2
cy = HEIGHT - int(HEIGHT * 0.10)

RADAR_RADIUS = min(WIDTH, HEIGHT) * 0.45

GREEN = (98, 245, 31)
RED = (255, 10, 10)
SWEEP = (30, 250, 60)

angle = 0
distance = 0

clock = pygame.time.Clock()
running = True

# --- Distance smoothing (Python-side filter) ---
smooth_buffer = deque(maxlen=5)


# ---------------- PRE-RENDER STATIC ELEMENTS ---------------- #

def create_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    for i in range(HEIGHT):
        shade = int(10 + i * 0.05)
        pygame.draw.line(bg, (0, shade, 0), (0, i), (WIDTH, i))
    return bg


def create_radar_overlay():
    radar = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    radii = [
        RADAR_RADIUS,
        RADAR_RADIUS * 0.75,
        RADAR_RADIUS * 0.50,
        RADAR_RADIUS * 0.25
    ]

    for r in radii:
        pygame.draw.circle(radar, (0, 120, 0), (cx, cy), int(r), 1)

    for a in range(0, 181, 30):
        x = cx + RADAR_RADIUS * math.cos(math.radians(a))
        y = cy - RADAR_RADIUS * math.sin(math.radians(a))
        pygame.draw.aaline(radar, (0, 200, 0), (cx, cy), (x, y))

        lx = cx + (RADAR_RADIUS + 20) * math.cos(math.radians(a))
        ly = cy - (RADAR_RADIUS + 20) * math.sin(math.radians(a))
        label = font_small.render(f"{a}°", True, GREEN)
        radar.blit(label, (lx - 10, ly - 10))

    return radar


background = create_background()
radar_overlay = create_radar_overlay()


# ---------------- DRAW FUNCTIONS ---------------- #

def draw_sweep(a):
    x = cx + RADAR_RADIUS * math.cos(math.radians(a))
    y = cy - RADAR_RADIUS * math.sin(math.radians(a))

    for w in range(1, 10):
        color = (30, 255, 60, max(0, 150 - w * 15))
        pygame.draw.line(screen, color, (cx, cy), (x, y), w)

    pygame.draw.aaline(screen, (50, 255, 100), (cx, cy), (x, y))


def draw_object(a, dist):
    if dist > 50:
        return

    px = dist * (RADAR_RADIUS / 40)
    x = cx + px * math.cos(math.radians(a))
    y = cy - px * math.sin(math.radians(a))

    for r in range(12, 2, -2):
        alpha = max(0, 80 - r * 5)
        halo = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 0, 0, alpha), (15, 15), r)
        screen.blit(halo, (x - 15, y - 15))

    pygame.draw.circle(screen, (255, 50, 50), (int(x), int(y)), 5)


def draw_text():
    hud = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
    hud.fill((0, 0, 0, 160))
    screen.blit(hud, (0, HEIGHT - 50))

    screen.blit(font_big.render("Radar", True, GREEN), (20, HEIGHT - 40))
    screen.blit(font_big.render(f"Angle: {angle}°", True, GREEN), (250, HEIGHT - 40))
    screen.blit(font_big.render(f"Distance: {distance:.1f} cm", True, GREEN), (450, HEIGHT - 40))


# ---------------- MAIN LOOP ---------------- #

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if ser.in_waiting:
        raw = ser.read_until(b'.').decode().strip('.')
        try:
            a, d = raw.split(',')
            angle = int(a)

            smooth_buffer.append(int(d))
            distance = sum(smooth_buffer) / len(smooth_buffer)

        except:
            pass

    screen.blit(background, (0, 0))
    screen.blit(radar_overlay, (0, 0))

    draw_sweep(angle)
    draw_object(angle, distance)
    draw_text()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
