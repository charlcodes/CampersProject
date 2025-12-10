"""DB creation user class creation"""

from tkinter import messagebox

VALID_PHONE_CHARS = set("0123456789-+ ()")


class UserData:
    """Camper's information including personal details and rating."""

    def __init__(
        self,
        name: str,
        number: str = "",
        surname: str = "",
        note: str = "",
        rating: float = 0.0,
        email: str = "",
        status: str = "",
    ):
        self.name = name.strip()
        self.surname = surname.strip()
        self.number = number
        self.note = note.strip()
        self.rating = float(rating)
        self.email = email.strip()
        self.status = status.strip()

    @staticmethod
    def is_valid_phone_input(number: str) -> bool:
        """Check if phone number contains only valid characters."""
        return all(char in VALID_PHONE_CHARS for char in number)

    def is_valid(self) -> bool:
        """Validate the user data."""
        if not self.name:
            messagebox.showerror("Missing Name", "Please enter a name.")
            return False

        if not self.surname:  # surname is optional could delete this if needed
            messagebox.showerror("Missing Surname", "Please enter a surname.")
            return False

        if not self.is_valid_phone_input(self.number):

            messagebox.showerror(
                "Invalid Input", "Number must contain digits and symbols only."
            )
            return False

        if len(self.number) > 21:
            messagebox.showerror("Too Long", "Number must be 21 digits or fewer.")
            return False

        if self.rating < 0.0 or self.rating > 5.0:
            messagebox.showerror("Invalid Rating", "Rating must be between 0 and 5.")
            return False

        return True

    def to_dict(self):
        """Convert user data to dictionary format."""
        return {
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "number": self.number,
            "note": self.note,
            "rating": self.rating,
            "status": self.status,
        }
