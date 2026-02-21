import pygame
import random
import sys
from sheets import SpriteSheet
from sheets import ATLAS_KEYS
from carlogic import CarLogic, cars

WIDTH, HEIGHT = 400, 800
FPS = 60

LANES = 3
ROAD_WIDTH = 260
ROAD_LEFT = (WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
LANE_W = ROAD_WIDTH // LANES

GRASS_COLOR = (40, 120, 40)
ROAD_COLOR = (30, 30, 30)
LINE_COLOR = (235, 235, 235)

CAR_W, CAR_H = 22, 40

# --- Units ---
# World distance is in METERS.
# Sign limits are in KM/H.
def kmh_to_mps(kmh: float) -> float:
    return kmh * 1000.0 / 3600.0

def mps_to_kmh(x: float) -> float:
    return x / 1000.0 * 3600.0

class Car(CarLogic):
    def __init__(self, lane, position_m, speed_kmh, speed_limit_kmh, sprite):
        super().__init__()
        self.set_properties(
            lane=lane,
            position=position_m,
            speed=kmh_to_mps(speed_kmh),
            speed_limit=kmh_to_mps(speed_limit_kmh),
            acceleration=12.0 + random.uniform(-6, 6),     # m/s^2 (tuned for sane feel)
            deceleration=-18.0 + random.uniform(-6, 6),   # m/s^2
            laneCount=LANES,
            length=CAR_H
        )
        self.sprite = sprite

    def x(self):
        lane_center = ROAD_LEFT + self.lane * LANE_W + LANE_W // 2
        return lane_center - CAR_W // 2

    def draw(self, screen, camera_y_m):
        screen_y = HEIGHT - (self.position - camera_y_m)
        screen.blit(self.sprite, (self.x(), screen_y))
        pygame.draw.rect(screen, (255, 0, 0), (self.x() - 5, screen_y - self.get_stopping_distance(), 10, self.get_stopping_distance()))

class SpeedSign:
    def __init__(self, position, limit_kmh):
        self.position = position
        self.limit_kmh = limit_kmh

    def draw(self, screen, camera_y_m, font):
        screen_y = HEIGHT - (self.position - camera_y_m) - 34
        x = ROAD_RIGHT + 10

        pygame.draw.line(screen, (120, 120, 120), (x + 22, screen_y + 34), (x + 22, screen_y + 60), 3)
        pygame.draw.rect(screen, (245, 245, 245), (x, screen_y, 44, 34), border_radius=6)
        pygame.draw.rect(screen, (30, 30, 30), (x, screen_y, 44, 34), 2, border_radius=6)

        txt = font.render(str(self.limit_kmh), True, (20, 20, 20))
        screen.blit(txt, (x + (44 - txt.get_width()) // 2, screen_y + (34 - txt.get_height()) // 2))

class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font, enabled=True):
        bg = (60, 160, 240) if enabled else (90, 90, 90)
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        pygame.draw.rect(screen, (20, 20, 20), self.rect, 2, border_radius=8)
        txt = font.render(self.text, True, (10, 10, 10))
        screen.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

def draw_world(screen, signs, camera_y_m, font):
    screen.fill(GRASS_COLOR)
    pygame.draw.rect(screen, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + LANE_W, 0), (ROAD_LEFT + LANE_W, HEIGHT), 2)
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + 2 * LANE_W, 0), (ROAD_LEFT + 2 * LANE_W, HEIGHT), 2)

    for s in signs:
        s.draw(screen, camera_y_m, font)

