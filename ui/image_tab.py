
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.app import App

import sys

class ImageTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(ImageTab, self).__init__(**kwargs)
        self.text = 'Image'
        self.layout = GridLayout(cols=1)
        self.layout.padding = 10
        self.layout.spacing = 10

        self.image_box = BoxLayout(orientation='vertical')
        self.image_box.padding = 10
        self.image_box.spacing = 10

        self.image_button = Button(text='Load Image', size_hint_y=None, height=70, on_press=self.load_image)
        self.image_box.add_widget(self.image_button)

        self.layout.add_widget(self.image_box)
        self.add_widget(self.layout)

    def load_image(self, instance):
        # open file dialog to select image
        from kivy.uix.filechooser import FileChooserIconView
        file_chooser = FileChooserIconView()
        if sys.platform == 'linux':
            file_chooser.path = "/home/pi/Pictures"
        else:
            file_chooser.path = "images"

        file_chooser.bind(on_submit=self.load_image_file)
        file_chooser.bind(on_cancel=self.cancel_image_file)
        self.file_popup = Popup(title='Select Image', content=file_chooser, size_hint=(0.8, 0.8))
        self.file_popup.open()

    def load_image_file(self, instance, value, *args, **kwargs):
        print("Loading image:", value[0])
        if self.file_popup:
            self.file_popup.dismiss()
        app = App.get_running_app()
        matrix = app.matrix
        matrix.load_image(value[0])
        matrix.send_pixels()


    def cancel_image_file(self, instance):
        print("Image selection cancelled")
