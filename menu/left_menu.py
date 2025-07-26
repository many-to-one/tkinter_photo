import customtkinter as ctk

class LeftSideBar(ctk.CTkFrame):
    def __init__(self, master, width):
        super().__init__(master, width=width)
        self.grid_propagate(False)  # Prevent the frame from resizing to its content

        for i, label in enumerate(["Gr", "Br", "Ct"]):
            btn = ctk.CTkButton(self, text=label, width=20, fg_color="#333333")
            btn.grid(row=i, column=0, padx=5, pady=2, sticky="w")

            if label == "Gr":
                btn.configure(command=lambda: self.optionmenu_callback('Gr'))
            if label == "Br":
                btn.configure(command=lambda: self.optionmenu_callback('Br'))
            if label == "Ct":
                btn.configure(command=lambda: self.optionmenu_callback('Ct'))


    def optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)
        if choice == "Gr":
            self.master.open_gradient_panel()

        # optionmenu = ctk.CTkOptionMenu(self.master, values=["option 1", "option 2"],
        #                                         command=optionmenu_callback)
        # optionmenu.set("option 2")

