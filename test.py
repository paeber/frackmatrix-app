import serial
import time

run = True
port = "COM12"

x = y = 0

width = 16
height = 16


rgb_pixels = [[(0, 0, 0) for x in range(width)] for y in range(height)]


ser = serial.Serial(port, 115200, timeout=1)

def xy_to_snake(x, y, width):
    if y % 2 == 0:
        return y * width + x
    else:
        return y * width + (width - x - 1)
    
def clear_pixels_buffer():
    for y in range(height):
        for x in range(width):
            rgb_pixels[y][x] = (0, 0, 0)

def set_pixel_cmd(x, y, r, g, b):
    index = xy_to_snake(x, y, width)
    data = bytes([0, index, r, g, b])
    ser.write(data)
    ret = ser.read(1)
    return (ret == b'\x10')

def set_pixel_buffer(x, y, r, g, b):
    index = xy_to_snake(x, y, width)
    rgb_pixels[index // width][index % width] = (r, g, b)

def send_pixels():
    data = bytes([2])
    for y in range(height):
        for x in range(width):
            r, g, b = rgb_pixels[y][x]
            data += bytes([r, g, b])
    ser.write(data)
    ret = ser.read(1)
    return (ret == b'\x10')




try:
  
    while run:
        
        clear_pixels_buffer()
        set_pixel_buffer(10, 3, 0, 255, 0)
        set_pixel_buffer(10, 4, 0, 255, 0)
        set_pixel_buffer(10, 5, 0, 255, 0)
        set_pixel_buffer(10, 6, 0, 255, 0)
        set_pixel_buffer(10, 7, 0, 255, 0)
        set_pixel_buffer(10, 8, 0, 255, 0)
        set_pixel_buffer(10, 10, 0, 255, 0)
        set_pixel_buffer(11, 10, 0, 255, 0)
        set_pixel_buffer(12, 10, 0, 255, 0)
        set_pixel_buffer(13, 10, 0, 255, 0)
        send_pixels()

        time.sleep(1/30)
        
        clear_pixels_buffer()
        set_pixel_buffer(6, 3, 0, 255, 0)
        set_pixel_buffer(6, 4, 0, 255, 0)
        set_pixel_buffer(6, 5, 0, 255, 0)
        set_pixel_buffer(6, 6, 0, 255, 0)
        set_pixel_buffer(6, 7, 0, 255, 0)
        set_pixel_buffer(6, 8, 0, 255, 0)
        set_pixel_buffer(6, 6, 0, 255, 0)
        set_pixel_buffer(11, 6, 0, 255, 0)
        set_pixel_buffer(12, 6, 0, 255, 0)
        set_pixel_buffer(13, 6, 0, 255, 0)
        send_pixels()

        time.sleep(1/30)
        

except Exception as e:
    run = False
    print(e)

except KeyboardInterrupt:
    print("Keyboard interrupt")
    run = False

finally:
    print("Closing serial port")
    ser.close()