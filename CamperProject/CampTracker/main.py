"""Main entry point for the Camper Information Management System."""

import tkinter as tk

from gui import BuildGUI

# 1
if __name__ == "__main__":
    root = tk.Tk()
    app = BuildGUI(root)
    root.mainloop()
