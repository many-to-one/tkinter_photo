import customtkinter as ctk

class TopMenu(ctk.CTkFrame):
    def __init__(self, master, height):
        super().__init__(master, height=height)
        self.grid_propagate(False)
