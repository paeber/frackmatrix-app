#!venv/bin/python3

# Import the required Kivy modules
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.properties import ListProperty, NumericProperty, StringProperty
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
from animations import Animations
from music import MusicAnalyzer
from frackstock import Frackstock

# Define the global variables
VERSION = 0.4

WIDTH=50
HEIGHT=20
ASPECT_RATIO=WIDTH/HEIGHT
TOP_KEEPOUT=80
BOTTOM_KEEPOUT=0

restart = False
alwayson = False

# Print welcome message
print("Frack Matrix v{0}".format(VERSION))
print(sys.platform)

# Check if the application is running on a Raspberry Pi
if 'linux' in sys.platform:
    Window.cursor = False
    Window.size = (800, 480)
    alwayson = True
elif sys.platform == 'win32':
    Window.show_cursor = True
    Window.size = (800, 480)
elif sys.platform == 'darwin':
    Window.show_cursor = True
    Window.size = (800, 480)
    Window.scale = 2


Matrix = MatrixProtocol(width=WIDTH, height=HEIGHT)
Anims = Animations(Matrix)
serial_ports = Matrix.scan_serial_ports()
if len(serial_ports) == 0:
    print("No serial ports found")
    serial_ports = ["/dev/tty/Nönö"]
    Matrix.simulation = True


