import os
import sys
import subprocess
import platform

# List of required Python packages with specific versions
REQUIRED_PACKAGES = [
    "pdfminer.six==20221105",
    "python-docx==0.8.11",
    "pytesseract==0.3.10",
    "pillow==10.3.0",
    "pdf2image==1.17.0",  # Added pdf2image
    "PyPDF2==3.0.1",
]

def update_pip():
    """Update pip to the latest version."""
    print("\nUpdating pip to the latest version...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ Successfully updated pip")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update pip: {e}") # Include the error message

def install_pip_packages():
    """Install Python packages using pip."""
    print("\nInstalling Python packages...")
    for package in REQUIRED_PACKAGES:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}") # Include the error message

def install_tesseract_windows():
    """Download and install Tesseract OCR on Windows."""
    print("\nDownloading Tesseract OCR for Windows...")
    tesseract_url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    download_path = os.path.join(os.getenv("TEMP"), "tesseract-ocr-setup.exe")
    
    try:
        import urllib.request
        urllib.request.urlretrieve(tesseract_url, download_path)
        print("✅ Tesseract downloaded. Running installer...")
        subprocess.run([download_path, "/S"], check=True)
        print("✅ Tesseract OCR installed successfully.")
    except Exception as e:
        print(f"❌ Failed to install Tesseract OCR: {e}")

def main():
    print("=== Setting Up File Organizer ===")
    
    # Update pip
    update_pip()
    
    # Install Python packages
    install_pip_packages()
    
    # Install Tesseract OCR (Windows only)
    if platform.system() == "Windows":
        install_tesseract_windows()
    else:
        print("\n⚠️  For macOS/Linux, install Tesseract manually:")
        print("    macOS: `brew install tesseract`")
        print("    Linux (Debian/Ubuntu): `sudo apt install tesseract-ocr`")
    
    print("\n✅ Setup complete! Run `main.py` to start the program.")

if __name__ == "__main__":
    main()