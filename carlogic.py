from enum import Enum
from random import uniform

car_id = 0

class Intent(Enum):
  CRUISE = 0
  ACCELERATE = 1
  DECELERATE = 2
  LANE_CHANGE_RIGHT = 3
  LANE_CHANGE_LEFT = 4

class CarLogic:
  def __init__(self):
    global car_id
    self.id = car_id
    car_id += 1
    cars.append(self)
    self.intent = Intent.CRUISE
    self.speed_preference = uniform(-10, 10)
  
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
    for car in cars:
      if car.id == self.id: continue
      lane_diff = car.lane - self.lane
      car_back = car.position + car.length
      car_front = car.position - self.get_stopping_distance()
      self_back = self.position + self.length
      self_front = self.position - car.get_stopping_distance()
      
      overlap_front = self_front < car_front < self_back
      overlap_back = car_front < self_front < car_back

      if lane_diff == 0 and overlap_front: params["car_front"] = True
      if lane_diff == -1 and (overlap_front or overlap_back): params["car_left"] = True
      if lane_diff == 1 and (overlap_front or overlap_back): params["car_right"] = True
    return params

  def update(self, dt):
    params = self.analyze_traffic()
    if params["car_front"]:
      if not params["car_left"] and self.lane > 0:
        self.intent = Intent.LANE_CHANGE_LEFT
      elif not params["car_right"] and self.lane < self.laneCount - 1:
        self.intent = Intent.LANE_CHANGE_RIGHT
      else:
        self.intent = Intent.DECELERATE
    else:
        if self.speed - (self.speed_limit + self.speed_preference) > 1:
          self.intent = Intent.DECELERATE
        elif self.speed < (self.speed_limit + self.speed_preference):
          self.intent = Intent.ACCELERATE
        else:
          self.intent = Intent.CRUISE
    
    match self.intent:
      case Intent.ACCELERATE:
        self.speed += self.acceleration * dt
      case Intent.DECELERATE:
        self.speed += self.deceleration * dt
        if self.speed < 0: self.speed = 0
      case Intent.LANE_CHANGE_RIGHT:
        self.lane += 1
      case Intent.LANE_CHANGE_LEFT:
        self.lane -= 1

cars = []