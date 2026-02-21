from enum import Enum
from random import randint

car_id = 0

class Intent(Enum):
  CRUISE = 0
  ACCELERATE = 1
  DECELERATE = 2
  LANE_CHANGE_LEFT = 3
  LANE_CHANGE_RIGHT = 4

class CarLogic:
  def __init__(self):
    global car_id
    self.id = car_id
    car_id += 1
    cars.append(self)
    self.intent = Intent.CRUISE

  def set_properties(self, position=0, speed=0, speed_limit=0, acceleration=0, deceleration=0, lane=0, laneCount=1, length=0):
    self.position = position
    self.speed = speed
    self.speed_limit = speed_limit
    self.acceleration = acceleration
    self.deceleration = deceleration
    self.lane = lane
    self.laneCount = laneCount
    self.length = length
  
  def get_stopping_distance(self):
    return -self.speed**2/(2*self.deceleration)

  def analyze_traffic(self):
    params = {
      "car_front": False,
      "car_left": False,
      "car_right": False
    }
    stopping_distance = self.get_stopping_distance()
    for car in cars:
      if car.id == self.id: continue
      lane_diff = car.lane - self.lane
      too_close_to_front = car.position + car.length >= self.position - stopping_distance
      too_close_to_back = self.position + self.length >= car.position - car.get_stopping_distance()
      if lane_diff == 0 and too_close_to_front: params["car_front"] = True
      if lane_diff == 1 and (too_close_to_front or too_close_to_back): params["car_left"] = True
      if lane_diff == -1 and (too_close_to_front or too_close_to_back): params["car_right"] = True
    return params

  def update(self, dt):
    params = self.analyze_traffic()
    if params["car_front"]:
      if not params["car_left"] and self.lane < self.laneCount - 1:
        self.intent = Intent.LANE_CHANGE_LEFT
      elif not params["car_right"] and self.lane > 0:
        self.intent = Intent.LANE_CHANGE_RIGHT
      else:
        self.intent = Intent.DECELERATE
    else:
        if self.speed - self.speed_limit > 1:
          self.intent = Intent.DECELERATE
        elif self.speed < self.speed_limit:
          self.intent = Intent.ACCELERATE
        else:
          self.intent = Intent.CRUISE
    
    match self.intent:
      case Intent.ACCELERATE:
        self.speed += self.acceleration * dt
      case Intent.DECELERATE:
        self.speed += self.deceleration * dt
        if self.speed < 0: self.speed = 0
      case Intent.LANE_CHANGE_LEFT:
        self.lane += 1
      case Intent.LANE_CHANGE_RIGHT:
        self.lane -= 1
    
    self.position += self.speed * dt

cars = []