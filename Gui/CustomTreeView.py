try:
    import Tkinter as tk
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    from tkinter import ttk, messagebox


class CustomTreeView(ttk.Treeview):

    def __init__(self, top_window, *args, **kwargs):
        ttk.Treeview.__init__(self, top_window, *args, **kwargs)
        self.item_selected = None
        self.bind("<ButtonPress-3>", lambda event: self.pop_up_menu(event))
        self.nodes = dict()

    def insert_node(self, parent, text):
        children = self.get_children()
        existing_text = [self.item(i)['text'] for i in children]
        if text not in existing_text:
            node = self.insert(parent, 'end', text=text)
            self.nodes.update({text: node})

    def get_all_elements(self):
        """Returns all the parents and children in the treeview as a dict with their given text."""
        return [i for i in self.nodes.keys()]

    def pop_up_menu(self, event: ttk.Treeview) -> None:
        """Create a popup menu by right-clicking with options."""
        instance = event.widget
        # Listbox drop down menu
        if isinstance(instance, ttk.Treeview):
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Delete", command=self.remove_elements)

            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def remove_elements(self):
        """Removes parents and children from the tree view that are not in the exempt list."""
        selected = list(self.selection())
        for i in selected:
            if self.exists(i):
                text = self.item(i)['text']
                del self.nodes[text]
                self.delete(i)