class FrackstockTab(TabbedPanelItem):

    def __init__(self, **kwargs):
        super(FrackstockTab, self).__init__(**kwargs)
        self.text = 'Frackstock'
        self.layout = BoxLayout(orientation='vertical')
        self.layout.padding = 10
        self.layout.spacing = 10
        self.frackstock = None
        self.check_event = None

        connection_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10, padding=10)
        connection_label = Label(text='Connection (ACM0)', font_size=36)
        self.layout.add_widget(connection_label)

        serial_port_label = Label(text='Port:', size_hint_x=0.2)
        connection_box.add_widget(serial_port_label)
        self.stock_serial_port_spinner = Spinner(text=str(serial_ports[0]), values=serial_ports)
        self.stock_serial_port_spinner.size_hint_x = 1
        self.stock_serial_port_spinner.bind(on_press=self.scan)
        connection_box.add_widget(self.stock_serial_port_spinner)

        self.stock_connect_button = Button(text='Connect', size_hint_x=0.4)
        self.stock_connect_button.bind(on_release=self.connect)
        self.stock_connect_button.background_color = (0, 1, 0, 1)
        connection_box.add_widget(self.stock_connect_button)

        self.listener_button = ToggleButton(text='Listen', size_hint_x=0.4)
        self.listener_button.bind(on_press=self.frackstock_listen)
        connection_box.add_widget(self.listener_button)

        self.layout.add_widget(connection_box)

        quick_actions_box = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        quick_actions_label = Label(text='Radio', font_size=24)
        self.target_address_slider_high = Slider(min=0, max=15, value=15, step=1)
        self.target_address_slider_low = Slider(min=0, max=15, value=15, step=1)
        self.target_address_slider_high.bind(value=self.set_target_address)
        self.target_address_slider_low.bind(value=self.set_target_address)
        self.target_address_value = Label(text=str(hex(255)), font_size=24)
        send_button = Button(text='Send', size_hint_x=0.5, on_press=self.send)

        quick_actions_box.add_widget(quick_actions_label)

        slider_box = BoxLayout(orientation='vertical')
        slider_box.add_widget(self.target_address_slider_high)
        slider_box.add_widget(self.target_address_slider_low)

        quick_actions_box.add_widget(slider_box)
        quick_actions_box.add_widget(self.target_address_value)
        quick_actions_box.add_widget(send_button)

        self.layout.add_widget(Label(text=''))

        self.layout.add_widget(quick_actions_box)
        self.add_widget(self.layout)

    def set_target_address(self, instance, value):
        high = int(self.target_address_slider_high.value)
        low = int(self.target_address_slider_low.value)
        value = int((high << 4) | low)
        self.target_address_value.text = str(hex(value))

    def scan(self, instance):
        self.serial_ports = Matrix.scan_serial_ports()
        if len(self.serial_ports) == 0:
            self.serial_ports = ["/dev/tty/Nönö"]
        self.stock_serial_port_spinner.values = self.serial_ports

    def connect(self, instance):
        action = instance.text
        if action == "Connect":
            port = self.stock_serial_port_spinner.text
            self.frackstock = Frackstock(port=port)
            self.frackstock.connect()
            self.stock_connect_button.text = 'Disconnect'
            self.stock_connect_button.background_color = (1, 0, 0, 1)
        elif action == "Disconnect":
            self.frackstock.disconnect()
            self.stock_connect_button.text = 'Connect'
            self.stock_connect_button.background_color = [0, 1, 0, 1]

    def send(self, instance):
        if self.frackstock is not None:
            target_address = int(self.target_address_value.text, 16)
            self.frackstock.radio_send(target_address)
        else:
            print("Frackstock not connected")

    def frackstock_listen(self, instance):
        if self.frackstock is None:
            print("Frackstock not connected")
            instance.state = 'normal'
            return
        
        if instance.state == 'down':
            self.check_event = Clock.schedule_interval(self.frackstock_check, 0.5)
        else:
            Clock.unschedule(self.check_event)
            self.check_event = None

    def frackstock_check(self, dt):
        if self.frackstock is not None:
            if self.frackstock.isDataAvailable():
                data = self.frackstock.getData()
                print(data)
                try:
                    r, g, b = data['color'].split(' ')
                    color = (int(r), int(g), int(b))
                except Exception as e:
                    color = (0, 255, 0)
                msg = f"{hex(int(data['from']))[:2]}: {data['beer']}"
                #Matrix.scroll_text(text=msg, foreground=color, background=(0, 0, 0), fill=True, blank=True)

                Matrix.textRenderer.clear()
                Matrix.textRenderer.add_text(f"{hex(int(data['from']))}", line=0, foreground=color, background=(0, 0, 0))
                Matrix.textRenderer.add_text(f" {data['beer']} BEER", line=1, foreground=color, background=(0, 0, 0))
                Matrix.pixels = Matrix.textRenderer.get_buffer()
                Matrix.send_pixels()

    





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
            self.width = Window.width
            self.height = self.width / ASPECT_RATIO

        # Get the size of the window
        window_width, window_height = Window.size
        self.x = (window_width / 2) - (self.width / 2)
        self.y = (window_height / 2) - (self.height / 2)
        self.corners = (self.x, self.y, self.x + self.width, self.y + self.height)      
        self.clear()


    def set_color(self, color):
        self.line_color = color
        
    def clear(self):
        self.canvas.clear()
        self.x = self.corners[0]
        self.y = self.corners[1]
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
            print("Exception:", e)
        finally:
            return super(PaintWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        try:
            if (self.corners[0] < touch.x < self.corners[2] and self.corners[1] < touch.y < self.corners[3]):
                touch.ud['line'].points += [touch.x, touch.y]
                return True
        except Exception as e:
            print("Exception:", e)   
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
       
        color_spinner = Spinner(text='White', values=('White', 'Black', 'Red', 'Green', 'Blue', 'Custom'))
        color_spinner.bind(text=self.new_color)
        clear_button = Button(text='Clear')
        clear_button.bind(on_press=self.clear_canvas)
        save_button = Button(text='Save')
        save_button.bind(on_press=self.save_canvas)
        live_button = ToggleButton(text='Live')
        live_button.bind(on_press=self.live_canvas)

        box.add_widget(self.paint_widget)
        btn_box.add_widget(color_spinner)
        btn_box.add_widget(clear_button)
        btn_box.add_widget(save_button)
        btn_box.add_widget(live_button)
        box.add_widget(btn_box)
        self.add_widget(box)
        
    def new_color(self, instance, value):
        if value == 'White':
            self.paint_widget.line_color = [1, 1, 1]
        elif value == 'Black':
            self.paint_widget.line_color = [0, 0, 0]
        elif value == 'Red':
            self.paint_widget.line_color = [1, 0, 0]
        elif value == 'Green':
            self.paint_widget.line_color = [0, 1, 0]
        elif value == 'Blue':
            self.paint_widget.line_color = [0, 0, 1]
        elif value == 'Custom':
            color_picker = ColorPicker()
            color_picker.bind(color=self.on_color)
            color_picker_popup = Popup(title='Color Picker', content=color_picker, size_hint=(0.8, 0.8))
            color_picker_popup.open()

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
            self.live_event = Clock.schedule_interval(self.save_canvas, 0.2)
        else:
            # Stop calling self.save_canvas
            self.live_event.cancel()



class TextTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(TextTab, self).__init__(**kwargs)
        self.text = 'Text'
        self.text_color_fg = (255, 255, 255)
        self.text_color_bg = (0, 0, 0)
        self.text_box = GridLayout(cols=1)
        self.text_box.padding = 10
        self.text_box.spacing = 10

        self.color_spinner_fg = Spinner(text='White', values=('White', 'Black', 'Red', 'Green', 'Blue', 'Purple', 'Orange', 'Yellow'), size_hint_x=0.2)
        self.color_spinner_fg.bind(text=self.set_foreground_color)
        self.color_spinner_bg = Spinner(text='Black', values=('Black', 'White', 'Red', 'Green', 'Blue', 'Purple', 'Orange', 'Yellow'), size_hint_x=0.2)
        self.color_spinner_bg.bind(text=self.set_background_color)

        box_1 = BoxLayout(orientation='horizontal')
        self.text_line_1 = TextInput(text='HELLO', multiline=False, size_hint_y=None, height=52)
        self.text_line_1.font_size = 32
        self.text_line_1.bind(on_touch_down=self.ontouch)
        self.check_scroll_1 = CheckBox(size_hint_x=None, width=50)
        self.check_fill_1 = CheckBox(size_hint_x=None, width=50)
        
        box_options_1 = GridLayout(cols=2, size_hint_x=None, width=100)
        box_options_1.add_widget(Label(text='Scroll', size_hint_x=None, width=50))
        box_options_1.add_widget(Label(text='Fill', size_hint_x=None, width=50))
        box_options_1.add_widget(self.check_scroll_1)
        box_options_1.add_widget(self.check_fill_1)
        box_1.add_widget(self.text_line_1)
        box_1.add_widget(box_options_1)
        box_1.add_widget(self.color_spinner_fg)
        self.text_box.add_widget(box_1)

        box_2 = BoxLayout(orientation='horizontal')
        self.text_line_2 = TextInput(text='WORLD', multiline=False, size_hint_y=None, height=52)
        self.text_line_2.font_size = 32
        self.text_line_2.bind(on_touch_down=self.ontouch)
        self.check_scroll_2 = CheckBox(size_hint_x=None, width=50)
        self.check_fill_2 = CheckBox(size_hint_x=None, width=50)
        box_options_2 = GridLayout(cols=2, size_hint_x=None, width=100)
        box_options_2.add_widget(Label(text='Scroll', size_hint_x=None, width=50))
        box_options_2.add_widget(Label(text='Fill', size_hint_x=None, width=50))
        box_options_2.add_widget(self.check_scroll_2)
        box_options_2.add_widget(self.check_fill_2)
        box_2.add_widget(self.text_line_2)
        box_2.add_widget(box_options_2)
        box_2.add_widget(self.color_spinner_bg)

        self.text_box.add_widget(box_2)

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

    def text_to_color(self, text):
        if text == 'Black':
            return (0, 0, 0)
        elif text == 'White':
            return (255, 255, 255)
        elif text == 'Red':
            return (255, 0, 0)
        elif text == 'Green':
            return (0, 255, 0)
        elif text == 'Blue':
            return (0, 0, 255)
        elif text == 'Purple':
            return (255, 0, 255)
        elif text == 'Orange':
            return (255, 165, 0)
        elif text == 'Yellow':
            return (255, 255, 0)

    def set_foreground_color(self, instance, value):
        color = self.text_to_color(value)
        self.text_color_fg = color
        self.color_spinner_fg.background_color = color

    def set_background_color(self, instance, value):
        color = self.text_to_color(value)
        self.text_color_bg = color
        self.color_spinner_bg.background_color = color


    def send_text(self, instance):
        if self.check_scroll_1.active:
            def scroll_text_in_background():
                Matrix.scroll_text(text=self.text_line_1.text, foreground=self.text_color_fg, background=self.text_color_bg, fill=self.check_fill_1.active, blank=True)

            Matrix.run_async(scroll_text_in_background)

        elif self.check_scroll_2.active:
            def scroll_text_in_background():
                Matrix.scroll_text(text=self.text_line_2.text, foreground=self.text_color_fg, background=self.text_color_bg, fill=self.check_fill_2.active, blank=True)

            Matrix.run_async(scroll_text_in_background)

        else:
            Matrix.textRenderer.clear()
            Matrix.textRenderer.add_text(self.text_line_1.text, line=0, foreground=self.text_color_fg, background=self.text_color_bg)
            Matrix.textRenderer.add_text(self.text_line_2.text, line=1, foreground=self.text_color_fg, background=self.text_color_bg)
            Matrix.pixels = Matrix.textRenderer.get_buffer()
            Matrix.send_pixels()

    def vkbinput(self, keyboard, keycode, *args):
        ignore = ['shift', 'tab', 'capslock', 'layout']
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
        elif keycode == 'escape':
            text = ''
        elif keycode in ignore:
            pass
        else:
            text = f'{text}{keycode.upper()}'

        if self.textbox_number == 1:
            self.text_line_1.text = text
        elif self.textbox_number == 2:
            self.text_line_2.text = text



class AnimationTab(TabbedPanelItem):

    def __init__(self, **kwargs):
        super(AnimationTab, self).__init__(**kwargs)
        self.text = 'Animation'
        self.layout = GridLayout(cols=1)
        self.layout.padding = 10
        self.layout.spacing = 10

        # Status row
        status_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=70)
        status_label = Label(text='Status:')
        self.status_label = Label(text='Stopped', size_hint_x=0.4)
        stop_button = Button(text='Stop', size_hint_x=0.3, on_press=self.stop_animation)
        color_spinner = Spinner(text='White', values=('White', 'Red', 'Green', 'Blue', 'Purple', 'Orange', 'Yellow'))
        color_spinner.bind(text=self.set_animation_color)
        status_box.add_widget(status_label)
        status_box.add_widget(self.status_label)
        status_box.add_widget(stop_button)
        status_box.add_widget(color_spinner)
        self.layout.add_widget(status_box)

        # Radio buttons for selecting the animation
        wave_box = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        wave_label = Label(text='Wave')
        sine_button = ToggleButton(text='Sine', group='animation', on_press=self.set_new_animation)
        square_button = ToggleButton(text='Square', group='animation', on_press=self.set_new_animation)
        saw_button = ToggleButton(text='Saw', group='animation', on_press=self.set_new_animation)

        wave_box.add_widget(wave_label)
        wave_box.add_widget(sine_button)
        wave_box.add_widget(square_button)
        wave_box.add_widget(saw_button)
        self.layout.add_widget(wave_box)

        # Parameters for the animation
        param_box = GridLayout(cols=3, size_hint_y=0.4)
        param_box.add_widget(Label(text='Frequency'))
        self.freq_slider = Slider(min=0.1, max=10, value=4, step=0.1, on_touch_move=self.set_params)
        self.freq_value = Label(text=str(self.freq_slider.value))
        param_box.add_widget(self.freq_slider)
        param_box.add_widget(self.freq_value)

        param_box.add_widget(Label(text='Amplitude'))
        self.amp_slider = Slider(min=0, max=1, value=0.9, step=0.1, on_touch_move=self.set_params)
        self.amp_value = Label(text=str(self.amp_slider.value))

        param_box.add_widget(self.amp_slider)
        param_box.add_widget(self.amp_value)

        param_box.add_widget(Label(text='Duty Cycle'))
        self.dc_slider = Slider(min=0, max=1, value=0.5, step=0.1, on_touch_move=self.set_params)
        self.dc_value = Label(text=str(self.dc_slider.value))
        param_box.add_widget(self.dc_slider)
        param_box.add_widget(self.dc_value)

        self.layout.add_widget(param_box)


        # Radio buttons for selecting special apps
        app_box = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        app_label = Label(text='Special')
        clock_button = ToggleButton(text='Clock', group='animation', on_press=self.set_new_animation)
        rainbow_button = ToggleButton(text='Rainbow', group='animation', on_press=self.set_new_animation)
        fire_button = ToggleButton(text='Fire', group='animation', on_press=self.set_new_animation)
        raindrops_button = ToggleButton(text='Raindrops', group='animation', on_press=self.set_new_animation)
        
        app_box.add_widget(app_label)
        app_box.add_widget(clock_button)
        app_box.add_widget(rainbow_button)
        app_box.add_widget(fire_button)
        app_box.add_widget(raindrops_button)
        self.layout.add_widget(app_box)

        self.add_widget(self.layout)

    def stop_animation(self, instance):
        Anims.stop()
        self.status_label.text = 'Stopped'

    def set_params(self, instance, value):
        Anims.freq = self.freq_slider.value
        Anims.A = self.amp_slider.value
        Anims.dc = self.dc_slider.value
        self.freq_value.text = str(round(self.freq_slider.value, 2))
        self.amp_value.text = str(round(self.amp_slider.value, 2))
        self.dc_value.text = str(round(self.dc_slider.value, 2))

    def set_animation_color(self, instance, value):
        color = instance.text
        if color == 'White':
            Anims.color = (255, 255, 255)
        elif color == 'Red':
            Anims.color = (255, 0, 0)
        elif color == 'Green':
            Anims.color = (0, 255, 0)
        elif color == 'Blue':
            Anims.color = (0, 0, 255)   
        elif color == 'Purple':
            Anims.color = (255, 0, 255)
        elif color == 'Orange':
            Anims.color = (255, 165, 0)
        elif color == 'Yellow':
            Anims.color = (255, 255, 0)

    def set_new_animation(self, instance):
        Anims.stop()
        if instance.state == 'down':
            self.status_label.text = 'Running'
            if instance.text == 'Sine':
                Anims.func = Anims.sine_wave
            elif instance.text == 'Square':
                Anims.func = Anims.square_wave
            elif instance.text == 'Saw':
                Anims.func = Anims.sawtooth_wave
            elif instance.text == 'Clock':
                Anims.func = Anims.clock
            elif instance.text == 'Raindrops':
                Anims.func = Anims.raindrops
            elif instance.text == 'Random':
                Anims.func = Anims.random_pixels
            elif instance.text == 'Rainbow':
                Anims.func = Anims.rainbow
            Anims.start()


class MusicTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = 'Music'
        self.layout = BoxLayout(orientation='vertical')
        self.layout.padding = 10
        self.layout.spacing = 10
        self.music_analyzer = MusicAnalyzer(matrix=Matrix, visu_mode="timeline")

        info_box = BoxLayout(orientation='horizontal')
        info_label = Label(text='Info:', size_hint_x=0.2)
        self.info_label = Label(text='Stopped', size_hint_x=0.8)
        info_box.add_widget(info_label)
        info_box.add_widget(self.info_label)
        
        # self.open_button = Button(text='Open Stream', size_hint_x=0.5)
        # self.open_button.bind(on_press=self.open_stream)
        # self.close_button = Button(text='Close Stream', size_hint_x=0.5)
        # self.close_button.bind(on_press=self.close_stream)
        # self.layout.add_widget(self.open_button)
        # self.layout.add_widget(self.close_button)

        self.start_button = Button(text='Start', size_hint_x=0.5)
        self.start_button.bind(on_press=self.start)
        self.stop_button = Button(text='Stop', size_hint_x=0.5)
        self.stop_button.bind(on_press=self.stop)
        info_box.add_widget(self.start_button)
        info_box.add_widget(self.stop_button)

        self.layout.add_widget(info_box)

        visu_mode_label = Label(text='Visualization Mode:', size_hint_x=0.5)
        self.layout.add_widget(visu_mode_label)
        timeline_button = ToggleButton(text='Timeline', group='visu_mode', size_hint_x=0.5)
        timeline_button.bind(on_press=self.set_visu_mode)
        self.layout.add_widget(timeline_button)
        timeline_dual_button = ToggleButton(text='Timeline Dual', group='visu_mode', size_hint_x=0.5)
        timeline_dual_button.bind(on_press=self.set_visu_mode)
        self.layout.add_widget(timeline_dual_button)
        circle_button = ToggleButton(text='Circle', group='visu_mode', size_hint_x=0.5)
        circle_button.bind(on_press=self.set_visu_mode)
        self.layout.add_widget(circle_button)

        self.add_widget(self.layout)

    def open_stream(self, instance):
        self.music_analyzer.open_stream()
        # check if stream is open
        if self.music_analyzer.stream.is_active():
            print("Stream is open")
    
    def close_stream(self, instance):
        self.music_analyzer.close_stream()

    def start(self, instance):
        self.music_analyzer.start()
        self.info_label.text = 'Running'
    
    def stop(self, instance):
        self.music_analyzer.stop()
        self.info_label.text = 'Stopped'

    def set_visu_mode(self, instance):
        visu_mode = instance.text.lower()
        visu_mode = visu_mode.replace(' ', '_')
        self.music_analyzer.visu_mode = visu_mode
        print("Visualization mode set to", visu_mode)
    



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
        global restart, alwayson
        alwayson = False
        restart = False
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
        connection_label = Label(text='Matrix Connection (USB0)', font_size=36, size_hint_y=None, height=80)
        home_box.add_widget(connection_label)

        serial_port_label = Label(text='Port:', size_hint_x=0.2)
        connection_box.add_widget(serial_port_label)
        self.serial_port_spinner = Spinner(text=str(serial_ports[0]), values=serial_ports)
        self.serial_port_spinner.size_hint_x = 1
        self.serial_port_spinner.bind(on_press=self.scan)
        connection_box.add_widget(self.serial_port_spinner)

        baud_rate_label = Label(text='Baud:', size_hint_x=0.2)
        connection_box.add_widget(baud_rate_label)
        self.baud_rate_spinner = Spinner(text='1000000', values=('9600', '115200', '250000', '500000', '1000000'), size_hint_x=0.5)
        connection_box.add_widget(self.baud_rate_spinner)

        self.connect_button = Button(text='Connect', size_hint_x=0.4)
        self.connect_button.bind(on_release=self.connect)
        self.connect_button.background_color = (0, 1, 0, 1)
        connection_box.add_widget(self.connect_button)

        home_box.add_widget(connection_box)

        quick_actions_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10, padding=10)
        quick_actions_label = Label(text='Quick Actions', font_size=24, size_hint_y=None, height=80)
        animation_button = Button(text='Example', size_hint_x=0.3, on_press=self.scrolling_text)
        reset_button = Button(text='Reset', size_hint_x=0.3, on_press=self.reset_matrix)
        kill_thread = Button(text='Kill Thread', size_hint_x=0.3, on_press=self.kill_thread)

        quick_actions_box.add_widget(quick_actions_label)
        quick_actions_box.add_widget(animation_button)
        quick_actions_box.add_widget(reset_button)
        quick_actions_box.add_widget(kill_thread)

        home_box.add_widget(Label(text=''))

        home_box.add_widget(quick_actions_box)

        self.add_widget(home_box)

    def connect(self, instance):
        action = instance.text
        if action == "Connect":
            Matrix.simulation = False
            Matrix.port = self.serial_port_spinner.text
            Matrix.baudrate = int(self.baud_rate_spinner.text)
            Matrix.connect()
            self.connect_button.text = 'Disconnect'
            self.connect_button.background_color = (1, 0, 0, 1)
        elif action == "Disconnect":
            Matrix.disconnect()
            Matrix.simulation = True
            self.connect_button.text = 'Connect'
            self.connect_button.background_color = [0, 1, 0, 1]

    def scan(self, instance):
        self.serial_ports = Matrix.scan_serial_ports()
        if len(self.serial_ports) == 0:
            self.serial_ports = ["/dev/tty/Nönö"]
        self.serial_port_spinner.values = self.serial_ports

    def reset_matrix(self, instance):
        Matrix.reset()

    def kill_thread(self, instance):
        if Matrix.thread is not None:
            Matrix.stop_thread = True
            Matrix.thread.join()
            Matrix.thread = None

    def scrolling_text(self, instance):
        text = "ELEKTROTECHNIK"
    
        def scroll_text_in_background():
            Matrix.scroll_text(text, foreground=(0, 255, 255), background=(0, 0, 0))

        Matrix.run_async(scroll_text_in_background)




