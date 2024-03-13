# Import the required Kivy modules
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window

# Set the window size
Window.size = (800, 480)

# Define the field button
class PixelButton(ToggleButton):
    def __init__(self, **kwargs):
        super(PixelButton, self).__init__(**kwargs)
        self.background_color = (0, 0, 0, 1)  # black color
        self.bind(state=self.on_state)
        self.size_hint = (None, None)
        self.width = 16 
        self.height = 16 

    def on_state(self, instance, value):
        if value == 'down':  # button is pressed
            self.background_color = (1, 1, 1, 1)  # white color
        else:
            self.background_color = (0, 0, 0, 1)  # black color

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'left':
            self.state = 'down'  # simulate a click
        return super(PixelButton, self).on_touch_move(touch)

# Define the application class
class FrackMatrixApp(App):
    def build(self):
        # Create a tabbed panel
        tab_panel = TabbedPanel()


        # Add a new tab named "Home"
        home_tab = TabbedPanelItem(text='Home')
        home_box = BoxLayout(orientation='vertical')
        home_box.add_widget(Label(text='Welcome to FrackMatrix!'))
        home_tab.add_widget(home_box)
        tab_panel.add_widget(home_tab)


        # Add a new tab named "Text"
        text_tab = TabbedPanelItem(text='Text')
        text_box = BoxLayout(orientation='vertical')
        text_input = TextInput(text='Enter your text here', multiline=False)
        text_box.add_widget(text_input)
        text_tab.add_widget(text_box)
        tab_panel.add_widget(text_tab)


        # Add a new tab named "Draw"
        draw_tab = TabbedPanelItem(text='Draw')

        box = BoxLayout(orientation='vertical')
        grid = GridLayout(cols=50)
        # Initialize the pixel_buttons list
        self.pixel_buttons = []
        for _ in range(50 * 20):  # 50 columns x 20 rows
            pixel_button = PixelButton()
            self.pixel_buttons.append(pixel_button)
            grid.add_widget(pixel_button)

        box.add_widget(grid)

        # Add a reset button
        reset_button = Button(text='Reset', size_hint_y=None, height=50)
        reset_button.bind(on_press=self.reset_pixel_buttons)
        box.add_widget(reset_button)
        draw_tab.add_widget(box)
        tab_panel.add_widget(draw_tab)


        tab_panel.default_tab = home_tab
        return tab_panel
    
    def reset_pixel_buttons(self, instance):
        for pixel_button in self.pixel_buttons:
            pixel_button.state = 'normal'  # set button state to up

# Run the application
if __name__ == '__main__':
    FrackMatrixApp().run()