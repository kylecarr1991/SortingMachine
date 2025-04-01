import os
import sys
import subprocess
import platform
import urllib.request
import time
import tkinter as tk
from tkinter import ttk
from threading import Thread
from PIL import Image
import pytesseract

# ====================== CONFIGURATION ======================
REQUIRED_PACKAGES = [
    "psutil==5.9.5",        # For window positioning
    "pdfminer.six==20221105",
    "python-docx==0.8.11",
    "pytesseract==0.3.10",
    "pillow==10.3.0",
    "pdf2image==1.17.0",
    "PyPDF2==3.0.1"
]

TESSERACT_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
TESSERACT_INSTALLER = "tesseract_installer.exe"

# ====================== PROGRESS GUI ======================
class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Installer Progress")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.config(bg='black')
        
        # Position window to right of command prompt
        self._position_window()
        
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0, 
                               width=200, height=30)
        self.canvas.pack()
        
        self.current_task = None
        self.root.withdraw()  # Hide until first task

    def _position_window(self):
        """Position window relative to command prompt"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'cmd.exe' in proc.name().lower() or 'python' in proc.name().lower():
                    term = proc.terminal()
                    x = term.x + term.width + 10
                    y = term.y
                    self.root.geometry(f"+{x}+{y}")
                    break
        except:
            # Fallback position
            self.root.geometry("+100+100")

    def show_progress(self, task_name):
        """Show new progress bar"""
        self.canvas.delete("all")
        self.canvas.create_text(5, 5, text=task_name, anchor=tk.NW, 
                              fill='white', font=('Consolas', 8))
        self.progress_bar = self.canvas.create_rectangle(0, 20, 0, 25, 
                                                       fill='#00FF00', outline='')
        self.root.deiconify()
        self.root.update()

    def update_progress(self, percent):
        """Update current progress bar"""
        width = int(2 * percent)  # 200px max width
        self.canvas.coords(self.progress_bar, 0, 20, width, 25)
        self.root.update()

    def complete_progress(self):
        """Flash and hide progress bar"""
        self.canvas.itemconfig(self.progress_bar, fill='#00FFFF')
        self.root.update()
        time.sleep(0.5)
        self.root.withdraw()

# ====================== INSTALLATION LOGIC ======================
class DocumentInstaller:
    def __init__(self):
        self.gui = InstallerGUI()
        
    def run(self):
        """Main installation sequence"""
        try:
            # Phase 1: Critical dependencies
            self._install_with_progress("Installing psutil", [REQUIRED_PACKAGES[0]])
            
            # Phase 2: Tesseract OCR
            if platform.system() == "Windows":
                self._install_tesseract()
            
            # Phase 3: Remaining packages
            self._install_with_progress("Installing packages", REQUIRED_PACKAGES[1:])
            
            # Final validation
            self._validate_installation()
            
        except Exception as e:
            print(f"❌ Installation failed: {str(e)}")
        finally:
            self.gui.root.after(1000, self.gui.root.destroy)

    def _install_with_progress(self, task_name, packages):
        """Install Python packages with progress tracking"""
        self.gui.show_progress(task_name)
        
        for i, package in enumerate(packages):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                pass  # Continue even if one package fails
            
            progress = int((i + 1) / len(packages) * 100)
            self.gui.update_progress(progress)
            time.sleep(0.1)
            
        self.gui.complete_progress()

    def _install_tesseract(self):
        """Download and install Tesseract OCR"""
        self.gui.show_progress("Installing Tesseract")
        
        try:
            # Download with progress
            def update_progress(count, block_size, total_size):
                percent = min(int(count * block_size * 100 / total_size), 100)
                self.gui.update_progress(percent)
                
            urllib.request.urlretrieve(
                TESSERACT_URL, 
                TESSERACT_INSTALLER,
                reporthook=update_progress
            )
            
            # Silent install
            subprocess.run([TESSERACT_INSTALLER, "/S"], check=True)
            os.remove(TESSERACT_INSTALLER)
            
        except Exception as e:
            print(f"⚠️ Tesseract installation warning: {str(e)}")
        finally:
            self.gui.complete_progress()

    def _validate_installation(self):
        """Verify critical components"""
        self.gui.show_progress("Validating install")
        time.sleep(0.5)  # Simulate validation
        
        try:
            # Check Tesseract
            if platform.system() == "Windows":
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract {version} detected")
                
            # Check Python packages
            for package in REQUIRED_PACKAGES:
                pkg_name = package.split('==')[0]
                __import__(pkg_name)
                
            print("✅ All dependencies verified")
        except Exception as e:
            print(f"⚠️ Validation warning: {str(e)}")
        finally:
            self.gui.complete_progress()

# ====================== MAIN EXECUTION ======================
if __name__ == "__main__":
    installer = DocumentInstaller()
    
    # Run in background thread to prevent GUI blocking
    Thread(target=installer.run).start()
    
    # Start GUI main loop
    installer.gui.root.mainloop()