from .ui import MainApp


class Controller:

    def __init__(self, has_ui: bool = True):
        self.has_ui = has_ui
        if self.has_ui:
            self.ui = MainApp()

    def run(self):
        if self.has_ui:
            self.ui.run()
