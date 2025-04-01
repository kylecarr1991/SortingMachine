import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from playsound import playsound
from PIL import Image, ImageTk
import os
from dnd_organizer import organizer  # Update import statement

class DnDSuperGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("D&D Scroll Organizer")
        self.window.geometry("800x600")
        
        # D&D Theme
        self.setup_theme()
        
        # Load assets
        self.load_assets()
        
        # Create UI
        self.create_widgets()
        
    def setup_theme(self):
        """Configure D&D visual style"""
        self.window.configure(bg="#2c1e15")  # Parchment dark
        self.style = ttk.Style()
        self.style.configure(
            "DnD.TLabel", 
            foreground="#e6d8a5", 
            background="#2c1e15",
            font=("Old English Text MT", 12)
        )
        self.style.configure(
            "DnD.TButton",
            foreground="#2c1e15",
            background="#8b5a2b",
            font=("Old English Text MT", 10, "bold"),
            padding=10
        )
        
    def load_assets(self):
        """Load images and sounds"""
        self.background_image = ImageTk.PhotoImage(Image.open("assets/background.jpg"))
        self.icon_image = ImageTk.PhotoImage(Image.open("assets/icon.png"))
        self.sound_effect = "assets/sound.mp3"

    def create_widgets(self):
        """Build the interface"""
        # Background
        background_label = tk.Label(self.window, image=self.background_image)
        background_label.place(relwidth=1, relheight=1)
        
        # Header
        header_label = ttk.Label(
            self.window, 
            text="⚔️ D&D Scroll Organizer ⚔️", 
            style="DnD.TLabel"
        )
        header_label.pack(pady=20)

        # Source Folder
        source_label = ttk.Label(
            self.window, 
            text="Select Scroll Chest:", 
            style="DnD.TLabel"
        )
        source_label.pack()
        self.source_btn = ttk.Button(
            self.window,
            text="Open Ancient Tome",
            style="DnD.TButton",
            command=self.select_source
        )
        self.source_btn.pack(pady=5)
        self.source_label = ttk.Label(
            self.window, 
            text="No scrolls selected", 
            style="DnD.TLabel"
        )
        self.source_label.pack()

        # Destination Folder
        dest_label = ttk.Label(
            self.window, 
            text="Organize In:", 
            style="DnD.TLabel"
        )
        dest_label.pack(pady=(15,0))
        self.dest_btn = ttk.Button(
            self.window,
            text="Choose Treasure Hoard",
            style="DnD.TButton",
            command=self.select_destination
        )
        self.dest_btn.pack(pady=5)
        self.dest_label = ttk.Label(
            self.window, 
            text="No hoard selected", 
            style="DnD.TLabel"
        )
        self.dest_label.pack()

        # Organize Button
        self.organize_btn = ttk.Button(
            self.window,
            text="CAST SORTING SPELL",
            style="DnD.TButton",
            command=self.run_organization
        )
        self.organize_btn.pack(pady=30)

        # Icon
        icon_label = tk.Label(self.window, image=self.icon_image, bg="#2c1e15")
        icon_label.pack(pady=(10,0))

    def select_source(self):
        """Choose source folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.source_path = folder
            self.source_label.config(text=folder)
            playsound(self.sound_effect)

    def select_destination(self):
        """Choose destination folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.dest_path = folder
            self.dest_label.config(text=folder)
            playsound(self.sound_effect)

    def run_organization(self):
        """Execute the sorting"""
        if not hasattr(self, 'source_path') or not hasattr(self, 'dest_path'):
            messagebox.showerror("Error", "You must select both folders!")
            return
        
        try:
            organizer.organize_files(self.source_path, self.dest_path)
            playsound(self.sound_effect)
            messagebox.showinfo(
                "Success!", 
                "Scrolls organized successfully!\n"
                "Check your treasure hoard."
            )
        except Exception as e:
            messagebox.showerror(
                "Spell Failed!", 
                f"The magic backfired:\n{str(e)}"
            )

if __name__ == "__main__":
    app = DnDSuperGUI()
    app.window.mainloop()