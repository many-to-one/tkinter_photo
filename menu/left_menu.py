import customtkinter as ctk

class LeftSideBar(ctk.CTkFrame):
    def __init__(self, master, width):
        super().__init__(master, width=width)
        self.grid_propagate(False)  # Prevent the frame from resizing to its content

        for i, label in enumerate(["Gr", "Br", "Ct"]):
            btn = ctk.CTkButton(self, text=label, width=20)
            btn.grid(row=i, column=0, padx=5, pady=2, sticky="w")

