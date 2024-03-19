
import serial
import serial.tools.list_ports

class MatrixProtocol:

    def __init__(self, port='None', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def scan_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate)
        self.ser.open()

    def disconnect(self):
        self.ser.close()

    def reset_matrix(self):
        self.ser.write(0x01)

    def get_matrix_size(self):
        self.ser.write(0x05)
        width = self.ser.readline()
        height = self.ser.readline()
        return (width, height)
    
    def set_pixel(self, x, y, color):
        self.ser.write(0x06)
        self.ser.write(x)
        self.ser.write(y)
        self.ser.write(color)



