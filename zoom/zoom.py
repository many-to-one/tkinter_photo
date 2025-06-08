import customtkinter as ctk


class Zoom(ctk.CTkToplevel):

    def __init__(self, parent, event):
        super().__init__(parent)

        # Zoom logic
        self.zoom_level = 1.0  # Default 100%
        self.zoom_step = 0.1   # 10% per step

        # Zoom with buttons
        self.root.bind('<Control-minus>', self.zoom_out)
        self.root.bind('<Control-plus>', self.zoom_in)
        self.root.bind('<Control-equal>', self.zoom_in)




    def zoom_in(self, event=None):
        self.zoom_level = min(self + self.zoom_step, 10.0)
        self.show_image(self.display_image)

    def zoom_out(self, event=None):
        self.zoom_level = max(self - self.zoom_step, 0.1)
        self.show_image(self.display_image)

    def on_mousewheel(self, event):
        if hasattr(event, 'delta'):
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif event.num == 4:
            self.zoom_in()
        elif event.num == 5:
            self.zoom_out()