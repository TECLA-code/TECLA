class NeoPixel:
    def __init__(self, pin, n, brightness=1.0, auto_write=True, pixel_order=None):
        self.n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self._pixels = [(0,0,0)] * n

    def __setitem__(self, index, val):
        if isinstance(val, int):
            val = (val, val, val)
        self._pixels[index] = val

    def __getitem__(self, index):
        return self._pixels[index]

    def show(self):
        pass
    
    def fill(self, color):
        self._pixels = [color] * self.n
