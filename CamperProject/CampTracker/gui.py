"""GUI implementation for the Camper Information Management System using Tkinter."""

from operator import ne
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from logic import (
    handle_submit,
    fetch_campers,
    save_all_campers,
    delete_camper_by_number,
    create_db_backup,
)
from PIL import Image, ImageTk
from models import VALID_PHONE_CHARS
from symspellpy.symspellpy import SymSpell, Verbosity


# from itertools import islice


# GUI setup
class BuildGUI:
    """Builds the GUI for the Camper Information Management System."""

    def __init__(self, root):
        self.root = root
        self.root.title("Camper Information")
        self.tree: Optional[ttk.Treeview] = (
            None  # Initialize tree attribute with type hint
        )

        # Initialize SymSpell
        self.sym_spell = SymSpell()
        # Get the path to the dictionary file
        dictionary_path = os.path.join(
            os.path.dirname(__file__), "assets", "frequancy.txt"
        )
        self.sym_spell.load_dictionary(dictionary_path, 0, 1, " ")
        # Print out first 5 elements to demonstrate that dictionary is
        # successfully loaded
        # (previous) print(list(islice(self.sym_spell.words.items(), 5))) # type: ignore

        # Load star images
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.star_empty = ImageTk.PhotoImage(
            Image.open(os.path.join(assets_dir, "empty.png")).resize((20, 20))
        )
        self.star_half = ImageTk.PhotoImage(
            Image.open(os.path.join(assets_dir, "half.png")).resize((20, 20))
        )
        self.star_full = ImageTk.PhotoImage(
            Image.open(os.path.join(assets_dir, "full.png")).resize((20, 20))
        )

        # Load lightbulb image
        self.lightbulb = ImageTk.PhotoImage(
            Image.open(os.path.join(assets_dir, "lightbulb.png")).resize((10, 10))
        )

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Create tabs
        self.input_frame = ttk.Frame(self.notebook, padding="10")
        self.search_frame = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.input_frame, text="Add Camper")
        self.notebook.add(self.search_frame, text="Search")

        # Setup input tab
        self.setup_input_tab()
        # Setup search tab
        self.setup_search_tab()

        self.tooltip = tk.Label(
            self.root,
            text="Left click on the star for full stars and right click for half stars.",
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=1,
        )

        self.tooltip_suggestion = tk.Label(
            self.root,
            text="",
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=1,
        )
        # Make tooltip clickable
        self.tooltip_suggestion.bind("<Button-1>", self.replace_with_suggestion)
        self._suggestion_indices = None
        self._suggestion_text = None
        self._tooltip_hide_job = None             
        self.tooltip_suggestion.bind("<Enter>", self.cancel_hide_tooltip)
        self.tooltip_suggestion.bind("<Leave>", self.schedule_hide_tooltip)

        # Note input with word wrap and spellcheck
        ttk.Label(self.input_frame, text="Note:").grid(row=5, column=0, sticky=tk.W)
        self.note_entry = tk.Text(self.input_frame, height=3, width=30, wrap=tk.WORD)
        self.note_entry.grid(row=6, column=1, padx=5, pady=2, sticky=tk.W)
        self.note_entry.tag_config("misspelled", underline=True, foreground="red")
        self.note_entry.bind("<space>", self.check_spelling)
        self.note_entry.bind("<Return>", self.check_spelling)
        # Bind tooltip events for misspelled words
        self.note_entry.tag_bind("misspelled", "<Enter>", self.display_word_suggestion)
        self.note_entry.tag_bind("misspelled", "<Leave>", self.hide_word_suggestion)

        # Add status toggle (three-button)
        self.status_var = tk.StringVar(value="")
        status_frame = ttk.Frame(self.input_frame)
        status_frame.grid(row=8, column=0, columnspan=2, pady=5)
        self.status_buttons = {}
        for color in ["green", "yellow", "red"]:
            btn = tk.Button(
                status_frame,
                text=color.capitalize(),
                width=8,
                bg=color,
                relief="raised",
                command=lambda c=color: self.set_status(c),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.status_buttons[color] = btn

        # Submit button
        ttk.Button(
            self.input_frame,
            text="Submit",
            command=lambda: handle_submit(
                self.name_entry,
                self.surname_entry,
                self.email_entry,
                self.number_entry,
                self.note_entry,
                self.rating_var,
                self.status_var,
            ),
        ).grid(row=9, column=0, columnspan=2, pady=10)

        ttk.Button(
            self.input_frame,
            text="Backup Database",
            command=self.run_backup,
        ).grid(row=10, column=0, columnspan=2, pady=5)

    def run_backup(self):
        """Run the backup and inform the user."""
        try:
            backup_path = create_db_backup()
            messagebox.showinfo("Backup Successful", f"Backup saved to:\n{backup_path}")
        except (FileNotFoundError, PermissionError, OSError) as e:
            messagebox.showerror("Backup Failed", str(e))

    def validate_phone_input(self, action, char):
        """Validate phone number input to only allow valid characters, but allow all deletions."""
        if action == "0":  # Deletion action
            return True
        return char in VALID_PHONE_CHARS

    def setup_input_tab(self):
        """Setup the input form tab."""
        # Name input
        ttk.Label(self.input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_entry = ttk.Entry(self.input_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        # Surname input
        ttk.Label(self.input_frame, text="Surname:").grid(row=1, column=0, sticky=tk.W)
        self.surname_entry = ttk.Entry(self.input_frame)
        self.surname_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        # Email input
        ttk.Label(self.input_frame, text="Email:").grid(row=2, column=0, sticky=tk.W)
        self.email_entry = ttk.Entry(self.input_frame)
        self.email_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        # Number input with validation
        ttk.Label(self.input_frame, text="Number:").grid(row=3, column=0, sticky=tk.W)
        self.number_entry = ttk.Entry(self.input_frame)
        self.number_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)

        # Add validation to number entry
        vcmd = (self.root.register(self.validate_phone_input), "%d", "%S")
        self.number_entry.configure(validate="key", validatecommand=vcmd)

        # Rating input
        ttk.Label(self.input_frame, text="Rating:").grid(row=4, column=0, sticky=tk.W)
        self.rating_var = tk.DoubleVar(value=0)
        rating_frame = ttk.Frame(self.input_frame)
        rating_frame.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)

        # Add the lightbulb icon label
        lightbulb_label = tk.Label(rating_frame, image = self.lightbulb, cursor="hand2") # type: ignore
        lightbulb_label.pack(side=tk.RIGHT, padx=(8, 0), pady=(0, 8), anchor="nw")
        lightbulb_label.bind("<Enter>", self.show_star_instructions)
        lightbulb_label.bind("<Leave>", self.hide_star_instructions)

        # Create star rating display
        self.star_labels = []
        for i in range(5):  # 5 stars
            label = tk.Label(rating_frame, image=self.star_empty)  # type: ignore
            label.pack(side=tk.LEFT, padx=1)
            label.bind("<Button-1>", lambda e, pos=i: self.set_rating(pos + 1.0))
            label.bind("<Button-3>", lambda e, pos=i: self.set_rating(pos + 0.5))
            self.star_labels.append(label)

    def show_star_instructions(self, event):
        """Show the star instructions on hover"""
        self.tooltip.place(
            x=event.x_root - self.root.winfo_rootx() + 10,
            y=event.y_root - self.root.winfo_rooty() + 10,
        )

    def hide_star_instructions(self, event):
        """Hide the star instructions on hover"""
        self.tooltip.place_forget()

    def setup_search_tab(self):
        """Setup the search tab."""
        # Search fields
        search_fields_frame = ttk.LabelFrame(
            self.search_frame, text="Search Fields", padding="6"
        )
        search_fields_frame.pack(fill="x", padx=6, pady=6)

        # Name search
        ttk.Label(search_fields_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.search_name = ttk.Entry(search_fields_frame)
        self.search_name.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.search_name.bind("<Return>", lambda e: self.perform_search())

        # Surname search
        ttk.Label(search_fields_frame, text="Surname:").grid(
            row=1, column=0, sticky=tk.W
        )
        self.search_surname = ttk.Entry(search_fields_frame)
        self.search_surname.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.search_surname.bind("<Return>", lambda e: self.perform_search())

        # Email search
        ttk.Label(search_fields_frame, text="Email:").grid(row=2, column=0, sticky=tk.W)
        self.search_email = ttk.Entry(search_fields_frame)
        self.search_email.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        # Number search
        ttk.Label(search_fields_frame, text="Number:").grid(
            row=3, column=0, sticky=tk.W
        )
        self.search_number = ttk.Entry(search_fields_frame)
        self.search_number.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)

        # Enter key usage bind
        self.search_number.bind("<Return>", lambda e: self.perform_search())

        # Validation
        vcmd = (self.root.register(self.validate_phone_input), "%d", "%S")
        self.search_number.configure(validate="key", validatecommand=vcmd)

        # Button frame
        button_frame = ttk.Frame(search_fields_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        # Search button
        ttk.Button(button_frame, text="Search", command=self.perform_search).pack(
            side=tk.LEFT, padx=5
        )

        # Edit button
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_selected).pack(
            side=tk.LEFT, padx=5
        )

        # Save button
        ttk.Button(button_frame, text="Save Changes", command=self.save_changes).pack(
            side=tk.LEFT, padx=5
        )

        # Add Delete button
        delete_btn = ttk.Button(
            self.search_frame,
            text="Delete Selected Camper",
            command=self.delete_selected_camper,
        )
        delete_btn.pack(pady=5)

        # Results treeview
        self.setup_results_treeview()

    def setup_results_treeview(self):
        """Setup the treeview for displaying search results."""
        # Create frame for treeview
        results_frame = ttk.LabelFrame(self.search_frame, text="Results", padding="5")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create treeview
        # Include id column to prevent duplicate campers
        self.tree = ttk.Treeview(
            results_frame,
            columns=(
                "name",
                "surname",
                "email",
                "number",
                "note",
                "rating",
                "status",
                "id",
            ),
            show="headings",
        )

        # Define headings
        self.tree.heading("name", text="Name")
        self.tree.heading("surname", text="Surname")
        self.tree.heading("email", text="Email")
        self.tree.heading("number", text="Number")
        self.tree.heading("note", text="Note")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("status", text="Status")
        self.tree.heading("id", text="ID")

        # Define columns
        # Hide id column
        self.tree.column("name", width=100)
        self.tree.column("surname", width=100)
        self.tree.column("email", width=200)
        self.tree.column("number", width=100)
        self.tree.column("note", width=200)
        self.tree.column("rating", width=50)
        self.tree.column("status", width=100)
        self.tree.column("id", width=0)
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bind double-click event for editing
        self.tree.bind("<Double-1>", self.on_double_click)

        # Pack everything
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

    def on_double_click(self, event):
        """Handle double-click event for editing cells."""
        if self.tree is None:
            return

        # Get the clicked region
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Get the clicked item and column
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item or not column:
            return

        # Get the current value include id column for delete function and prevent duplicate campers
        current_value = self.tree.item(item, "values")[int(column[1]) - 1]
        # Get id column for delete function and prevent duplicate campers
        # Create entry widget for editing
        entry = ttk.Entry(self.tree)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)

        # Number validation for #3
        # If editing the "Number" column, add validation
        if column == "#3":  # Adjust if your "Number" column is a different index
            vcmd = (self.root.register(self.validate_phone_input), "%d", "%S")
            entry.configure(validate="key", validatecommand=vcmd)

        # Get the cell coordinates
        x, y, width, height = self.tree.bbox(item, column)

        # Place the entry widget
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def save_edit(event=None):
            """Save the edited value."""
            new_value = entry.get()
            # Get all current values
            values = list(self.tree.item(item, "values"))  # type: ignore
            # Update the edited value
            values[int(column[1]) - 1] = new_value
            # Update the tree item
            self.tree.item(item, values=values)  # type: ignore
            # Ensure the id is preserved and included in the updated row
            # Get the id value
            id_value = self.tree.item(item, "values")[7]  # type: ignore
            # Update the id value
            values[7] = id_value
            # Update the tree item
            self.tree.item(item, values=values)  # type: ignore
            entry.destroy()

        # Bind events for the entry widget
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def perform_search(self):
        """Handle the search button click."""
        if self.tree is None:
            return
        # Add id column to results for delete function and prevent duplicate campers
        try:
            self.tree.column("id", width=0)
        except Exception:
            pass  # in case column("id") doesn't exist yet, suppress error
        for item in self.tree.get_children():
            self.tree.delete(item)
        name = self.search_name.get().strip()
        surname = self.search_surname.get().strip()
        email = self.search_email.get().strip()
        number = self.search_number.get().strip()
        if not any([name, surname, number, email]):
            results = fetch_campers()  # Get all records
        else:
            results = []
            if name:
                results = fetch_campers(search_term=name, column="name")
            elif surname:
                results = fetch_campers(search_term=surname, column="surname")
            elif email:
                results = fetch_campers(search_term=email, column="email")
            elif number:
                results = fetch_campers(search_term=number, column="number")
        if not results:
            return
        for result in results:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    result.get("name", ""),
                    result.get("surname", ""),
                    result.get("email", ""),
                    result.get("number", ""),
                    result.get("note", ""),
                    result.get("rating", ""),
                    result.get("status", ""),
                    result.get("id", ""),
                ),
            )

    def set_rating(self, value):
        """Update the star display based on the rating value."""
        self.rating_var.set(value)
        full_stars = int(value)
        has_half = (value % 1) >= 0.5

        for i in range(5):
            if i < full_stars:
                self.star_labels[i].configure(image=self.star_full)
            elif i == full_stars and has_half:
                self.star_labels[i].configure(image=self.star_half)
            else:
                self.star_labels[i].configure(image=self.star_empty)

        self.root.mainloop()

    def edit_selected(self):
        """Edit the selected row in the treeview."""
        if self.tree is None:
            return
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.tree.item(item, "values")
        name = values[0] if len(values) > 0 else ""
        surname = values[1] if len(values) > 1 else ""
        email = values[2] if len(values) > 2 else ""
        number = values[3] if len(values) > 3 else ""
        note = values[4] if len(values) > 4 else ""
        # Get id column for delete function and prevent duplicate campers
        id_value = values[7] if len(values) > 7 else ""
        try:
            rating_value = float(values[5]) if len(values) > 5 else 0.0
        except (ValueError, TypeError):
            rating_value = 0.0
        status = values[6] if len(values) > 6 else ""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Camper")
        edit_window.geometry("400x320")
        ttk.Label(edit_window, text="Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="Surname:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        surname_entry = ttk.Entry(edit_window)
        surname_entry.insert(0, surname)
        surname_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="Email:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        email_entry = ttk.Entry(edit_window)
        email_entry.insert(0, email)
        email_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="Number:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )
        number_entry = ttk.Entry(edit_window)
        number_entry.insert(0, number)
        number_entry.grid(row=3, column=1, padx=5, pady=5)
        vcmd = (self.root.register(self.validate_phone_input), "%d", "%S")
        number_entry.configure(validate="key", validatecommand=vcmd)
        ttk.Label(edit_window, text="Note:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=5
        )
        note_entry = tk.Text(edit_window, height=3, width=20, wrap=tk.WORD)
        note_entry.insert("1.0", note)
        note_entry.grid(row=4, column=1, padx=5, pady=5)
        note_entry.tag_config("misspelled", underline=True, foreground="red")
        note_entry.bind("<space>", self.check_spelling)
        note_entry.bind("<Return>", self.check_spelling)
        ttk.Label(edit_window, text="Rating:").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )
        rating_var = tk.DoubleVar(value=rating_value)
        rating_frame = ttk.Frame(edit_window)
        rating_frame.grid(row=5, column=1, padx=5, pady=5)
        star_labels = []
        for i in range(5):
            label = tk.Label(rating_frame, image=self.star_empty)  # type: ignore
            label.pack(side=tk.LEFT, padx=1)
            label.bind(
                "<Button-1>",
                lambda e, pos=i: self.set_edit_rating(
                    pos + 1.0, star_labels, rating_var
                ),
            )
            label.bind(
                "<Button-3>",
                lambda e, pos=i: self.set_edit_rating(
                    pos + 0.5, star_labels, rating_var
                ),
            )
            star_labels.append(label)
        self.update_star_display(star_labels, rating_var.get())
        # Status toggle in edit window
        ttk.Label(edit_window, text="Status:").grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=5
        )
        status_var = tk.StringVar(value=status)
        status_frame = ttk.Frame(edit_window)
        status_frame.grid(row=6, column=1, padx=5, pady=5)
        status_buttons = {}

        def set_status_edit(color):
            status_var.set(color)
            for c, btn in status_buttons.items():
                if c == color:
                    btn.config(relief="sunken", bd=4)
                else:
                    btn.config(relief="raised", bd=2)

        for color in ["green", "yellow", "red"]:
            btn = tk.Button(
                status_frame,
                text=color.capitalize(),
                width=8,
                bg=color,
                relief="sunken" if color == status else "raised",
                command=lambda c=color: set_status_edit(c),
            )
            btn.pack(side=tk.LEFT, padx=2)
            status_buttons[color] = btn

        def save_edit():
            new_values = (
                name_entry.get(),
                surname_entry.get(),
                email_entry.get(),
                number_entry.get(),
                note_entry.get("1.0", tk.END).strip(),
                str(rating_var.get()),
                status_var.get(),
                id_value,
            )
            if self.tree is not None and item:
                self.tree.item(item, values=new_values)
                items = []
                for row in self.tree.get_children():
                    vals = self.tree.item(row, "values")
                    items.append(
                        {
                            "name": vals[0],
                            "surname": vals[1],
                            "email": vals[2],
                            "number": vals[3],
                            "note": vals[4],
                            "rating": vals[5],
                            "status": vals[6],
                            "id": vals[7],
                        }
                    )
                save_all_campers(items)
            edit_window.destroy()

        ttk.Button(edit_window, text="Save", command=save_edit).grid(
            row=7, column=0, columnspan=2, pady=10
        )

    def set_edit_rating(self, value, star_labels, rating_var):
        """Update the star display in edit window."""
        rating_var.set(value)
        self.update_star_display(star_labels, value)

    def update_star_display(self, star_labels, value):
        """Update star display based on rating value."""
        full_stars = int(value)
        has_half = (value % 1) >= 0.5

        for i in range(5):
            if i < full_stars:
                star_labels[i].configure(image=self.star_full)
            elif i == full_stars and has_half:
                star_labels[i].configure(image=self.star_half)
            else:
                star_labels[i].configure(image=self.star_empty)

    def save_changes(self):
        """Save all changes to the CSV file."""
        if self.tree is None:
            return
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            items.append(
                {
                    "name": values[0],
                    "surname": values[1],
                    "email": values[2],
                    "number": values[3],
                    "note": values[4],
                    "rating": values[5],
                    "status": values[6],
                    "id": values[7],
                }
            )
        save_all_campers(items)

    # display word sugestion on mouse hover
    def display_word_suggestion(self, event):
        """Display word suggestion on mouse hover for misspelled words."""
        index = self.note_entry.index(f"@{event.x},{event.y}")
        word_start = self.note_entry.index(f"{index} wordstart")
        word_end = self.note_entry.index(f"{index} wordend")
        word = self.note_entry.get(word_start, word_end).strip()
        suggestions = self.sym_spell.lookup(
            word, Verbosity.CLOSEST, max_edit_distance=2
        )
        suggestion_text = suggestions[0].term if suggestions else "No suggestion"
        self.tooltip_suggestion.config(text=suggestion_text)
        self.tooltip_suggestion.place(
            x=event.x_root - self.root.winfo_rootx() + 10,
            y=event.y_root - self.root.winfo_rooty() + 10,
            anchor="nw",
        )
        self._suggestion_indices = (word_start, word_end)
        self._suggestion_text = suggestion_text
        self.cancel_hide_tooltip()  # Cancel any scheduled hide

    def hide_word_suggestion(self, event):
        self.schedule_hide_tooltip(event)

    def schedule_hide_tooltip(self, event=None):
        # Schedule the tooltip to hide after 300ms
        self.cancel_hide_tooltip()
        self._tooltip_hide_job = self.root.after(
            300, self.tooltip_suggestion.place_forget
        )

    def cancel_hide_tooltip(self, event=None):
        if self._tooltip_hide_job is not None:
            self.root.after_cancel(self._tooltip_hide_job)
            self._tooltip_hide_job = None

    def check_spelling(self, event=None):
        """Check spelling of the note field."""

        if not event or not hasattr(event, "widget"):
            return None
        widget = event.widget

        widget.tag_remove("misspelled", "1.0", "end")
        words = widget.get("1.0", "end-1c").split()
        start = "1.0"

        for word in words:
            suggestions = self.sym_spell.lookup(
                word.lower(), Verbosity.CLOSEST, max_edit_distance=2
            )
            if not suggestions or suggestions[0].term != word.lower():
                pos = widget.search(word, start, stopindex="end")
                if pos:
                    end = f"{pos}+{len(word)}c"
                    widget.tag_add("misspelled", pos, end)
                    start = end
        return None

    def set_status(self, color):
        self.status_var.set(color)
        for c, btn in self.status_buttons.items():
            if c == color:
                btn.config(relief="sunken", bd=4)
            else:
                btn.config(relief="raised", bd=2)

    def delete_selected_camper(self):
        """Delete the selected camper from the database and refresh the treeview."""
        if self.tree is None:
            return
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.tree.item(item, "values")
        number = values[3] if len(values) > 3 else None
        if number:
            delete_camper_by_number(number)
            self.perform_search()

    def match_capitalization(self, original, suggestion):
        if original.isupper():
            return suggestion.upper()
        elif original.istitle():
            return suggestion.capitalize()
        elif original.islower():
            return suggestion.lower()
        else:
            return suggestion

    def replace_with_suggestion(self, event):
        if (
            self._suggestion_indices
            and self._suggestion_text
            and self._suggestion_text != "No suggestion"
        ):
            word_start, word_end = self._suggestion_indices
            original_word = self.note_entry.get(word_start, word_end)
            # Match capitalization
            replacement = self.match_capitalization(
                original_word, self._suggestion_text
            )
            self.note_entry.delete(word_start, word_end)
            self.note_entry.insert(word_start, replacement)
            self.tooltip_suggestion.place_forget()
            self.check_spelling()
