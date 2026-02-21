import math
import pygame
import random
import sys
from sheets import SpriteSheet
from sheets import ATLAS_KEYS
from carstats import CarStats, cars

WIDTH, HEIGHT = 1400, 800
FPS = 60

SIM_SPEED = 1
all_run_results = []

SPEEDO_CENTER = (80, 680)  # left side, near bottom
SPEEDO_RADIUS = 60
SPEEDO_MAX_SPEED = 300  # km/h

LANES = 5
ROAD_WIDTH = 800
ROAD_LEFT = (WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
LANE_W = ROAD_WIDTH // LANES

GRASS_COLOR = (40, 120, 40)
ROAD_COLOR = (30, 30, 30)
LINE_COLOR = (235, 235, 235)

CAR_W, CAR_H = 22, 40

def speed_to_angle(speed, max_speed=300):
    angle = 225 - (speed / max_speed) * 270
    return math.radians(angle)

def draw_speedometer(surface, speed_kmh, center, radius, max_speed, font):
    pygame.draw.circle(surface, (60, 60, 60), center, radius + 4)
    pygame.draw.circle(surface, (10, 10, 10), center, radius)
    pygame.draw.circle(surface, (180, 180, 180), center, radius, 2)

    for s in range(0, max_speed + 1, 20):
        angle = speed_to_angle(s, max_speed)
        is_major = s % 60 == 0
        tick_len = 5 if is_major else 2

        outer = (center[0] + (radius - 2) * math.cos(angle),
                 center[1] - (radius - 2) * math.sin(angle))
        inner = (center[0] + (radius - 2 - tick_len) * math.cos(angle),
                 center[1] - (radius - 2 - tick_len) * math.sin(angle))

        color = (255, 255, 255) if is_major else (150, 150, 150)
        pygame.draw.line(surface, color, outer, inner, 1)

        if is_major:
            label_r = radius - 12
            lx = center[0] + label_r * math.cos(angle)
            ly = center[1] - label_r * math.sin(angle)
            text = font.render(str(s), True, (255, 255, 255))
            rect = text.get_rect(center=(lx, ly))
            surface.blit(text, rect)

    # Needle based on actual player speed
    needle_angle = speed_to_angle(min(speed_kmh, max_speed), max_speed)
    needle_len = radius - 8
    nx = center[0] + needle_len * math.cos(needle_angle)
    ny = center[1] - needle_len * math.sin(needle_angle)
    for w in range(3, 0, -1):
        pygame.draw.line(surface, (255, 80 + w * 15, 50), center, (nx, ny), w)

    # Center cap
    pygame.draw.circle(surface, (220, 50, 50), center, 4)
    pygame.draw.circle(surface, (255, 255, 255), center, 2)

    # Speed number
    spd_text = font.render(f"{int(speed_kmh)}", True, (255, 255, 255))
    surface.blit(spd_text, spd_text.get_rect(center=(center[0], center[1] + 16)))

# --- Units ---
# World distance is in METERS.
# Sign limits are in KM/H.
def kmh_to_mps(kmh: float) -> float:
    return kmh * 1000.0 / 3600.0

def mps_to_kmh(x: float) -> float:
    return x / 1000.0 * 3600.0

class Car(CarStats):
    def __init__(self, lane, position_m, speed_kmh, speed_limit_kmh, sprite):
        super().__init__()
        self.set_properties(
            lane=lane,
            position=position_m,
            speed=kmh_to_mps(speed_kmh),
            speed_limit=kmh_to_mps(speed_limit_kmh),
            acceleration=8.0 + random.uniform(-4, 4),     # m/s^2 (tuned for sane feel)
            deceleration=-12.0 + random.uniform(-4, 4),   # m/s^2
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
        pygame.draw.rect(screen, (255, 0, 0), (self.x(), screen_y - self.get_stopping_distance(), 10, self.get_stopping_distance()))

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
    for i in range(1, LANES):
        pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + i * LANE_W, 0), (ROAD_LEFT + i * LANE_W, HEIGHT), 2)

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
    END_Y_M = START_Y_M + 10000.0

    start_button = Button((10, 40, 110, 32), "START")
    moving = False
    finished = False

    # Build player + traffic (player returned; all cars stored in global cars list)
    player_car = spawn_traffic(sheet, START_Y_M, player_speed_limit_kmh=120.0, count=13)
    cars[1].lane = 1
    cars[1].speed_preference = -20
    #cars[2].lane = 0
    #cars[2].speed_preference = -15

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


            # Desired camera position (follow player)
            desired_camera_y = player_car.position - 120.0

            # Maximum camera value so finish line stays centered
            max_camera_y = END_Y_M - HEIGHT / 2

            # Clamp it
            camera_y_m = min(desired_camera_y, max_camera_y)

            if min(c.position for c in cars) >= END_Y_M:
                finished = True
                moving = False

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

        # Center x=110 (midpoint of 220px left grass), radius=90
        draw_speedometer(screen, mps_to_kmh(player_car.speed), (110, 680), 90, 300, font)

        label = font.render("Player Speed", True, (255, 255, 255))
        screen.blit(label, (110 - label.get_width() // 2, 578))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def run_simulation(sheet, num_traffic=6, speed_limit_kmh=120.0):
    """Run one full sim headless, return list of (car_id, elapsed_time, finished)"""
    START_Y_M = 0.0
    END_Y_M = 1000.0
    
    player = spawn_traffic(sheet, START_Y_M, speed_limit_kmh, count=num_traffic)
    
    # Build signs once
    signs = []
    next_sign_y = -150.0
    while next_sign_y < END_Y_M:
        signs.append(SpeedSign(next_sign_y, random.choice([120, 160, 200, 240, 280])))
        next_sign_y += random.uniform(350, 450)

    SIM_SPEED = 50.0
    SUB_STEPS = 4
    dt_base = 1.0 / 60.0  # simulate at 60fps timestep regardless of wall clock
    dt = (dt_base * SIM_SPEED) / SUB_STEPS

    while True:
        for _ in range(SUB_STEPS):
            for c in cars:
                # apply signs
                latest_limit_kmh = None
                for sign in signs:
                    if sign.position <= c.position:
                        latest_limit_kmh = sign.limit_kmh
                    else:
                        break
                if latest_limit_kmh is not None:
                    c.speedLimit = kmh_to_mps(latest_limit_kmh)

                if not c.finished:
                    c.update(dt)
                    if c.position >= END_Y_M:
                        c.finished = True
                        c.speed = 0.0

        if all(c.finished for c in cars):
            break

    return [(c.id, c.elapsed_time, c.finished) for c in cars]


def run_monte_carlo(sheet, num_runs=100):
    all_run_results = []
    
    for i in range(num_runs):
        results = run_simulation(sheet)
        all_run_results.append(results)
        print(f"Run {i+1}/{num_runs} done")
    
    return all_run_results


def analyze_results(all_run_results, time_threshold=25.0):
    import matplotlib.pyplot as plt
    from collections import defaultdict
    times_by_car = defaultdict(list)
    
    for run in all_run_results:
        for car_id, elapsed, finished in run:
            if finished:
                times_by_car[car_id].append(elapsed)
    
    # Flatten all times across all cars for the histogram
    all_times = [t for times in times_by_car.values() for t in times]
    total_entries = len(all_times)
    under_threshold = sum(1 for t in all_times if t < time_threshold)
    prob_under = under_threshold / total_entries * 100 if total_entries > 0 else 0

    print(f"\n==== MONTE CARLO RESULTS ({len(all_run_results)} runs) ====")
    for car_id, times in sorted(times_by_car.items()):
        avg = sum(times) / len(times)
        pct_under = sum(1 for t in times if t < time_threshold) / len(times) * 100
        runs_str = "  |  ".join(f"run{i+1}: {t:.2f}s" for i, t in enumerate(times))
        print(f"Car #{car_id}: avg={avg:.2f}s  % under {time_threshold}s: {pct_under:.1f}%  [{runs_str}]")

    print(f"\nProbability of finishing under {time_threshold}s: {prob_under:.1f}%")

    # Histogram — floor each time to nearest second for bucketing
    import math
    bucketed = [math.floor(t) for t in all_times]
    counts = defaultdict(int)
    for b in bucketed:
        counts[b] += 1

    seconds = sorted(counts.keys())
    freqs = [counts[s] for s in seconds]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(seconds, freqs, color=["red" if s >= time_threshold else "steelblue" for s in seconds], edgecolor="black", width=0.8)
    plt.axvline(x=time_threshold, color="red", linestyle="--", linewidth=1.5, label=f"Threshold: {time_threshold}s")
    plt.xlabel("Finish Time (s)")
    plt.ylabel("Count")
    plt.title(f"Finish Time Distribution ({len(all_run_results)} runs, {len(all_times)} total finishes)")
    plt.legend()
    plt.xticks(seconds)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    mode = input("Run mode? [sim/monte]: ").strip().lower()
    if mode == "monte":
        num_runs = int(input("How many runs? "))
        threshold = float(input("Time threshold (seconds)? "))
        pygame.init()
        pygame.display.set_mode((1, 1))  # dummy window, needed for image loading
        sheet = SpriteSheet("cars.png")
        results = run_monte_carlo(sheet, num_runs=num_runs)
        analyze_results(results, time_threshold=threshold)
    else:
        main()