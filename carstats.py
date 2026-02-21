from enum import Enum
from random import randint
from carlogic import CarLogic, cars

car_id = 0

class Intent(Enum):
  CRUISE = 0
  ACCELERATE = 1
  DECELERATE = 2
  LANE_CHANGE_LEFT = 3
  LANE_CHANGE_RIGHT = 4

class CarStats(CarLogic):
    def __init__(self):
        super().__init__()

        self.elapsed_time = 0.0
        self.finished = False

        self.max_speed = 0.0
        self.min_speed = float("inf")

    def update(self, dt):
        # Only update movement if not finished
        if not self.finished:
            super().update(dt)

            # Track time
            self.elapsed_time += dt

            # Track max/min speed
            if self.speed > self.max_speed:
                self.max_speed = self.speed

            if self.speed < self.min_speed:
                self.min_speed = self.speed