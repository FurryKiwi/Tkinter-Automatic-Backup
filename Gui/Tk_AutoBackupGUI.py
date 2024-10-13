import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from BackupScripts.Utils import *


class AutomaticBackupGui:
    """Main GUI for selecting Profiles and starting them."""
    def __init__(self, root, controller, icon, silent_start):
        self.controller = controller
        self.windows_icon = icon
        self.root = root
        self.tree_view = None
        self.silent_start_var = None
        self.silent_start = silent_start

        self.profiles = {}

        self.setup_window()
        self.create_window()

        self.load_saved_profiles()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_gui)

        if self.silent_start:
            self.hide_gui()

    def setup_window(self):
        self.root.title("Automatic Backup")
        self.root.after(100, lambda: self.root.wm_iconbitmap(default=ICON_IMG))
        self.hide_gui()

    def set_window_position(self):
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        w, h = (320, 295)
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.root.resizable(False, False)
        self.root.focus_force()

    def create_window(self):
        frame0 = ttk.Frame(self.root)
        btn_width = 0
        ttk.Button(frame0, text="Create Profile", takefocus=False, command=self.controller.create_profile_window,
                   width=btn_width).pack(side='left', padx=10 , pady=4)

        ttk.Button(frame0, text="Open Profiles", takefocus=False, command=open_config,
                   width=btn_width).pack(side='left', padx=10, pady=4)

        ttk.Button(frame0, text="Reload Profiles", takefocus=False, command=self.load_saved_profiles,
                   width=btn_width).pack(side='left', padx=10, pady=4)

        # The Tree view goes here
        frame1 = ttk.Frame(self.root)
        self.tree_view = ttk.Treeview(frame1)
        self.tree_view.heading("#0", text="Loaded Profiles:")
        self.tree_view.pack(side='top', fill='both')
        self.tree_view.bind("<ButtonPress-3>", lambda event: self.pop_up_menu(event))
        self.tree_view.bind("<Double-1>", lambda event=None: self.edit_profile())

        frame2 = ttk.Frame(self.root)
        self.silent_start_var = ttk.Checkbutton(frame2, text="Silent Start:", takefocus=False)
        self.silent_start_var.pack(side='left', padx=10)
        self.silent_start_var.state(["!alternate"])
        if self.silent_start:
            self.silent_start_var.state(["selected"])
        else:
            self.silent_start_var.state(["!selected"])
        self.silent_start_var.bind("<ButtonPress-1>", lambda event: self.toggle_silent_start(event))
        ttk.Button(frame2, text="Start Backup", takefocus=False, command=self.start_backup,
                   width=btn_width).pack(side='left', padx=10)

        ttk.Button(frame2, text="Stop Backup", takefocus=False, command=self.controller.stop_backup,
                   width=btn_width).pack(side='left', padx=15)

        frame0.pack(side='top', fill='x', padx=4)
        frame1.pack(side='top', fill='both', padx=4)
        frame2.pack(side='top', fill='x', padx=4, pady=4)

    def toggle_silent_start(self, event):
        state = event.widget.instate(["!selected"])
        self.controller.toggle_silent_start(state)

    def load_saved_profiles(self):
        self.profiles = self.controller.load_saved_profiles()
        children = self.tree_view.get_children()
        # Delete all children
        for i in children:
            self.tree_view.delete(i)
        # Insert saved profiles back into the tree view
        for i in self.profiles.keys():
            self.tree_view.insert("", 'end', text=i)

    def pop_up_menu(self, event: ttk.Treeview) -> None:
        """Create a popup menu by right-clicking with options."""
        instance = event.widget
        # Listbox drop down menu
        if isinstance(instance, ttk.Treeview):
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Enable Autostart", command=self.enable_autostart)
            menu.add_command(label="Disable Autostart", command=self.controller.disable_autostart)
            menu.add_command(label="Edit", command=self.edit_profile)
            menu.add_command(label="Delete", command=self.remove_elements)

            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def enable_autostart(self):
        selected = list(self.tree_view.selection())
        # If more than 1 selected from the tree view throw error.
        if len(selected) == 1:
            text = self.tree_view.item(selected)['text']
            self.controller.enable_autostart(text)
        else:
            self.windows_icon.notify_user("ERROR:", "Could not set autostart, only one profile can be selected.")

    def remove_elements(self):
        """Removes parents from the tree view."""
        if messagebox.askyesno("Deletion", "Are you sure you want to delete this profile(s)?"):
            selected = list(self.tree_view.selection())
            for i in selected:
                if self.tree_view.exists(i):
                    text = self.tree_view.item(i)['text']
                    del self.profiles[text]
                    self.tree_view.delete(i)
            self.controller.update_profiles(self.profiles)
            self.load_saved_profiles()

    def edit_profile(self):
        selected = list(self.tree_view.selection())
        if len(selected) == 1:
            text = self.tree_view.item(selected)['text']
            config = self.profiles[text]
            self.controller.create_profile_window(config, text)

    def hide_gui(self):
        self.windows_icon.notify_user("INFO:", "Auto Backup is still running in background.", override=True)
        self.root.withdraw()

    def show_gui(self):
        self.set_window_position()
        self.root.deiconify()

    def start_backup(self):
        selection = self.tree_view.selection()
        if len(selection) > 1:
            self.windows_icon.notify_user("ALERT:", "Only one profile can be selected to start at a time.")
            return
        try:
            selected_profile = self.tree_view.item(selection)['text']
            profile = self.profiles[selected_profile]
            self.controller.start_backup(profile, selected_profile)
        except KeyError:
            self.windows_icon.notify_user("ERROR:", "No profile is selected.")
