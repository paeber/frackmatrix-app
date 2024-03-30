
import serial
import serial.tools.list_ports
import numpy as np
from PIL import Image
from text_renderer import TextRenderer

class MatrixProtocol:

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, width=16, height=16):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.width = width
        self.height = height
        self.pixels = [[(0, 0, 0) for x in range(self.width)] for y in range(self.height)]
        self.textRenderer = TextRenderer(width, height)
        self.snake = True
        self.mirror = True

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
        return True

    def reset(self):
        if self.ser is None:
            print("Serial port not connected")
            return False
        data = bytes([1])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')

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
    
    def set_pixel_cmd(self, x, y, r, g, b):
        if self.ser is None:
            print("Serial port not connected")
            return False
        index = self.xy_to_snake(x, y, self.width)
        data = bytes([0, index, r, g, b])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')
    
    def set_pixel_buffer(self, x, y, r, g, b, snake=False):
        if snake:
            index = self.xy_to_snake(x, y, self.width)
            self.pixels[index // self.width][index % self.width] = (r, g, b)
        else:
            self.pixels[y][x] = (r, g, b)

    def send_pixels(self, snake=True):
        if self.ser is None:
            print("Serial port not connected")
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
    

    def load_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((self.width, self.height))
        pixels = img.load()
        for y in range(self.height):
            for x in range(self.width):
                r, g, b, a= pixels[x, y]
                self.set_pixel_buffer(x, y, r, g, b)




if __name__ == "__main__":
    import time

    run = True

    try: 
        Matrix = MatrixProtocol()
        #ports = Matrix.scan_serial_ports()
        ports = ["COM12"]
        if(len(ports) < 1):
            print("No port found")
            exit()

        Matrix.port = ports[0]
        if not Matrix.connect():
            print("Failed to connect to port")
            exit()
        
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


    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        run = False

    finally:
        if Matrix.ser is not None:
            Matrix.ser.close()

