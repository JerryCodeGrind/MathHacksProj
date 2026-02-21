import pygame
import random
import sys

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


class Car:
    def __init__(self, lane, world_y, speed, color=(60, 200, 80)):
        self.lane = lane
        self.world_y = world_y
        self.speed = speed
        self.speed_limit = speed
        self.color = color

    def x(self):
        lane_center = ROAD_LEFT + self.lane * LANE_W + LANE_W // 2
        return lane_center - CAR_W // 2

    def update(self, dt):
        self.world_y += self.speed * dt

    def draw(self, screen, camera_y):
        screen_y = HEIGHT - (self.world_y - camera_y) - CAR_H
        pygame.draw.rect(screen, self.color, (self.x(), screen_y, CAR_W, CAR_H))


class SpeedSign:
    def __init__(self, world_y, limit):
        self.world_y = world_y
        self.limit = limit

    def draw(self, screen, camera_y, font):
        screen_y = HEIGHT - (self.world_y - camera_y) - 34
        x = ROAD_RIGHT + 10  # always right side

        pygame.draw.line(screen, (120, 120, 120), (x + 22, screen_y + 34), (x + 22, screen_y + 60), 3)
        pygame.draw.rect(screen, (245, 245, 245), (x, screen_y, 44, 34), border_radius=6)
        pygame.draw.rect(screen, (30, 30, 30), (x, screen_y, 44, 34), 2, border_radius=6)

        txt = font.render(str(self.limit), True, (20, 20, 20))
        screen.blit(txt, (x + (44 - txt.get_width()) // 2, screen_y + (34 - txt.get_height()) // 2))


def draw_world(screen, signs, camera_y, font):
    screen.fill(GRASS_COLOR)
    pygame.draw.rect(screen, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + LANE_W, 0), (ROAD_LEFT + LANE_W, HEIGHT), 2)
    pygame.draw.line(screen, LINE_COLOR, (ROAD_LEFT + 2 * LANE_W, 0), (ROAD_LEFT + 2 * LANE_W, HEIGHT), 2)

    for s in signs:
        s.draw(screen, camera_y, font)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)

    # player car (the one that controls the camera + hits speed signs)
    player_car = Car(lane=1, world_y=0.0, speed=220.0, color=(60, 200, 80))

    # random traffic cars
    number_of_cars = 5
    cars = []
    for i in range(number_of_cars):
        lane = random.randint(0, LANES - 1)
        world_y = random.uniform(-2000, -200)     # start ahead (off-screen)
        speed = random.uniform(150, 300)
        cars.append(Car(lane=lane, world_y=world_y, speed=speed, color=(220, 180, 60)))

    camera_y = 0.0
    signs = []
    next_sign_y = 300.0
    sign_index = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # update cars
        player_car.update(dt)
        for c in cars:
            c.update(dt)

        # camera follows player
        camera_y = player_car.world_y - 120.0

        # spawn signs ahead of player
        while next_sign_y < player_car.world_y + 1400:
            signs.append(SpeedSign(next_sign_y, random.choice([120, 160, 200, 240, 280])))
            next_sign_y += random.uniform(500, 900)

        # apply current sign limit to player (with bounds check)
        while sign_index < len(signs) and player_car.world_y >= signs[sign_index].world_y:
            player_car.speed = signs[sign_index].limit
            sign_index += 1

        # draw
        draw_world(screen, signs, camera_y, font)

        info = font.render(
            f"speed={int(player_car.speed)}",
            True,
            (255, 255, 255),
        )
        screen.blit(info, (10, 10))

        # draw traffic + player
        for c in cars:
            c.draw(screen, camera_y)
        player_car.draw(screen, camera_y)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()