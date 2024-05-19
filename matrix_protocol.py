import time
import serial
import serial.tools.list_ports
import numpy as np
from PIL import Image
from text_renderer import TextRenderer
import threading

class MatrixProtocol:

    def __init__(self, port='/dev/ttyUSB0', baudrate=1000000, width=16, height=16):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.width = width
        self.height = height
        self.pixels = [[(0, 0, 0) for x in range(self.width)] for y in range(self.height)]
        self.textRenderer = TextRenderer(width, height)
        self.snake = False
        self.mirror = False
        self.rotation = 180
        self.simulation = False
        self.thread = None
        self.stop_thread = False

    def scan_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self):
        if self.ser is not None:
            return False
        print("Connect to port: " + self.port)
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        if self.ser.isOpen():
            return True

    def disconnect(self):
        if self.ser is None:
            return False
        print("Disconnect from port: " + self.port)
        self.ser.close()
        self.ser = None
        return True

    def reset(self):
        if self.ser is None:
            print("Serial port not connected")
            return False
        data = bytes([1])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')
    
    def get_size(self):
        if self.ser is None:
            print("Serial port not connected")
            return False
        self.ser.write(bytes([11]))
        ret = self.ser.read(3)
        print(ret)
        return ret[2] == b'\x10'


    def xy_to_snake(self, x, y, width):
        if y % 2 == 0:
            return y * width + x
        else:
            return y * width + (width - x - 1)
        
    def snake_to_xy(self, index, width):
        y = index // width
        x = index % width
        if y % 2 != 0:
            x = width - x - 1
        return x, y
        
    def clear_pixels_buffer(self):
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[y][x] = (0, 0, 0)

    def clear(self):
        self.clear_pixels_buffer()
        self.send_pixels()
    
    def set_pixel_cmd(self, x, y, r, g, b, snake=False):
        if self.ser is None:
            print("Serial port not connected")
            return False
        if not (0 <= x < self.width and 0 <= y < self.height):
            print("Invalid x, y coordinates")
            return False
        if snake:
            index = self.xy_to_snake(x, y, self.width)
        else:
            index = y * self.width + x
        data = bytes([0, index, r, g, b])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')
    
    def set_pixel_buffer(self, x, y, r, g, b, snake=False):
        if not (0 <= x < self.width and 0 <= y < self.height):
            print("Invalid x, y coordinates")
            return False
        if snake:
            index = self.xy_to_snake(x, y, self.width)
            self.pixels[index // self.width][index % self.width] = (r, g, b)
        else:
            self.pixels[y][x] = (r, g, b)

    def send_pixels(self, snake=False, priority=False):
        if self.ser is None and not self.simulation:
            print("Serial port not connected")
            return False
        if threading.current_thread().name == 'MainThread':
            if self.thread is not None and self.thread.is_alive():
                print("[WARN]: send_pixels is locked for", self.thread.name)
                return False
        data = bytes([2])

        #convert self.pixels to numpy array
        send_buf = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            for x in range(self.width):
                if self.mirror:
                    send_buf[y][x] = self.pixels[y][self.width - (x + 1)]
                else:
                    send_buf[y][x] = self.pixels[y][x]

        if self.simulation:
            self.simulation_output(send_buf)
            return True

        if self.rotation == 0:
            pass
        elif self.rotation == 180:
            send_buf = np.rot90(send_buf, 2)
                        
        if snake:
            for idx in range(self.width * self.height):
                x, y = self.snake_to_xy(idx, self.width)
                r, g, b = send_buf[y][x]
                data += bytes([r, g, b])
        else: 
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = send_buf[y][x]
                    data += bytes([r, g, b])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')

    def load_image(self, image_path, stretch=False):  
        img = Image.open(image_path)
        if stretch:
            img = img.resize((self.width, self.height))
            x_offset = 0
            y_offset = 0
        else:
            # check which dimension is larger and scale it to the matrix size
            if img.width > img.height:
                img = img.resize((self.width, self.height * img.height // img.width))
            else:
                img = img.resize((self.width * img.width // img.height, self.height))
            # center the image on the matrix
            x_offset = (self.width - img.width) // 2
            y_offset = (self.height - img.height) // 2
        try:
            pixels = img.load()
            for y in range(self.height):
                for x in range(self.width):
                    if len(pixels[x, y]) == 3:
                        r, g, b = pixels[x, y]
                    elif len(pixels[x, y]) == 4:
                        r, g, b, a= pixels[x, y]
                    self.set_pixel_buffer(x + x_offset, y + y_offset, r, g, b)
        except Exception as e:
            print("Error loading image:", e)

    def scroll_text(self, text="HELLO", line=0, foreground=(255, 255, 255), background=(0, 0, 0), blank=True, fill=False, **kwargs):
        if blank:
            quotient, remainder = divmod(self.width, self.textRenderer.slot_width)
            blanks = quotient + bool(remainder)
            text = "{0}{1}{0}".format(" " * blanks, text)

        self.clear_pixels_buffer()
        disp_width = self.width
        disp_height = self.height

        disp_buffer = [[background for x in range(disp_width)] for y in range(disp_height)]
        text_buffer = self.textRenderer.render_buffer(text, foreground, background)

        if fill:
            # scale up text buffer to display buffer size
            text_buffer = np.repeat(text_buffer, disp_height // self.textRenderer.char_height, axis=0)
            text_buffer = np.repeat(text_buffer, disp_width // self.textRenderer.char_width, axis=1)
            

        # move text buffer to display buffer from right to left with a step of 1 pixel algin at the top
        for i in range(len(text_buffer[0]) - disp_width):
            for y in range(disp_height):
                for x in range(disp_width):
                    try:
                        disp_buffer[y][x] = text_buffer[y][i + x]
                    except:
                        pass
            self.pixels = disp_buffer.copy()
            self.send_pixels()
            time.sleep(1/30)

            if self.stop_thread:
                print("[INFO]: Thread stopped")
                self.stop_thread = False
                return

    def run_async(self, task, task_args=(), name="MatrixProtocolThread"):
        if self.ser is None and not self.simulation:
            print("Serial port not connected")
            return False
        if self.thread is not None and self.thread.is_alive():
            return False
        self.stop_thread = False
        self.thread = threading.Thread(target=task, args=task_args, name=name)
        self.thread.start()
        print("[INFO]: Thread {0} started".format(self.thread.name))
        return self.thread.is_alive()
    
    def stop_async(self):
        if self.thread is not None and self.thread.is_alive():
            self.stop_thread = True
            self.thread.join()
            return True
        return False
    
    def start_auto_buffer(self):
        def update_matrix():
            print("[INFO]: Thread {0} created".format(threading.current_thread().name))
            while not self.stop_thread:
                self.send_pixels()
                time.sleep(0.001)
            print("[INFO]: Thread {0} stopped".format(threading.current_thread().name))
        self.run_async(update_matrix, name="MatrixProtocolAutoBufferThread")

    def stop_auto_buffer(self):
        return self.stop_async()
    
    def simulation_output(self, buf):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        # pretty print the matrix to console for simulation 
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = buf[y][x]
                if r == 0 and g == 0 and b == 0:
                    print("  ", end="")
                else:
                    print("X ", end="")
            print()

if __name__ == "__main__":
    import time

    run = True
        

    try: 
        Matrix = MatrixProtocol(width=50, height=20)
        #ports = Matrix.scan_serial_ports()
        ports = ["COM27"]
        if(len(ports) < 1):
            print("No port found")
            exit()

        Matrix.port = ports[0]
        Matrix.simulation = True
        #if not Matrix.connect():
        #    print("Failed to connect to port")
        #    exit()
        
        Matrix.set_pixel_cmd(10, 10, 255, 0, 0)
        time.sleep(2)

        while run:

            Matrix.textRenderer.clear()
            Matrix.textRenderer.add_text("HOI")
            buf = Matrix.textRenderer.get_buffer()
            Matrix.pixels = buf
            Matrix.send_pixels()
            time.sleep(.1)

            Matrix.textRenderer.clear()
            Matrix.textRenderer.add_text("HOI", line=1)
            buf = Matrix.textRenderer.get_buffer()
            Matrix.pixels = buf
            Matrix.send_pixels()
            time.sleep(.1)

            Matrix.textRenderer.clear()
            Matrix.textRenderer.add_text("E", line=0)
            Matrix.textRenderer.add_text(" T", line=1)
            buf = Matrix.textRenderer.get_buffer()
            Matrix.pixels = buf
            Matrix.send_pixels()
            time.sleep(1)

            Matrix.clear_pixels_buffer()
            Matrix.send_pixels()
            time.sleep(1)


            Matrix.scroll_text("ELEKTROTECHNIK")


            '''
            Matrix.clear_pixels_buffer()
            background = (0, 0, 0)
            foreground = (0, 0, 255)
            text = "ELEKTROTECHNIK"
            disp_width = 16
            disp_height = 16

            disp_buffer = [[background for x in range(disp_width)] for y in range(disp_height)]
            text_buffer = Matrix.textRenderer.render_buffer(text, foreground, background)

            # move text buffer to display buffer from right to left with a step of 1 pixel algin at the top
            for i in range(len(text_buffer[0]) - disp_width):
                for y in range(disp_height):
                    for x in range(disp_width):
                        try:
                            disp_buffer[y][x] = text_buffer[y][i + x]
                        except:
                            pass
                Matrix.pixels = disp_buffer.copy()
                Matrix.send_pixels()
                time.sleep(1/30)
            '''
            


    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        run = False
        Matrix.reset()

    finally:
        if Matrix.ser is not None:
            Matrix.ser.close()

