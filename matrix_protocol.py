
import serial
import serial.tools.list_ports

class MatrixProtocol:
    width = 16
    height = 16
    pixels = []

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.pixels = [[0 for x in range(self.width)] for y in range(self.height)]

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
        self.ser.write(0x01)

    def get_matrix_size(self):
        self.ser.write(0x05)
        self.ser.flush()
        width = self.ser.readline()
        height = self.ser.readline()
        return (width, height)
    
    def set_pixel(self, x, y, color):
        # color to 16bpp
        color = self.convert_24_to_16_bit_color(color[0], color[1], color[2])
        self.pixels[y][x] = color

    def send_pixels(self):
        self.ser.write(0x12)
        for y in range(self.height):
            for x in range(self.width):
                self.ser.write(self.pixels[y][x] >> 8)
                self.ser.write(self.pixels[y][x] & 0xFF)
        ret = self.ser.read(1)
        print(ret)
        return (ret == 0x06)
    
    def convert_24_to_16_bit_color(self, r, g, b):
        r = r >> 3
        g = g >> 2
        b = b >> 3
        return (r << 11) | (g << 5) | b


if __name__ == "__main__":
    import time

    try: 
        Matrix = MatrixProtocol()
        #ports = Matrix.scan_serial_ports()
        ports = ["/dev/ttyUSB0"]
        if(len(ports) < 1):
            print("No port found")
            exit()

        Matrix.port = ports[0]
        Matrix.connect()

        print("Matrix size: ", Matrix.get_matrix_size())

        Matrix.set_pixel(5, 5, (255, 0, 0))
        time.sleep(1)
        Matrix.send_pixels()


    except Exception as e:
        print(e)
    finally:
        Matrix.ser.close()

    print("done")
