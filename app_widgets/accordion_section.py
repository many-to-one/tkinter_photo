import customtkinter as ctk

# class AccordionSection(ctk.CTkFrame):
#     def __init__(self, master, title):
#         super().__init__(master)
#         self.pack(fill="x", padx=5, pady=5)

#         self.content = ctk.CTkFrame(self)
#         self.toggle_btn = ctk.CTkButton(self, text=title, fg_color="#333333", command=lambda: self.toggle_section(self.content))
#         self.toggle_btn.pack(fill="x")

def create_accordion_section(parent, title):
    section_frame = ctk.CTkFrame(parent)
    section_frame.pack(fill="x", padx=5, pady=5)

    content = ctk.CTkFrame(section_frame)

    toggle_btn = ctk.CTkButton(section_frame, text=title, fg_color="#333333", command=lambda: toggle_section(content))
    toggle_btn.pack(fill="x")

    return content

def toggle_section(frame):
    if frame.winfo_viewable():
        frame.pack_forget()
    else:
        frame.pack(fill="x", padx=10, pady=5)