# Define the application class
class FrackMatrixApp(App):
    matrix = Matrix
    active_tab = "Home"

    def __init__(self, **kwargs):
        super(FrackMatrixApp, self).__init__(**kwargs)
        

    def build(self):

        screen = BoxLayout(orientation='vertical')

        # Create a tabbed panel
        tab_panel = TabbedPanel()
        #tab_panel.tab_height_hint = 0.15
        tab_panel.tab_height = 80

        # Add a new tab named "Home"
        home_tab = HomeTab()
        tab_panel.add_widget(home_tab)

        # Add a new tab named "Animation"
        animation_tab = AnimationTab()
        tab_panel.add_widget(animation_tab)

        # Add a new tab named "Music"
        music_tab = MusicTab()
        tab_panel.add_widget(music_tab)

        # Add a new tab named "Text"
        text_tab = TextTab()
        tab_panel.add_widget(text_tab)

        # Add a new tab named "Image"
        image_tab = ImageTab()
        tab_panel.add_widget(image_tab)

        # Add a new tab named "Paint"
        paint_tab = PaintTab()
        tab_panel.add_widget(paint_tab)

        # Add a new tab named "Frackstock"
        frackstock_tab = FrackstockTab()
        tab_panel.add_widget(frackstock_tab)

        # Add a new tab named "Debug"
        debug_tab = DebugTab()
        tab_panel.add_widget(debug_tab)

        tab_panel.default_tab = home_tab

        tab_panel.bind(current_tab=self.on_tab_switch)
        screen.add_widget(tab_panel)
        return screen
    
    def on_tab_switch(self, instance, value):
        print(f'Tab switched from {self.active_tab} to {value.text}')
        self.active_tab = value.text



# Run the application
if __name__ == '__main__':
    try:
        FrackMatrixApp().run()
    except Exception as e:
        print("[ERROR]", e)
    finally:
        if restart or alwayson:
            import os
            print("Restarting...")
            os.execv("run.sh", sys.argv)