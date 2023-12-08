from ipywidgets import Button

class InstallIntegrationButton(Button):
    def __init__(self, value, description, button_style, layout):
        super().__init__()
        self.value = value
        self.description = description
        self.button_style = button_style
        self.layout = layout
        
    def make_button(self):
        return self