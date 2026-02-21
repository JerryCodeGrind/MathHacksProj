import pygame
import sys

WIDTH = 400
HEIGHT = 800
SPEED_LIMIT = 100


class Car:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.width = 30
        self.height = 50
        self.color = (200, 50, 50)

    def update(self, dt):
        self.y -= self.speed * dt

    def draw(self, screen):
        pygame.draw.rect(screen, self.color,
                         (self.x, self.y, self.width, self.height))


def draw_road(screen):
    screen.fill((30, 30, 30))

    lane_width = WIDTH // 3

    pygame.draw.line(screen, (255, 255, 255), (lane_width, 0), (lane_width, HEIGHT), 2)
    pygame.draw.line(screen, (255, 255, 255), (lane_width * 2, 0), (lane_width * 2, HEIGHT), 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    car = Car(WIDTH // 2 - 15, 500, SPEED_LIMIT)

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        car.update(dt)

        draw_road(screen)
        car.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()