class DigitalInOut:
    def __init__(self, pin):
        self.direction = None
        self.value = False
        self.pull = None

class Direction:
    INPUT = 0
    OUTPUT = 1

class Pull:
    UP = 0
    DOWN = 1
