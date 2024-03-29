#!venv/bin/python3

# Import the required Kivy modules
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.properties import ListProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.config import Config
from kivy.clock import Clock

from matrix_protocol import MatrixProtocol

WIDTH=16
HEIGHT=16
ASPECT_RATIO=WIDTH/HEIGHT
TOP_KEEPOUT=120
BOTTOM_KEEPOUT=0

# Set the window size
Window.size = (800, 480)
Window.virtual_keyboard_mode = 'dock'
Config.set('kivy', 'keyboard_mode', 'dock')

Matrix = MatrixProtocol(width=WIDTH, height=HEIGHT)
serial_ports = Matrix.scan_serial_ports()

class PaintWidget(Widget):
    line_color = ListProperty([1, 1, 1])
    
    def __init__(self, **kwargs):
        super(PaintWidget, self).__init__(**kwargs)

        if ASPECT_RATIO > 1:
            self.size_hint_x = None
            self.width = self.height * ASPECT_RATIO
        else:
            self.size_hint_y = None
            self.height = self.width * ASPECT_RATIO
        self.bind(width=self._update_height)

    def _update_height(self, instance, value):
        self.height = value * ASPECT_RATIO

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.y < (self.top - TOP_KEEPOUT) and touch.y > self.y + BOTTOM_KEEPOUT:
            with self.canvas:
                Color(*self.line_color)
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=10)
            return True
        return super(PaintWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and touch.y < (self.top - TOP_KEEPOUT) and touch.y > self.y + BOTTOM_KEEPOUT:
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        return super(PaintWidget, self).on_touch_move(touch)

class PaintTab(TabbedPanelItem):
    live_event = None

    def __init__(self, **kwargs):
        super(PaintTab, self).__init__(**kwargs)
        self.text = 'Paint'
        box = BoxLayout(orientation='vertical')
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        self.paint_widget = PaintWidget()
        self.paint_widget.bind(width=self._update_height)
        color_picker = ColorPicker()
        color_picker.bind(color=self.on_color)
        color_picker_popup = Popup(title='Color Picker', content=color_picker, size_hint=(0.8, 0.8))
        color_button = Button(text='Pick Color')
        color_button.bind(on_press=color_picker_popup.open)
        clear_button = Button(text='Clear')
        clear_button.bind(on_press=self.clear_canvas)
        save_button = Button(text='Save')
        save_button.bind(on_press=self.save_canvas)
        live_button = ToggleButton(text='Live')
        live_button.bind(on_press=self.live_canvas)
        box.add_widget(self.paint_widget)
        btn_box.add_widget(color_button)
        btn_box.add_widget(clear_button)
        btn_box.add_widget(save_button)
        btn_box.add_widget(live_button)
        box.add_widget(btn_box)
        self.add_widget(box)

    def _update_height(self, instance, value):
        self.paint_widget.height = value * ASPECT_RATIO

    def on_color(self, instance, value):
        self.paint_widget.line_color = value

    def clear_canvas(self, instance):
        self.paint_widget.canvas.clear()

    def save_canvas(self, instance):
        self.paint_widget.export_to_png('drawing.png')
        Matrix.load_image('drawing.png')
        Matrix.send_pixels()

    def live_canvas(self, instance):
        if instance.state == 'down':
            # Call self.save_canvas every 0.1 seconds
            self.live_event = Clock.schedule_interval(self.save_canvas, 0.2)
        else:
            # Stop calling self.save_canvas
            self.live_event.cancel()
            


# Define the field button
class PixelButton(ToggleButton):
    led = 0

    def __init__(self, **kwargs):
        super(PixelButton, self).__init__(**kwargs)
        self.background_color = (0, 0, 0, 1)  # black color
        self.bind(state=self.on_state)
        self.size_hint = (1, 1)
        self.touched = False

    def on_state(self, instance, value):
        x = self.led % WIDTH
        y = self.led // WIDTH
        if value == 'down':  # button is pressed
            self.background_color = (1, 1, 1, 1)  # white color
            print(self.led, "on")
            Matrix.set_pixel_cmd(x, y, 100, 100, 100)
        else:
            self.background_color = (0, 0, 0, 1)  # black color
            print(self.led, "off")
            Matrix.set_pixel_cmd(x, y, 0, 0, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'left':
            self.state = 'down'
        return super(PixelButton, self).on_touch_down(touch)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'left':
            self.state = 'normal'
        return super(PixelButton, self).on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'left':
            self.state = 'down'   # simulate a click
            print("move", self.led)
        return super(PixelButton, self).on_touch_move(touch)
    

class DrawTab(TabbedPanelItem):
    color = (1, 0, 0, 1)  # red color

    def __init__(self, **kwargs):
        super(DrawTab, self).__init__(**kwargs)
        self.text = 'Draw'
        draw_box = BoxLayout(orientation='vertical')
        draw_grid = GridLayout(cols=WIDTH, rows=HEIGHT, size_hint=(1, 1))
        self.pixel_buttons = []
        for i in range(WIDTH * HEIGHT):
            pixel_button = PixelButton()
            pixel_button.led = i
            self.pixel_buttons.append(pixel_button)
            draw_grid.add_widget(pixel_button)
        draw_box.add_widget(draw_grid)
        
        reset_button = Button(text='Reset', size_hint_y=None, height=50)
        reset_button.bind(on_press=self.reset_pixel_buttons)
        draw_box.add_widget(reset_button)

        self.add_widget(draw_box)

    def reset_pixel_buttons(self, instance):
        for pixel_button in self.pixel_buttons:
            pixel_button.state = 'normal'  # set button state to up

    


class TextTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(TextTab, self).__init__(**kwargs)
        self.text = 'Text'
        text_box = BoxLayout(orientation='vertical')
        text_box.padding = 10
        text_box.spacing = 10
        spacer = Label(text='')
        text_box.add_widget(spacer)
        self.text_line_1 = TextInput(text='Hello', multiline=False, size_hint_y=None, height=80)
        self.text_line_1.font_size = 36
        text_box.add_widget(self.text_line_1)
        self.text_line_2 = TextInput(text='World', multiline=False, size_hint_y=None, height=80)
        self.text_line_2.font_size = 36
        text_box.add_widget(self.text_line_2)
        btn = Button(text="Send", size_hint_y=None, height=80)
        btn.bind(on_press=self.send_text)
        text_box.add_widget(btn)
        self.add_widget(text_box)

    def send_text(self, instance):
        text = self.text_line_1.text + ' ' + self.text_line_2.text
        print(text)


class HomeTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(HomeTab, self).__init__(**kwargs)
        self.text = 'Home'
        home_box = BoxLayout(orientation='vertical')
        connection_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10, padding=10)

        # Add connection setup UI
        connection_label = Label(text='Connection', font_size=48, size_hint_y=None, height=80)
        home_box.add_widget(connection_label)

        serial_port_label = Label(text='Serial Port:', size_hint_x=0.5)
        connection_box.add_widget(serial_port_label)
        self.serial_port_spinner = Spinner(text=str(serial_ports[0]), values=serial_ports)
        self.serial_port_spinner.size_hint_x = 1
        connection_box.add_widget(self.serial_port_spinner)

        baud_rate_label = Label(text='Baud Rate:', size_hint_x=0.5)
        connection_box.add_widget(baud_rate_label)
        self.baud_rate_spinner = Spinner(text='115200', values=('9600', '19200', '38400', '57600', '115200'), size_hint_x=0.5)
        connection_box.add_widget(self.baud_rate_spinner)

        self.connect_button = Button(text='Connect', size_hint_x=0.3)
        self.connect_button.bind(on_release=self.connect)
        connection_box.add_widget(self.connect_button)

        home_box.add_widget(connection_box)
        home_box.add_widget(Label(text=''))

        self.add_widget(home_box)

    def connect(self, instance):
        Matrix.port = self.serial_port_spinner.text
        Matrix.baudrate = int(self.baud_rate_spinner.text)
        Matrix.connect()
        self.connect_button.text = 'Disconnect'

    def disconnect(self, instance):
        Matrix.disconnect()
        self.connect_button.text = 'Connect'


# Define the application class
class FrackMatrixApp(App):
    def build(self):

        screen = BoxLayout(orientation='vertical')

        # Create a tabbed panel
        tab_panel = TabbedPanel()
        tab_panel.tab_height = TOP_KEEPOUT

        # Add a new tab named "Home"
        home_tab = HomeTab()
        tab_panel.add_widget(home_tab)

        # Add a new tab named "Text"
        text_tab = TextTab()
        tab_panel.add_widget(text_tab)

        # Add a new tab named "Draw"
        draw_tab = DrawTab()
        tab_panel.add_widget(draw_tab)


        # Add a new tab named "Paint"
        paint_tab = PaintTab()
        tab_panel.add_widget(paint_tab)

        tab_panel.default_tab = home_tab
        screen.add_widget(tab_panel)
        return screen
    
    def reset_pixel_buttons(self, instance):
        for pixel_button in self.pixel_buttons:
            pixel_button.state = 'normal'  # set button state to up

# Run the application
if __name__ == '__main__':
    FrackMatrixApp().run()
