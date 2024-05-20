import threading
import serial
import serial.tools.list_ports
import time
import sys

if sys.platform == "linux" or sys.platform == "linux2":
    port = "/dev/ttyACM0"
else:
    port = "COM21"

class Frackstock:

    def __init__(self, port: str):
        self.port = port
        self.ser = None
        self.thread = threading.Thread(target=self.check_serial)
        self.thread.daemon = True  # Daemonize thread
        self.last_data = None
        self.last_data_time = 0
        self.new_data_available = False
        self.stop_thread = False

    def connect(self):
        self.ser = serial.Serial(port, 115200, timeout=1, rtscts=True)
        if not self.ser.isOpen():
            print("Failed to open serial port")
            return False
        print("Serial port opened")
        self.ser.flush()
        self.set_serial(self.ser, "serial 1")
        self.thread.start()  # Start the execution
        return True
    
    def disconnect(self):
        self.stop_thread = True
        self.thread.join()
        self.ser.close()

    def check_serial(self):
        while not self.stop_thread:
            message = None
            if self.ser.in_waiting > 0:
                message = self.ser.readline().decode("utf-8").strip()

            if message:
                if "[RF] RX: {" in message:
                    message = message.replace("[RF] RX: {", "").replace("}", "")
                    message = message.split(", ")
                    data = {}
                    for i in message:
                        i = i.split(": ")
                        data[i[0]] = i[1]
                    
                    self.last_data = data
                    self.last_data_time = time.time()
                    self.new_data_available = True
                    
            time.sleep(.5)  # sleep

    def get_serial(self, ser: serial.Serial, cmd: str):
        cmd = (cmd + "\n").encode("utf-8")
        ser.reset_input_buffer()
        ser.flush()
        ser.write(cmd)
        time.sleep(0.2)
        ret = ser.readline().decode("utf-8").strip()
        ret = ret.replace("\n", "").replace("\r", "")
        return ret

    def set_serial(self, ser: serial.Serial, cmd: str):
        cmd = (cmd + "\n").encode("utf-8")
        ser.reset_input_buffer()
        ser.flush()
        ser.write(cmd)
        time.sleep(0.2)
        ser.flush()

    def radio_send(self, id: int):
        self.set_serial(self.ser, "send to " + str(id))

    def isDataAvailable(self):
        return self.new_data_available
    
    def getData(self):
        self.new_data_available = False
        return self.last_data
        


if __name__ == "__main__":
    frackstock = Frackstock(port="COM21")

    if not frackstock.connect():
        sys.exit(1)
    
    #frackstock.radio_send(0xff)

    while True:
        time.sleep(10)

        frackstock.radio_send(0xff)
    