import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from BackupScripts.Utils import *
from Gui.CustomTreeView import CustomTreeView


class ProfileWindow(tk.Toplevel):
    """Pop up window for creating and editing Profiles."""
    def __init__(self, root, controller, **kwargs):
        tk.Toplevel.__init__(self, root, **kwargs)
        self.root = root
        self.controller = controller
        self.tree_view = None
        self.dest_var = tk.StringVar()
        self.profile_name = tk.StringVar()
        self.interval_var = None
        self.copies_var = None
        self.method_var = tk.StringVar(value="Rotate")
        self.compression_var = None

        self.protocol("WM_DELETE_WINDOW", self.hide)

        self.setup_window()
        self.create_ui()

    def setup_window(self):
        self.title("Create Profile")
        self.after(100, lambda: self.wm_iconbitmap(default=ICON_IMG))
        self.set_window_position()
        self.focus_force()

    def set_window_position(self):
        ws = self.root.winfo_screenwidth()
        rootx = self.root.winfo_rootx() - (self.root.winfo_width() // 2)
        rooty = self.root.winfo_rooty() - self.root.winfo_height() + 20
        w, h = (350, 540)
        x = ((w // 2) + rootx)
        y = ((h // 2) + rooty)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.resizable(True, True)
        self.wm_minsize(w, h)
        self.wm_maxsize(ws, h)

    def create_ui(self):
        frame0 = ttk.Frame(self)
        ttk.Label(frame0, text="Profile Name:").pack(side='top')
        ttk.Entry(frame0, textvariable=self.profile_name, width=30).pack(side='top')

        frame1 = ttk.Frame(self)
        frame1_0 = ttk.Frame(frame1)
        frame1_0.pack(side='top')
        ttk.Label(frame1_0, text="Destination Folder:").pack(side='left', pady=4)
        ttk.Button(frame1_0, text="Browse", takefocus=False, command=self.browse_dest).pack(side='left')
        ttk.Entry(frame1, textvariable=self.dest_var).pack(side='left', pady=4, fill='x', expand=True)

        frame2 = ttk.Frame(self)
        ttk.Label(frame2, text="Time Interval (seconds):").pack(pady=4, padx=4)
        self.interval_var = (ttk.Spinbox(frame2, values=[str(i) for i in range(self.controller.min_interval,
                                                                               self.controller.max_interval + 1)]))
        self.interval_var.set(self.controller.min_interval)
        self.interval_var.pack(side='top', fill='x')
        ttk.Label(frame2, text="Number of Copies (empty for 1):").pack(pady=4, padx=4)
        self.copies_var = ttk.Spinbox(frame2, values=[str(i) for i in range(self.controller.min_copies,
                                                                            self.controller.max_copies + 1)])
        self.copies_var.set(self.controller.min_copies)
        self.copies_var.pack(side='top', fill='x')
        frame2_0 = ttk.Frame(frame2)
        frame2_0.pack(pady=4)
        ttk.Label(frame2_0, text="Backup Method:").pack(side='left', padx=8)

        ttk.Radiobutton(frame2_0, text="Rotate", takefocus=False, variable=self.method_var, value="Rotate",
                        command=lambda: self.set_backup_method("Rotate")).pack(side='left')
        ttk.Radiobutton(frame2_0, text="OnModified", takefocus=False, variable=self.method_var, value="OnModified",
                        command=lambda: self.set_backup_method("OnModified")).pack(side='left')
        ttk.Radiobutton(frame2_0, text="Daily", takefocus=False, variable=self.method_var, value="Daily",
                        command=lambda: self.set_backup_method("Daily")).pack(side='left')

        frame3 = ttk.Frame(self)
        ttk.Button(frame3, text="Add Folders", takefocus=False, command=self.browse_source).pack(side='top',
                                                                                                 pady=4, padx=4)

        frame3_0 = ttk.Frame(frame3)
        frame3_0.pack(side='top', expand=True, fill='both')
        self.tree_view = CustomTreeView(frame3_0)
        self.tree_view.heading("#0", text="Folders To Backup:")
        self.tree_view.pack(side='top', fill='both')

        frame3_1 = ttk.Frame(frame3)
        frame3_1.pack(side='top')
        self.compression_var = ttk.Checkbutton(frame3_1, text="Do Compression:", takefocus=False)
        self.compression_var.pack(side='left', pady=4, padx=10)
        self.compression_var.state(["!alternate"])
        ttk.Button(frame3_1, text="Save Profile", takefocus=False, command=self.save_profile).pack(side='left',
                                                                                                   pady=4, padx=10)

        frame0.pack(side='top', padx=4, pady=4)
        frame1.pack(side='top', padx=4, expand=True, fill='both')
        frame2.pack(side='top', padx=4, expand=True, fill='both')
        frame3.pack(side='top', padx=4, pady=4, expand=True, fill='both')

    def browse_dest(self):
        folder_path = filedialog.askdirectory(parent=self)
        if folder_path:
            self.dest_var.set(folder_path)

    def browse_source(self):
        folder_path = filedialog.askdirectory(parent=self)
        if folder_path:
            self.tree_view.insert_node("", folder_path)

    def set_backup_method(self, value):
        self.method_var.set(value)

    def save_profile(self):
        config = {
            "Folders": self.tree_view.get_all_elements(),
            "Destination": self.dest_var.get(),
            "Interval": self.interval_var.get(),
            "Copies": self.copies_var.get(),
            "Method": self.method_var.get(),
            "WarningTime": self.controller.min_warning_time,
            "Compression": self.compression_var.instate(['selected'])
        }
        self.controller.save_profile(config, self.profile_name.get())

    def edit_profile(self, config, profile_name):
        self.profile_name.set(profile_name)
        self.dest_var.set(config["Destination"])
        self.interval_var.set(config["Interval"])
        self.copies_var.set(config["Copies"])
        self.method_var.set(config["Method"])
        if config["Compression"]:
            self.compression_var.state(["selected"])
        else:
            self.compression_var.state(["!selected"])
        # Delete all children first before inserting
        children = self.tree_view.get_children()
        if children:
            for i in children:
                self.tree_view.delete(i)
        for i in config["Folders"]:
            self.tree_view.insert_node("", i)

    def hide(self):
        self.withdraw()

    def show(self, clear=False):
        """Shows the Popup window. 'clear' parameter is used for when the 'create_btn' is pressed and is not editing
        an existing profile."""
        if clear:
            self.profile_name.set("")
            self.dest_var.set("")
            self.interval_var.set(self.controller.min_interval)
            self.copies_var.set(self.controller.min_copies)
            self.method_var.set("Rotate")
            self.compression_var.state(["!selected"])
            # Delete all children first before inserting
            children = self.tree_view.get_children()
            if children:
                for i in children:
                    self.tree_view.delete(i)
        self.set_window_position()
        self.deiconify()
