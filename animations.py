import math
import time
import random
from matrix_protocol import MatrixProtocol
import threading

class Animations:
    def __init__(self, matrix: MatrixProtocol):
        self.matrix = matrix
        self.func = self.sine_wave
        self.stop_thread = False
        self.delay = 0.01
        self.thread = None
        self.options = [self.sine_wave, self.sawtooth_wave, self.square_wave, self.random_pixels, self.raindrops, self.clock, self.rainbow]
        self.freq = 1
        self.A = 0.9
        self.dc = 0.5

    def thread_func(self):
        print("Starting Animation Thread")
        t = 0
        while not self.stop_thread:
            self.func(t=t, f=self.freq, dt=self.delay, A=self.A, dc=self.dc)
            time.sleep(self.delay)
            t += self.delay

    def stop(self):
        self.stop_thread = True
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()
        print("Animation Thread Stopped")
        self.matrix.clear()
        
    def start(self):
        self.stop_thread = False
        self.thread = threading.Thread(target=self.thread_func, name="AnimationThread")
        self.thread.start()

    def sine_wave(self, f=100, t=0, A=0.9, dt=1/30, **kwargs):
        width = self.matrix.width
        height = self.matrix.height

        # set all pixels to (0,0,0)
        for x in range(width):
            for y in range(height):
                self.matrix.set_pixel_buffer(x, y, 0, 0, 0)

        # display sine wave in 2d matrix
        prev_y = None
        for x in range(0, width):
            y = int((math.sin(2 * math.pi * f * (x + t)) + 1) * (height / 2) * A)
            t += dt
            if prev_y is not None and abs(y - prev_y) > 1:
                for i in range(min(y, prev_y), max(y, prev_y)):
                    self.matrix.set_pixel_buffer(x, i, 0, 255, 0)
            self.matrix.set_pixel_buffer(x, y, 0, 255, 0)
            prev_y = y
        self.matrix.send_pixels()

    def sawtooth_wave(self, f=100, t=0, A=0.9, **kwargs):
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

    def square_wave(self, f=100, dc=0.5, t=0, A=0.9, **kwargs):
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

    def random_pixels(self, n=10, **kwargs):
        width = self.matrix.width
        height = self.matrix.height

        for i in range(n):
            x = int(width * random.random())
            y = int(height * random.random())
            r = int(255 * random.random())
            g = int(255 * random.random())
            b = int(255 * random.random())
            self.matrix.set_pixel_buffer(x, y, r, g, b)
        self.matrix.send_pixels()

    def raindrops(self, n=10, **kwargs):
        width = self.matrix.width
        height = self.matrix.height

        for i in range(n):
            x = int(width * random.random())
            y = int(height * random.random())
            self.matrix.set_pixel_buffer(x, y, 0, 0, 255)
        self.matrix.send_pixels()

    def clock(self, **kwargs):
        from datetime import datetime
        current_time = datetime.now()
        hour = current_time.hour
        minute = current_time.minute
        time_str = f"{hour:02d}:{minute:02d}"

        self.matrix.clear_pixels_buffer()
        self.matrix.textRenderer.add_text(time_str.split(":")[0], line=0)
        self.matrix.textRenderer.add_text(time_str.split(":")[1], line=1)
        self.matrix.pixels = self.matrix.textRenderer.get_buffer()
        self.matrix.send_pixels()

    def rainbow(self, t=0, **kwargs):
        width = self.matrix.width
        height = self.matrix.height
        
        # move rainbow colors in 2d matrix
        for x in range(0, width):
            for y in range(0, height):
                r = int(127 * (math.sin(0.3 * (x + t)) + 1))
                g = int(127 * (math.sin(0.3 * (y + t)) + 1))
                b = int(127 * (math.sin(0.3 * (x + y + 2*t)) + 1))
                self.matrix.set_pixel_buffer(x, y, r, g, b)
        self.matrix.send_pixels()


if __name__ == '__main__':
    stop_thread = False

    def play_animation(matrix: MatrixProtocol, animations: Animations):
        previous_time = time.time()
        t = 0
        dt = 1/30
        wait = dt

        while not stop_thread:
            current_time = time.time()
            time_delta = current_time - previous_time
            previous_time = current_time

            animations.sine_wave(1, t=t, A=0.9)
            wait = (dt - time_delta)
            t += wait
            if wait < 0:
                wait = 0
            time.sleep(wait)


    matrix = MatrixProtocol(port="/dev/cu.usbserial-110")
    #matrix.port = "COM12"
    matrix.connect()

    import threading

    thread = None

    try:
        animations = Animations(matrix)
        t = 0
        dt = 1/30

        #thread = threading.Thread(target=play_animation, args=(matrix, animations), name="MatrixProtocolThread")
        #thread.start()
        animations.func = animations.rainbow

        animations.start()

        while True:
            #animations.clock()
            #animations.sine_wave(50, t=t, A=0.9)
            #animations.sawtooth_wave(50, t=t, A=1)
            #animations.square_wave(0.4, dc=0.25, t=t, A=1)
            #animations.random_pixels(10)
            #animations.raindrops(10)

            #t += dt
            #t = t % (10*matrix.width)
            
            # check if user pressed a key
            arg = input("Press any key to change animation: ")
            if arg:
                animations.stop()           
                entries = [animations.clock, animations.raindrops, animations.random_pixels, animations.sine_wave, animations.sawtooth_wave, animations.square_wave]
                animations.func = random.choice(entries)
                animations.start()

    
    except KeyboardInterrupt:
        stop_thread = True
        print("Stopping thread...")
        if thread is not None and thread.is_alive():
            thread.join()
        
        print("Exiting...")
        matrix.reset()
        time.sleep(1)

    finally:
        matrix.disconnect()