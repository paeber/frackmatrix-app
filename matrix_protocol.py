
import serial
import serial.tools.list_ports
from PIL import Image

class MatrixProtocol:
    width = 16
    height = 16
    pixels = []

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, width=16, height=16):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.width = width
        self.height = height
        self.pixels = [[(0, 0, 0) for x in range(self.width)] for y in range(self.height)]

    def scan_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self):
        if self.ser is not None:
            return -1

        print("Connect to port: " + self.port)
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        #self.ser.open()

    def disconnect(self):
        if self.ser is None:
            return -1
        print("Disconnect from port: " + self.port)
        self.ser.close()

    def reset_matrix(self):
        if self.ser is None:
            print("Serial port not connected")
            return False
        data = bytes([2])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')

    def xy_to_snake(self, x, y, width):
        if y % 2 == 0:
            return y * width + x
        else:
            return y * width + (width - x - 1)
        
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
    
    def set_pixel_buffer(self, x, y, r, g, b):
        index = self.xy_to_snake(x, y, self.width)
        self.pixels[index // self.width][index % self.width] = (r, g, b)

    def send_pixels(self):
        if self.ser is None:
            print("Serial port not connected")
            return False
        data = bytes([2])
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.pixels[y][x]
                data += bytes([r, g, b])
        self.ser.write(data)
        ret = self.ser.read(1)
        return (ret == b'\x10')
    

    def load_image(self, image_path):
        # Open the image file
        img = Image.open(image_path)
        # Resize the image
        img = img.resize((self.width, self.height))
        # Load the pixel data
        pixels = img.load()
        # Apply the colors to the pixels buffer
        for y in range(self.height):
            for x in range(self.width):
                print(x, y, pixels[x, y])
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
        Matrix.connect()
        
        while run:
            Matrix.set_pixel_buffer(10, 3, 0, 255, 0)
            Matrix.send_pixels()
            time.sleep(1)


    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        run = False

    finally:
        Matrix.ser.close()

    print("done")