def spawn_traffic(sheet, start_y_m, player_speed_limit_kmh, count=6):
    """
    Spawn cars ahead of the player, spaced out per lane so they don't overlap.
    """
    # Clear any previous cars
    cars.clear()

    # Create player first and add to cars so traffic logic sees them
    player_sprite = sheet.get_scaled("lambo", (CAR_W, CAR_H))
    player = Car(lane=1, position_m=start_y_m, speed_kmh=120.0, speed_limit_kmh=player_speed_limit_kmh, sprite=player_sprite)

    # Track last placed position per lane to avoid overlaps
    last_pos_by_lane = [start_y_m + 80.0 for _ in range(LANES)]
    min_gap = CAR_H + 35.0  # meters (tuned spacing)

    for _ in range(count):
        lane = random.randint(0, LANES - 1)

        # place this car ahead of the last one in that lane
        lane_base = last_pos_by_lane[lane]
        pos = lane_base + random.uniform(min_gap, min_gap + 160.0)
        last_pos_by_lane[lane] = pos

        sprite_name = random.choice(ATLAS_KEYS)
        traffic_sprite = sheet.get_scaled(sprite_name, (CAR_W, CAR_H))

        # Start traffic at some reasonable speed (near limit, with a little variation)
        spd = random.uniform(0.65, 0.9) * player_speed_limit_kmh
        traffic = Car(lane=lane, position_m=pos, speed_kmh=spd, speed_limit_kmh=player_speed_limit_kmh, sprite=traffic_sprite)

    return player

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    sheet = SpriteSheet("cars.png")

    START_Y_M = 0.0
    END_Y_M = START_Y_M + 3000.0

    start_button = Button((10, 40, 110, 32), "START")
    moving = False
    finished = False

    # Build player + traffic (player returned; all cars stored in global cars list)
    player_car = spawn_traffic(sheet, START_Y_M, player_speed_limit_kmh=120.0, count=6)

    # Camera in meters
    camera_y_m = 0.0

    # Speed signs
    signs = []
    next_sign_y_m = -150

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.hit(event.pos) and not moving and not finished:
                    moving = True

        if moving and not finished:
            # Spawn signs ahead (km/h)
            while next_sign_y_m < min(player_car.position + 1400, END_Y_M + 400) and next_sign_y_m < END_Y_M:
                signs.append(SpeedSign(next_sign_y_m, random.choice([120, 160, 200, 240, 280])))
                next_sign_y_m += random.uniform(350, 450)

            '''# Apply sign: update SPEED LIMIT (m/s) when player passes sign
            while sign_index < len(signs) and player_car.position >= signs[sign_index].position:
                new_limit_kmh = float(signs[sign_index].limit_kmh)
                player_car.speed_limit = kmh_to_mps(new_limit_kmh)
                sign_index += 1'''

            # Update all cars with dt-based physics
            for c in cars:
                for sign in signs:
                    if sign.position > c.position: continue
                    c.speed_limit = kmh_to_mps(sign.limit_kmh)
                
                c.update(dt)
                c.position += c.speed * dt


            # Camera follows player
            camera_y_m = player_car.position - 120.0

            # End condition
            if player_car.position >= END_Y_M:
                finished = True
                moving = False
            
            #print(f"{cars[1].intent} {mps_to_kmh(cars[1].speed)} {mps_to_kmh(cars[1].speed_limit)}")

        # Draw world + signs
        draw_world(screen, signs, camera_y_m, font)

        # Start/end markers
        start_screen_y = HEIGHT - (START_Y_M - camera_y_m)
        end_screen_y = HEIGHT - (END_Y_M - camera_y_m)
        pygame.draw.line(screen, (0, 200, 255), (ROAD_LEFT, start_screen_y), (ROAD_RIGHT, start_screen_y), 3)
        pygame.draw.line(screen, (255, 80, 80), (ROAD_LEFT, end_screen_y), (ROAD_RIGHT, end_screen_y), 3)

        # UI info
        distance_m = max(0.0, player_car.position - START_Y_M)
        speed_kmh = mps_to_kmh(player_car.speed)
        limit_kmh = mps_to_kmh(player_car.speed_limit)

        info1 = font.render(f"Speed: {int(speed_kmh)} km/h   Limit: {int(limit_kmh)}", True, (255, 255, 255))
        info2 = font.render(f"Distance: {distance_m:.1f} m / 1000.0 m", True, (255, 255, 255))
        screen.blit(info1, (10, 10))
        screen.blit(info2, (10, 25))

        if finished:
            msg = font.render("FINISHED (1.0 km)", True, (255, 255, 255))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 80))

        # Start button
        start_button.draw(screen, font, enabled=(not moving and not finished))

        # Draw cars (player is already in cars list)
        for c in cars:
            c.draw(screen, camera_y_m)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()