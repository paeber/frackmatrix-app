import math
import time
import random
from matrix_protocol import MatrixProtocol
import subprocess
import threading
import numpy as np
import pyaudio

def hue_to_rgb(color):
    r, g, b = 0, 0, 0
    if 0 <= color < 60:
        r = 255
        g = int(255 * color / 60)
    elif 60 <= color < 120:
        r = int(255 * (120 - color) / 60)
        g = 255
    elif 120 <= color < 180:
        g = 255
        b = int(255 * (color - 120) / 60)
    elif 180 <= color < 240:
        g = int(255 * (240 - color) / 60)
        b = 255
    elif 240 <= color < 300:
        r = int(255 * (color - 240) / 60)
        b = 255
    elif 300 <= color < 360:
        r = 255
        b = int(255 * (360 - color) / 60)
    return (r, g, b)


class MusicAnalyzer:
    
    def __init__(self, matrix: MatrixProtocol, window_size=10, visu_mode="timeline"):
        self.matrix = matrix
        self.visu_mode = visu_mode
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = 1024
        self.rate = 48000
        self.max_peak = 1023
        self.sensitivity = 340
        self.window_size = window_size
        self.peaks = []
        self.bands = [(20, 100), (100, 250), (250, 500), (500, 2000), (2000, 4000), (4000, 6000), (6000, 12000), (12000, 20000)]
        self.stop_thread = False
        self.thread = None

    def open_stream(self):
        try:
            self.stream = self.p.open(format=pyaudio.paInt16, channels=2, rate=self.rate, input=True, frames_per_buffer=self.frames)
        except Exception as e:
            print("[ERROR] Audio device missing?", e)
            self.stream = None

    def close_stream(self):
        self.stream.stop_stream()
        self.stream.close()

    def start(self):
        self.stop_thread = False
        if self.stream is None:
            self.open_stream()
        self.thread = threading.Thread(target=self.calc_frame)
        self.thread.start()
        self.matrix.start_auto_buffer()

    def stop(self):
        self.stop_thread = True
        if self.stream is not None:
            self.thread.join()
        if self.stream is not None:
            self.close_stream()
            self.stream = None
        self.matrix.stop_auto_buffer()

    def get_peak(self):
        data = np.frombuffer(self.stream.read(2048), dtype=np.int16)
        peak = np.max(np.abs(data))
        peak = int(peak * self.max_peak / 2 ** 16)

        # Add the new peak value to the list of peaks
        self.peaks.append(peak)

        # If the list of peaks is larger than the window size, remove the oldest peak value
        if len(self.peaks) > self.window_size:
            self.peaks.pop(0)

        # Calculate the moving average of the peak values
        moving_average_peak = sum(self.peaks) / len(self.peaks)
        self.expected_peak = int(moving_average_peak * 1.2) + 100

        return peak

    def calc_frame(self):
        color = (255, 0, 0)
        hue = 0
        frame = [[(0, 0, 0) for x in range(self.matrix.width)] for y in range(self.matrix.height)]

        while not self.stop_thread:
            peak = self.get_peak()

            if self.visu_mode == "timeline":
                # shift the pixels in the frame to the left
                for y in range(self.matrix.height):
                    for x in range(self.matrix.width - 1):
                        frame[y][x] = frame[y][x + 1]
                
                # draw the new peak value on the right side of the frame
                for y in range(self.matrix.height):
                    inv_y = self.matrix.height - 1 - y
                    if y < peak * self.matrix.height // self.sensitivity:
                        frame[inv_y][self.matrix.width - 1] = color
                    else:
                        frame[inv_y][self.matrix.width - 1] = (0, 0, 0)

            elif self.visu_mode == "timeline_dual":
                # shift the pixels in the frame to the left
                for y in range(self.matrix.height):
                    for x in range(self.matrix.width - 1):
                        frame[y][x] = frame[y][x + 1]
                
                # draw the new peak value on the right side of the frame
                for y in range(self.matrix.height):
                    inv_y = self.matrix.height - 1 - y
                    level = peak * self.matrix.height // self.sensitivity
                    middle = self.matrix.height // 2
                    for y in range(level // 2):
                        frame[middle - y][self.matrix.width - 1] = color  
                        frame[middle + y][self.matrix.width - 1] = color          
                    else:
                        frame[inv_y][self.matrix.width - 1] = (0, 0, 0)

            else:
                # draw circle on matrix based on volume
                x = self.matrix.width // 2
                y = self.matrix.height // 2
                r = int(peak * (self.matrix.height // self.sensitivity) / 2)
                for i in range(360):
                    angle = math.radians(i)
                    x1 = int(x + r * math.cos(angle))
                    y1 = int(y + r * math.sin(angle))
                    if 0 <= x1 < self.matrix.width and 0 <= y1 < self.matrix.height:
                        frame[y1][x1] = (255, 0, 0)        

            self.matrix.pixels = frame.copy()

            # increment color loop
            hue += 1
            if hue >= 360:
                hue = 0
            color = hue_to_rgb(hue)

            time.sleep(0.001)

    
    


if __name__ == '__main__':

    matrix = MatrixProtocol()
    matrix.port = "COM12"
    matrix.baudrate = 1000000
    matrix_connected = False
    try:
        if matrix.connect():

            def update_matrix():
                while True:
                    matrix.send_pixels()
                    time.sleep(0.01)

            matrix.run_async(update_matrix)
            matrix_connected = True
    except:
        print("Matrix not connected")
        matrix.width = 50
        matrix.height = 20


    Music = MusicAnalyzer()



    mode = "timeline"

    # Define the number of frequency bins for the spectrogram
    num_bins = matrix.height

    try: 
        color = (255, 0, 0)
        hue = 0
        frame = [[(0, 0, 0) for x in range(matrix.width)] for y in range(matrix.height)]

        while True:
            peak = Music.get_peak()

            if mode == "circle":
                # draw circle on matrix based on volume
                x = matrix.width // 2
                y = matrix.height // 2
                r = int(peak * (matrix.height // Music.sensitivity) / 2)
                for i in range(360):
                    angle = math.radians(i)
                    x1 = int(x + r * math.cos(angle))
                    y1 = int(y + r * math.sin(angle))
                    if 0 <= x1 < matrix.width and 0 <= y1 < matrix.height:
                        frame[y1][x1] = (255, 0, 0)

            elif mode == "timeline":
                # shift the pixels in the frame to the left
                for y in range(matrix.height):
                    for x in range(matrix.width - 1):
                        frame[y][x] = frame[y][x + 1]
                
                # draw the new peak value on the right side of the frame
                for y in range(matrix.height):
                    inv_y = matrix.height - 1 - y
                    if y < peak * matrix.height // Music.sensitivity:
                        frame[inv_y][matrix.width - 1] = color
                    else:
                        frame[inv_y][matrix.width - 1] = (0, 0, 0)

            elif mode == "timeline_dual":
                # shift the pixels in the frame to the left
                for y in range(matrix.height):
                    for x in range(matrix.width - 1):
                        frame[y][x] = frame[y][x + 1]
                
                # draw the new peak value on the right side of the frame
                for y in range(matrix.height):
                    inv_y = matrix.height - 1 - y
                    level = peak * matrix.height // Music.sensitivity
                    middle = matrix.height // 2
                    for y in range(level // 2):
                        frame[middle - y][matrix.width - 1] = color  
                        frame[middle + y][matrix.width - 1] = color          
                    else:
                        frame[inv_y][matrix.width - 1] = (0, 0, 0)        

     

            # increment color loop
            hue += 1
            if hue >= 360:
                hue = 0
            color = hue_to_rgb(hue)

            time.sleep(0.01)
            

                    
                

                
                
            
            matrix.pixels = frame.copy()

            # Pretty print the matrix
            if matrix_connected == False:
                for row in frame:
                    print("".join(["#" if pixel != (0, 0, 0) else " " for pixel in row]))
                print("\n\n")
        
    except KeyboardInterrupt:
        print("Exiting...")
        matrix.stop_async()

    finally:
        Music.stream.close()
        Music.p.terminate()
        
        





        
