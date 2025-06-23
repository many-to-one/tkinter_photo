import customtkinter as ctk
import tkinter as tk
import threading
from concurrent.futures import ThreadPoolExecutor


class InfoWindow(ctk.CTkToplevel):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.title("Image Editor")
        self.geometry("300x100")
        self.grab_set()  # Block interaction with main window
        self.resizable(False, False)
        self.answer = tk.BooleanVar(value=False)

        # Get screen width and height from parent
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()

        # Calculate position to center window
        window_width = 300
        window_height = 100
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

        # Apply centered geometry
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Display message
        label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=14), text_color="white")
        label.pack(expand=True, fill="both", padx=10, pady=10)

        cont = ctk.CTkFrame(self, height=30) 
        cont.pack(pady=5, padx=5, fill="x")

        # Inner frame to center buttons
        btn_frame = ctk.CTkFrame(cont)
        btn_frame.pack(anchor="center")

        btn = ctk.CTkButton(btn_frame, text=f"Yes", width=60, command=lambda: self.close_info_window(True))
        btn.pack(side="left", padx=10)

        btn = ctk.CTkButton(btn_frame, text=f"No", width=60, command=lambda: self.close_info_window(False))
        btn.pack(side="right", padx=10)

    def get_answer(self):
        self.wait_window()
        return self.answer.get()


    def close_info_window(self, value):
        """Close the info window when saving is complete."""
        self.answer.set(value)
        self.destroy()
