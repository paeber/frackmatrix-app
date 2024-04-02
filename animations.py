import math
import time
from matrix_protocol import MatrixProtocol

class Animations:
    def __init__(self, matrix: MatrixProtocol):
        self.matrix = matrix

    def sine_wave(self, f, t=0, A=0.9):
        width = self.matrix.width
        height = self.matrix.height

        # set all pixels to (0,0,0)
        for x in range(width):
            for y in range(height):
                self.matrix.set_pixel_buffer(x, y, 0, 0, 0)

        # display sine wave in 2d matrix
        prev_y = None
        for x in range(0, width):
            y = int((math.sin(2 * math.pi * f * ((x + t) / width)) + 1) * (height / 2) * A)
            if prev_y is not None and abs(y - prev_y) > 1:
                for i in range(min(y, prev_y), max(y, prev_y)):
                    self.matrix.set_pixel_buffer(x, i, 0, 255, 0)
            self.matrix.set_pixel_buffer(x, y, 0, 255, 0)
            prev_y = y
        self.matrix.send_pixels()

    def sawtooth_wave(self, f, t=0, A=0.9):
        width = self.matrix.width
        height = self.matrix.height

        # set all pixels to (0,0,0)
        for x in range(width):
            for y in range(height):
                self.matrix.set_pixel_buffer(x, y, 0, 0, 0)

        # display sawtooth wave in 2d matrix
        prev_y = None
        for x in range(0, width):
            y = int((x + t) * f * A) % height
            self.matrix.set_pixel_buffer(x, y, 0, 255, 0)
            
            if prev_y is not None and abs(y - prev_y) > 1:
                for i in range(min(y, prev_y), max(y, prev_y)):
                    self.matrix.set_pixel_buffer(x, i, 0, 255, 0)
            prev_y = y

        self.matrix.send_pixels()

    def square_wave(self, f, dc=0.5, t=0, A=0.9):
        width = self.matrix.width
        height = self.matrix.height

        # set all pixels to (0,0,0)
        for x in range(width):
            for y in range(height):
                self.matrix.set_pixel_buffer(x, y, 0, 0, 0)

        # display square wave in 2d matrix
        prev_y = None
        for x in range(0, width):
            y = int(A * (self.matrix.height - 1) if int((x + t) * f) % int(1/dc) == 0 else 0)
            if prev_y is not None and abs(y - prev_y) > 1:
                for i in range(min(y, prev_y), max(y, prev_y)):
                    self.matrix.set_pixel_buffer(x, i, 0, 255, 0)
            self.matrix.set_pixel_buffer(x, y, 0, 255, 0)
            prev_y = y
        self.matrix.send_pixels()



if __name__ == '__main__':
    matrix = MatrixProtocol(port="/dev/cu.usbserial-110")
    matrix.port = "COM12"
    matrix.connect()

    try:
        animations = Animations(matrix)
        t = 0
        while True:
            animations.square_wave(0.4, dc=0.25, t=t, A=1)
            t += 1
            t = t % (10*matrix.width)
    
    except KeyboardInterrupt:
        print("Exiting...")
        matrix.reset()
        
    finally:
        matrix.disconnect()