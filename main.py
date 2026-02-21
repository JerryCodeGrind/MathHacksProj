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

def m_to_km(m: float) -> float:
    return m / 1000.0

class Car(CarLogic):
    def __init__(self, lane, world_y_m, speed_kmh, speed_limit, sprite):
        super().__init__()
        self.set_properties(
            lane=lane,
            position=world_y_m,
            speed=kmh_to_mps(speed_kmh),
            speed_limit=kmh_to_mps(speed_limit),
            acceleration=10,
            deceleration=-20,
            laneCount=LANES,
            length=CAR_H
        )
        self.sprite = sprite  # REQUIRED
    
    def x(self):
        lane_center = ROAD_LEFT + self.lane * LANE_W + LANE_W // 2
        return lane_center - CAR_W // 2

    def draw(self, screen, camera_y_m):
        screen_y = HEIGHT - (self.world_y_m - camera_y_m) - CAR_H
        screen.blit(self.sprite, (self.x(), screen_y))


class SpeedSign:
    def __init__(self, world_y_m, limit_kmh):
        self.world_y_m = world_y_m
        self.limit_kmh = limit_kmh

    def draw(self, screen, camera_y_m, font):
        screen_y = HEIGHT - (self.world_y_m - camera_y_m) - 34
        x = ROAD_RIGHT + 10  # always right side

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
        screen.blit(
            txt,
            (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2),
        )

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def draw_world(screen, signs, camera_y_m, font):
    screen.fill(GRASS_COLOR)
    pygame.draw.rect(screen, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + LANE_W, 0), (ROAD_LEFT + LANE_W, HEIGHT), 2)
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + 2 * LANE_W, 0), (ROAD_LEFT + 2 * LANE_W, HEIGHT), 2)

    for s in signs:
        s.draw(screen, camera_y_m, font)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    sheet = SpriteSheet("cars.png")

    # --- Start/End setup (meters) ---
    START_Y_M = 0.0
    END_Y_M = START_Y_M + 1000.0  # 1 km

    # --- Start button ---
    start_button = Button((10, 40, 110, 32), "START")
    moving = False
    finished = False

    # --- Player car: controls camera + triggers speed signs ---
        # Player car (pick a specific sprite if you want, or random too)
    player_sprite = sheet.get_scaled("lambo", (CAR_W, CAR_H))
    player_car = Car(lane=1, world_y_m=START_Y_M, speed_kmh=240.0, sprite=player_sprite)

    number_of_cars = 5

    for i in range(number_of_cars):
        lane = i % LANES
        sprite_name = random.choice(ATLAS_KEYS)
        traffic_sprite = sheet.get_scaled(sprite_name, (CAR_W, CAR_H))

        cars.append(
            Car(
                lane=lane,
                world_y_m=START_Y_M,
                speed_kmh=player_car.speed_kmh,
                speed_limit=120,
                sprite=traffic_sprite
            )
        )
    

    for i, c in enumerate(cars):
        print(f"Car {i}: lane={c.lane}, speed={c.speed_kmh}, y={c.world_y_m}, sprite={c.sprite}")

    # Camera in meters
    camera_y_m = 0.0

    # Speed signs (km/h), placed ahead
    signs = []
    next_sign_y_m = 150.0
    sign_index = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Click start button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.hit(event.pos) and not moving and not finished:
                    moving = True

        if moving and not finished:
            # Update player and traffic
            player_car.update(dt, moving=True)

            # Keep all cars exactly same speed as player (no variation)
            for c in cars:
                c.speed_kmh = player_car.speed_kmh
                c.update(dt, moving=True)

            # Camera follows player (same "movement" as player)
            camera_y_m = player_car.world_y_m - 120.0

            # Spawn signs ahead of player until near the end point
            while next_sign_y_m < min(player_car.world_y_m + 1400, END_Y_M + 400) and next_sign_y_m < END_Y_M:
                signs.append(SpeedSign(next_sign_y_m, random.choice([120, 160, 200, 240, 280])))
                next_sign_y_m += random.uniform(150, 250)

            # Apply sign speed to player (KM/H), once we pass each sign
            while sign_index < len(signs) and player_car.world_y_m >= signs[sign_index].world_y_m:
                player_car.speed_kmh = float(signs[sign_index].limit_kmh)
                sign_index += 1

            # End condition: travelled 1km
            if player_car.world_y_m >= END_Y_M:
                finished = True
                moving = False

        # Draw world + signs
        draw_world(screen, signs, camera_y_m, font)

        # Draw start/end markers on the road (simple horizontal lines)
        start_screen_y = HEIGHT - (START_Y_M - camera_y_m)
        end_screen_y = HEIGHT - (END_Y_M - camera_y_m)
        pygame.draw.line(screen, (0, 200, 255), (ROAD_LEFT, start_screen_y), (ROAD_RIGHT, start_screen_y), 3)
        pygame.draw.line(screen, (255, 80, 80), (ROAD_LEFT, end_screen_y), (ROAD_RIGHT, end_screen_y), 3)

        # UI info
        distance_m = max(0.0, player_car.world_y_m - START_Y_M)
        info1 = font.render(f"Speed: {int(player_car.speed_kmh)} km/h", True, (255, 255, 255))
        info2 = font.render(f"Distance: {distance_m:.1f} m / 1000.0 m", True, (255, 255, 255))
        screen.blit(info1, (10, 10))
        screen.blit(info2, (10, 25))

        if finished:
            msg = font.render("FINISHED (1.0 km)", True, (255, 255, 255))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 80))

        # Start button
        start_button.draw(screen, font, enabled=(not moving and not finished))

        # Draw traffic + player
        for c in cars:
            c.draw(screen, camera_y_m)
        player_car.draw(screen, camera_y_m)

        pygame.display.flip()


    pygame.quit()
    sys.exit()

def statistics():
    print('hi')

if __name__ == "__main__":
    main()