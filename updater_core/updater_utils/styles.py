from ipywidgets import Button

class ButtonMaker(Button):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.value = kwargs["value"]
        self.description = kwargs["description"]
        self.button_style = kwargs["button_style"]
        self.layout = kwargs["layout"]
        self.origin = kwargs["origin"]
        
    def make_button(self):
        return self