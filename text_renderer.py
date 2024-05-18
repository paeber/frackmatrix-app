
from LUTs import LUT_5x7
import numpy as np


class TextRenderer:


    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixels = [[(0, 0, 0) for x in range(self.width)] for y in range(self.height)]
        self.height_offset = 2
        self.char_width = 5
        self.char_height = 7
        self.slot_width = self.char_width + 1
        self.slot_height = self.char_height + 2
        self.no_of_lines = self.width // (self.slot_width)
        self.no_of_columns = self.height // (self.slot_height)


    def clear(self):
        self.pixels = [[(0, 0, 0) for x in range(self.width)] for y in range(self.height)]

    
    def get_buffer(self):
        return self.pixels.copy()


    def add_text(self, text, line=0, slot=0, scale=False, foreground=(255, 255, 255), background=(0, 0, 0)):
        text = text.upper()
        if scale:
            line = slot = 0
        y = (line) * (self.slot_height) + self.height_offset
        x = (slot) * (self.slot_width)
        for char in text:
            if char in LUT_5x7.Characters:
                for i in range(self.char_height):
                    for j in range(self.char_width):
                        if x + j >= self.width or y + i >= self.height:
                            continue
                        self.pixels[y + i][x + j] = foreground if LUT_5x7.Characters[char][i][j] else background
            x += self.char_width + 1
        
        if scale:
            # scale up text buffer to display buffer size
            factor = self.height // self.char_height
            self.pixels = np.repeat(self.pixels, factor, axis=0)
            self.pixels = np.repeat(self.pixels, factor, axis=1)


    def render_buffer(self, text, foreground=(255, 255, 255), background=(0, 0, 0)):
        text = text.upper()
        # init a 2D pixel buffer
        width = len(text) * (self.slot_width)
        height = self.slot_height
        pixel_buffer = [[background for x in range(width)] for y in range(height)]
        x = y = 0
        for char in text:
            if char in LUT_5x7.Characters:
                for i in range(self.char_height):
                    for j in range(self.char_width):
                        pixel_buffer[y + i][x + j] = foreground if LUT_5x7.Characters[char][i][j] else background
                x += self.char_width + 1

        return pixel_buffer
    

if __name__ == "__main__":
    import time

    def plot_scroll_text(text, textRenderer, line=0):
        disp_width = 50
        disp_height = 20

        disp_buffer = [[(0, 0, 0) for x in range(disp_width)] for y in range(disp_height)]
        text_buffer = textRenderer.render_buffer(text)

        # move text buffer to display buffer from right to left with a step of 1 pixel algin at the top
        for i in range(len(text_buffer[0]) - disp_width):
            for y in range(disp_height):
                for x in range(disp_width):
                    try:
                        disp_buffer[y][x] = text_buffer[y][i + x]
                    except:
                        pass
            # print the display buffer
            for row in disp_buffer:
                print("".join(["#" if pixel != (0, 0, 0) else "." for pixel in row]))
            time.sleep(0.1)
            print("\n" * disp_height)




    textRenderer = TextRenderer(50, 20)

    textRenderer.add_text("17", line=0, slot=0)
    textRenderer.add_text("EBER", line=1, slot=0)

    # pretty print with # and . for black and white pixels
    for row in textRenderer.pixels:
        print("".join(["#" if pixel != (0, 0, 0) else "." for pixel in row]))


    buf = textRenderer.render_buffer("ELEKTROTECHNIK")
    for row in buf:
        print("".join(["#" if pixel != (0, 0, 0) else "." for pixel in row]))

    #plot_scroll_text("ELEKTROTECHNIK", textRenderer, line=1)