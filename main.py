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
from kivy.properties import ListProperty, NumericProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.vkeyboard import VKeyboard

# Import the required Python modules
import sys
import threading

# Import the custom modules
from matrix_protocol import MatrixProtocol
from ui.image_tab import ImageTab

# Define the global variables
VERSION = 0.1

WIDTH=16
HEIGHT=16
ASPECT_RATIO=WIDTH/HEIGHT
TOP_KEEPOUT=80
BOTTOM_KEEPOUT=0

restart = False

# Set the window size
Window.size = (800, 480)

Matrix = MatrixProtocol(width=WIDTH, height=HEIGHT)
serial_ports = Matrix.scan_serial_ports()
if len(serial_ports) == 0:
    print("No serial ports found")
    serial_ports = ["/dev/tty/Nönö"]


class PaintWidget(Widget):
    line_color = ListProperty([1, 1, 1])
    line_width = NumericProperty(4)
    
    def __init__(self, **kwargs):
        super(PaintWidget, self).__init__(**kwargs)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.size_hint = (None, None)
        self.height = 300
        self.width = self.height * ASPECT_RATIO

        if self.width > Window.width:
            self.width = Window.width - 20
            self.height = self.width / ASPECT_RATIO

        # Get the size of the window
        window_width, window_height = Window.size
        self.x = (window_width - self.width) / 2
        self.y = (window_height - self.height) / 2 - 60
        self.corners = (self.x, self.y, self.x + self.width, self.y + self.height)       
        self.clear()

    def show_toolbar(self):
        # Add button toolbar at the left side of the canvas
        self.toolbar = BoxLayout(orientation='vertical', size_hint=(None, None), size=(80, self.height))
        self.toolbar.pos = (self.x - 100, self.y)
        self.toolbar.add_widget(Button(text='White', size_hint=(None, None), size=(80, 40), on_press=lambda x: self.set_color([1, 1, 1])))
        self.toolbar.add_widget(Button(text='Black', size_hint=(None, None), size=(80, 40), on_press=lambda x: self.set_color([0, 0, 0])))
        self.toolbar.add_widget(Button(text='Red', size_hint=(None, None), size=(80, 40), on_press=lambda x: self.set_color([1, 0, 0])))
        self.toolbar.add_widget(Button(text='Green', size_hint=(None, None), size=(80, 40), on_press=lambda x: self.set_color([0, 1, 0])))
        self.toolbar.add_widget(Button(text='Blue', size_hint=(None, None), size=(80, 40), on_press=lambda x: self.set_color([0, 0, 1])))
        self.add_widget(self.toolbar)

    def set_color(self, color):
        self.line_color = color
        
    def clear(self):
        self.canvas.clear()
        self.show_toolbar()
        with self.canvas:
            Color(0, 0, 0)
            Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

    def on_touch_down(self, touch):
        try:
            if (self.corners[0] < touch.x < self.corners[2] and self.corners[1] < touch.y < self.corners[3]):
                with self.canvas:
                    Color(*self.line_color)
                    touch.ud['line'] = Line(points=(touch.x, touch.y), width=self.line_width)
                return True
        except Exception as e:
            print(e)
        finally:
            return super(PaintWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        try:
            if (self.corners[0] < touch.x < self.corners[2] and self.corners[1] < touch.y < self.corners[3]):
                touch.ud['line'].points += [touch.x, touch.y]
                return True
        except Exception as e:
            print(e)   
        finally:
            return super(PaintWidget, self).on_touch_move(touch)

class PaintTab(TabbedPanelItem):
    live_event = None

    def __init__(self, **kwargs):
        super(PaintTab, self).__init__(**kwargs)
        self.text = 'Paint'
        box = BoxLayout(orientation='vertical')
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        self.paint_widget = PaintWidget()
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
        

    def on_color(self, instance, value):
        self.paint_widget.line_color = value

    def clear_canvas(self, instance):
        self.paint_widget.clear()

    def save_canvas(self, instance):
        self.paint_widget.export_to_png('drawing.png')
        Matrix.load_image('drawing.png')
        Matrix.send_pixels()

    def live_canvas(self, instance):
        if instance.state == 'down':
            # Call self.save_canvas every 0.1 seconds
            self.live_event = Clock.schedule_interval(self.save_canvas, 0.1)
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
    pixel_color = ListProperty([1, 1, 1])

    def __init__(self, **kwargs):
        super(DrawTab, self).__init__(**kwargs)
        self.text = 'Draw'
        draw_box = BoxLayout(orientation='vertical')
        draw_grid = GridLayout(cols=WIDTH, rows=HEIGHT, size_hint=(1, 1))
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        self.pixel_buttons = []
        for i in range(WIDTH * HEIGHT):
            pixel_button = PixelButton()
            pixel_button.led = i
            self.pixel_buttons.append(pixel_button)
            draw_grid.add_widget(pixel_button)
        draw_box.add_widget(draw_grid)
        
        color_picker = ColorPicker()
        color_picker.bind(color=self.on_color)
        color_picker_popup = Popup(title='Color Picker', content=color_picker, size_hint=(0.8, 0.8))
        color_button = Button(text='Pick Color', on_press=color_picker_popup.open)
        reset_button = Button(text='Reset', on_press=self.reset_pixel_buttons)
        btn_box.add_widget(color_button)
        btn_box.add_widget(reset_button)
        draw_box.add_widget(btn_box)

        self.add_widget(draw_box)

    def reset_pixel_buttons(self, instance):
        for pixel_button in self.pixel_buttons:
            pixel_button.state = 'normal'  # set button state to up

    def on_color(self, instance, value):
        self.pixel_color = value
        for pixel_button in self.pixel_buttons:
            if pixel_button.state == 'down':
                pixel_button.background_color = self.pixel_color
    


class TextTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(TextTab, self).__init__(**kwargs)
        self.text = 'Text'
        self.text_box = GridLayout(cols=1)
        self.text_box.padding = 10
        self.text_box.spacing = 10
        self.text_line_1 = TextInput(text='HELLO', multiline=False, size_hint_y=None, height=52)
        self.text_line_1.font_size = 32
        self.text_line_1.bind(on_touch_down=self.ontouch)
        self.text_box.add_widget(self.text_line_1)
        self.text_line_2 = TextInput(text='WORLD', multiline=False, size_hint_y=None, height=52)
        self.text_line_2.font_size = 32
        self.text_line_2.bind(on_touch_down=self.ontouch)
        self.text_box.add_widget(self.text_line_2)

        self.kb = VKeyboard(
            on_key_up=self.vkbinput,
            pos_hint={'center_x': .5},
            layout='qwertz',
            width=780,
            height=250,
            do_translation=False,
        )
        self.text_box.add_widget(self.kb)

        self.add_widget(self.text_box)
        self.textbox_number = 1
        self.show_keyboard = True

    def ontouch(self, instance, value):
        if instance == self.text_line_1:
            self.textbox_number = 1
        elif instance == self.text_line_2:
            self.textbox_number = 2

        if self.show_keyboard:
            return
        self.show_keyboard = True

        self.kb = VKeyboard(
            on_key_up=self.vkbinput,
            pos_hint={'center_x': .5},
            size_hint=(None, None)
        )
        self.text_box.add_widget(self.kb)

    def send_text(self, instance):
        Matrix.textRenderer.clear()
        Matrix.textRenderer.add_text(self.text_line_1.text, line=0)
        Matrix.textRenderer.add_text(self.text_line_2.text, line=1)
        Matrix.pixels = Matrix.textRenderer.get_buffer()
        Matrix.send_pixels()

    def vkbinput(self, keyboard, keycode, *args):
        if self.textbox_number == 1:
            text = self.text_line_1.text
        elif self.textbox_number == 2:
            text = self.text_line_2.text

        if keycode == 'backspace':
            text = text[:-1]
        elif keycode == 'spacebar':
            text = f'{text} '
        elif keycode == 'enter':
            self.send_text(None)
        elif keycode == 'shift':
            pass
        elif keycode == 'tab':
            pass
        elif keycode == 'capslock':
            pass
        elif keycode == 'escape':
            text = ''
        elif keycode == 'layout':
            pass
        else:
            text = f'{text}{keycode.upper()}'

        if self.textbox_number == 1:
            self.text_line_1.text = text
        elif self.textbox_number == 2:
            self.text_line_2.text = text

        print("Key:", keycode)


class DebugTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(DebugTab, self).__init__(**kwargs)
        self.text = 'Debug'
        self.layout = GridLayout(cols=1)
        self.layout.padding = 10
        self.layout.spacing = 10
        
        restart_button = Button(text='Restart', size_hint_y=None, height=70, on_press=self.restart)
        restart_button.background_color = (0, 1, 0, 1)
        self.layout.add_widget(restart_button)
        stop_button = Button(text='Stop', size_hint_y=None, height=70, on_press=self.stop)
        stop_button.background_color = (0, 0, 1, 1)
        self.layout.add_widget(stop_button)

        self.poweroff_button = Button(text='Power Off', size_hint_y=None, height=70, on_press=self.poweroff_req)
        self.poweroff_button.background_color = (1, 0, 0, 1)
        self.layout.add_widget(self.poweroff_button)

        self.layout.add_widget(Label(text='', size_hint_y=1))

        about_label = Label(text='Frack Matrix v{0}'.format(VERSION), font_size=24, size_hint_y=None, height=30)
        self.layout.add_widget(about_label)
        company_label = Label(text='EberWare GmBH', font_size=16, size_hint_y=None, height=20)
        self.layout.add_widget(company_label)
        author_label = Label(text='by Pascal Eberhard', font_size=16, size_hint_y=None, height=20)
        self.layout.add_widget(author_label)
        

        self.add_widget(self.layout)

    def restart(self, instance):
        global restart
        restart = True
        App.get_running_app().stop()

    def stop(self, instance):
        App.get_running_app().stop()

    def poweroff_req(self, instance):
        # open popup to enter pin
        pin_popup = Popup(title='Power Off', size_hint=(0.5, 0.8))
        pin_box = BoxLayout(orientation='vertical')
        self.pin_input = TextInput(hint_text='Enter PIN', multiline=False, font_size=24, size_hint_y=None, height=60)

        pin_keypad = GridLayout(cols=3)
        for i in range(1, 10):
            button = Button(text=str(i))
            button.bind(on_press=lambda x, i=i: setattr(self.pin_input, 'text', self.pin_input.text + str(i)))
            pin_keypad.add_widget(button)
        pin_keypad.add_widget(Button(text='C', on_press=lambda x: setattr(self.pin_input, 'text', self.pin_input.text[:-1])))
        pin_keypad.add_widget(Button(text='0', on_press=lambda x: setattr(self.pin_input, 'text', self.pin_input.text + '0')))
        pin_keypad.add_widget(Button(text='Enter', on_press=pin_popup.dismiss))
        
        pin_box.add_widget(self.pin_input)
        pin_box.add_widget(pin_keypad)

        pin_popup.content = pin_box
        pin_popup.open()

        # when popup is closed, check pin
        pin_popup.bind(on_dismiss=self.poweroff)
            
    def poweroff(self, instance):
        try:
            if self.pin_input.text == '1234':
                import os
                print("Powering off...")
                os.system("sudo poweroff")
            else:
                print("Nah mate")
        except Exception as e:
            print(e)

    

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
        self.serial_port_spinner.bind(on_press=self.scan)
        connection_box.add_widget(self.serial_port_spinner)

        baud_rate_label = Label(text='Baud Rate:', size_hint_x=0.5)
        connection_box.add_widget(baud_rate_label)
        self.baud_rate_spinner = Spinner(text='115200', values=('9600', '19200', '38400', '57600', '115200'), size_hint_x=0.5)
        connection_box.add_widget(self.baud_rate_spinner)

        self.connect_button = Button(text='Connect', size_hint_x=0.3)
        self.connect_button.bind(on_release=self.connect)
        self.connect_button.background_color = (0, 1, 0, 1)
        connection_box.add_widget(self.connect_button)

        home_box.add_widget(connection_box)

        quick_actions_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10, padding=10)
        quick_actions_label = Label(text='Quick Actions', font_size=24, size_hint_y=None, height=80)
        animation_button = Button(text='Example', size_hint_x=0.3, on_press=self.scrolling_text)
        reset_button = Button(text='Reset', size_hint_x=0.3, on_press=self.reset_matrix)

        quick_actions_box.add_widget(quick_actions_label)
        quick_actions_box.add_widget(animation_button)
        quick_actions_box.add_widget(reset_button)
        home_box.add_widget(Label(text=''))

        home_box.add_widget(quick_actions_box)

        self.add_widget(home_box)

    def connect(self, instance):
        Matrix.port = self.serial_port_spinner.text
        Matrix.baudrate = int(self.baud_rate_spinner.text)
        Matrix.connect()
        self.connect_button.text = 'Disconnect'
        self.connect_button.bind(on_release=self.disconnect)
        self.connect_button.background_color = (1, 0, 0, 1)

    def disconnect(self, instance):
        Matrix.disconnect()
        self.connect_button.text = 'Connect'
        self.connect_button.bind(on_release=self.connect)
        self.connect_button.background_color = (0, 1, 0, 1)

    def scan(self, instance):
        self.serial_ports = Matrix.scan_serial_ports()
        if len(self.serial_ports) == 0:
            self.serial_ports = ["/dev/tty/Nönö"]
        self.serial_port_spinner.values = self.serial_ports

    def reset_matrix(self, instance):
        Matrix.reset()

    def scrolling_text(self, instance):
        text = "ELEKTROTECHNIK"
    
        def scroll_text_in_background():
            Matrix.scroll_text(text, foreground=(0, 255, 255), background=(0, 0, 0))

        threading.Thread(target=scroll_text_in_background).start()




# Define the application class
class FrackMatrixApp(App):

    def __init__(self, **kwargs):
        super(FrackMatrixApp, self).__init__(**kwargs)
        

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

        # Add a new tab named "Image"
        image_tab = ImageTab()
        tab_panel.add_widget(image_tab)

        # Add a new tab named "Paint"
        paint_tab = PaintTab()
        tab_panel.add_widget(paint_tab)

        # Add a new tab named "Debug"
        debug_tab = DebugTab()
        tab_panel.add_widget(debug_tab)

        tab_panel.default_tab = home_tab
        screen.add_widget(tab_panel)
        return screen
    
    def reset_pixel_buttons(self, instance):
        for pixel_button in self.pixel_buttons:
            pixel_button.state = 'normal'  # set button state to up



# Run the application
if __name__ == '__main__':
    FrackMatrixApp().run()


if restart:
    import os
    print("Restarting...")
    os.execv("run.sh", sys.argv)