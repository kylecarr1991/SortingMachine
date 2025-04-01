import tkinter as tk
from tkinter import ttk
import subprocess
import platform
import os
import sys
import urllib.request
from threading import Thread
import time
import psutil  # For finding command prompt window

class FloatingProgress:
    def __init__(self):
        # Find command prompt window position
        self.cmd_window = self.find_cmd_window()
        if not self.cmd_window:
            self.cmd_window = {'width': 80, 'height': 25, 'x': 100, 'y': 100}  # Fallback
            
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.wm_attributes('-transparentcolor', 'black')
        self.root.config(bg='black')
        
        # Position to right of command window
        x_pos = self.cmd_window['x'] + self.cmd_window['width'] + 10
        y_pos = self.cmd_window['y']
        self.root.geometry(f'+{x_pos}+{y_pos}')
        
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0, 
                               width=200, height=30)
        self.canvas.pack()
        
        self.bars = {}
        self.active_tasks = {}
        
    def find_cmd_window(self):
        """Get command prompt window dimensions"""
        try:
            import ctypes
            from ctypes import wintypes
            
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            return {
                'x': rect.left,
                'y': rect.top,
                'width': rect.right - rect.left,
                'height': rect.bottom - rect.top
            }
        except:
            return None
    
    def show_progress(self, task_id, label):
        """Create floating progress bar"""
        if task_id in self.bars:
            return
            
        # Create new bar
        bg = self.canvas.create_rectangle(0, 0, 200, 30, fill='black', outline='')
        text = self.canvas.create_text(5, 5, text=label, anchor=tk.NW, fill='white', font=('Consolas', 8))
        bar = self.canvas.create_rectangle(0, 20, 0, 25, fill='#00FF00', outline='')
        
        self.bars[task_id] = {
            'bg': bg,
            'text': text,
            'bar': bar,
            'width': 0
        }
        
        # Show window if hidden
        self.root.deiconify()
        self.root.update()
    
    def update_progress(self, task_id, percent):
        """Update existing progress bar"""
        if task_id not in self.bars:
            return
            
        bar = self.bars[task_id]
        new_width = int(2 * percent)  # 200px max width
        
        if new_width > bar['width']:
            self.canvas.coords(bar['bar'], 0, 20, new_width, 25)
            bar['width'] = new_width
            self.root.update()
    
    def complete_progress(self, task_id):
        """Finish and remove progress bar"""
        if task_id not in self.bars:
            return
            
        # Flash cyan before disappearing
        self.canvas.itemconfig(self.bars[task_id]['bar'], fill='#00FFFF')
        self.root.update()
        time.sleep(0.5)
        
        # Remove bar
        self.canvas.delete(self.bars[task_id]['bg'])
        self.canvas.delete(self.bars[task_id]['text'])
        self.canvas.delete(self.bars[task_id]['bar'])
        del self.bars[task_id]
        
        # Hide window if no more bars
        if not self.bars:
            self.root.withdraw()
        else:
            self.root.update()

class Installer:
    def __init__(self):
        self.gui = FloatingProgress()
        self.task_id = 0
        
    def run(self):
        steps = [
            ("Updating pip", self.update_pip),
            ("Installing packages", self.install_packages),
            ("Tesseract OCR", self.install_tesseract)
        ]
        
        for label, func in steps:
            task_id = self.new_task(label)
            func(task_id)
            self.complete_task(task_id)
        
        self.gui.root.after(1000, self.gui.root.destroy)
    
    def new_task(self, label):
        """Start new progress task"""
        self.task_id += 1
        self.gui.show_progress(self.task_id, label)
        return self.task_id
    
    def update_task(self, task_id, percent):
        """Update task progress"""
        self.gui.update_progress(task_id, percent)
    
    def complete_task(self, task_id):
        """Mark task as complete"""
        self.gui.complete_progress(task_id)
    
    def update_pip(self, task_id):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for i in range(101):
                self.update_task(task_id, i)
                time.sleep(0.02)
        except:
            self.update_task(task_id, 100)
    
    def install_packages(self, task_id):
        packages = [
            "pdfminer.six==20221105",
            "python-docx==0.8.11",
            "pytesseract==0.3.10",
            "pillow==10.3.0",
            "pdf2image==1.17.0",
            "PyPDF2==3.0.1"
        ]
        
        for i, package in enumerate(packages):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass
            
            self.update_task(task_id, int((i + 1) / len(packages) * 100))
            time.sleep(0.1)
    
    def install_tesseract(self, task_id):
        if platform.system() != "Windows":
            self.update_task(task_id, 100)
            return
            
        try:
            url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
            path = os.path.join(os.getenv("TEMP"), "tesseract-installer.exe")
            
            def progress_hook(count, block_size, total_size):
                percent = min(int(count * block_size * 100 / total_size), 100)
                self.update_task(task_id, percent)
            
            urllib.request.urlretrieve(url, path, progress_hook)
            subprocess.run([path, "/S"], check=True)
            self.update_task(task_id, 100)
        except:
            self.update_task(task_id, 100)

if __name__ == "__main__":
    installer = Installer()
    Thread(target=installer.run).start()
    installer.gui.root.mainloop()