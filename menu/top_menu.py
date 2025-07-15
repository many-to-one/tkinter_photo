import customtkinter as ctk

class TopMenu(ctk.CTkFrame):
    def __init__(self, master, height):
        super().__init__(master, height=height)
        self.grid_propagate(False)

        for i, label in enumerate([
                "Open Image", 
                "Save", 
                "Reset"
            ]):
            btn = ctk.CTkButton(self, text=label, width=20, fg_color="#333333")
            btn.grid(row=0, column=i, padx=5, pady=2, sticky="w")
