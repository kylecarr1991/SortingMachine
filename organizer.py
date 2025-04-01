import os
import shutil
import re
from datetime import datetime
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract
from docx import Document
from PIL import Image
import pytesseract

# Config
SETTINGS = {
    "categories": {
        "Military": ["epr", "performance report", "air force", "usaf"],
        "Maintenance": ["age", "equipment", "maintenance", "inspection"],
        "Training": ["ccaf", "course", "gpa", "dean's list"],
        "Financial": ["tax", "invoice", "receipt", "ledger", "bank", "statement"],
        "Legal": ["contract", "agreement", "nda", "lease", "will", "legal"],
        "Personal": ["resume", "cv", "application", "cover letter"],
        "Work": ["report", "meeting", "minutes", "presentation", "business"],
        "Academic": ["essay", "thesis", "research", "paper", "homework"]
    },
    "archive_years": True,
    "search_subfolders": True,
    "handle_empty_folders": "delete",
    "exclude_files": [".DS_Store", "Thumbs.db"],
    "tesseract_path": r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    "date_patterns": [
        r'(?:date|effective date|signed|created):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:date|effective date|signed|created):?\s*(\d{4}-\d{1,2}-\d{1,2})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+\d{4}',
        r'\b(20\d{2})\b',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        # Military-specific patterns
        r'date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        r'signed:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        r'af form \d+,\s*(\d{4})'
    ]
}

def extract_text(filepath):
    """Extract text from various file types with multiple fallbacks"""
    try:
        # Set Tesseract path
        pytesseract.pytesseract.tesseract_cmd = SETTINGS["tesseract_path"]
        
        # PDF files
        if filepath.lower().endswith('.pdf'):
            try:
                # Try PyPDF2 first
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages[:3]:
                        text += page.extract_text() + "\n"
                    if text.strip(): return text.lower()
                
                # Fallback to pdfminer
                text = pdfminer_extract(filepath)
                if text.strip(): return text.lower()
                
                # Final fallback for image PDFs
                images = convert_pdf_to_images(filepath)
                text = ""
                for img in images[:2]:
                    text += pytesseract.image_to_string(img) + "\n"
                return text.lower()
                
            except Exception:
                pass
        
        # Word documents
        elif filepath.lower().endswith('.docx'):
            try:
                doc = Document(filepath)
                return "\n".join([para.text for para in doc.paragraphs]).lower()
            except Exception:
                pass
        
        # Image files
        elif filepath.lower().split('.')[-1] in ['png', 'jpg', 'jpeg', 'bmp']:
            try:
                return pytesseract.image_to_string(Image.open(filepath)).lower()
            except Exception:
                pass
        
        # Plain text files
        with open(filepath, 'rb') as f:
            raw = f.read(5000)
            for encoding in ['utf-8', 'latin-1', 'windows-1252']:
                try:
                    return raw.decode(encoding, errors='ignore').lower()
                except UnicodeDecodeError:
                    continue
        
        return ""
    except Exception as e:
        print(f"⚠️ Error extracting text from {filepath}: {str(e)}")
        return ""

def convert_pdf_to_images(pdf_path):
    """Convert PDF pages to images for OCR"""
    try:
        from pdf2image import convert_from_path
        return convert_from_path(pdf_path, dpi=300, first_page=1, last_page=3)
    except Exception:
        return []

def extract_document_date(content):
    """Specialized date extraction for military performance reports"""
    if not content:
        return None

    # First look for signature dates (most relevant for EPRs)
    signature_patterns = [
        r'date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "DATE: 27 May 2015"
        r'signed:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "SIGNED: 1 Jun 2015"
        r'date\s*[^:]*:\s*(\d{1,2}/\d{1,2}/\d{4})'  # "DATE: 05/27/2015"
    ]

    # Try to find the latest signature date
    latest_year = None
    for pattern in signature_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            date_str = match.group(1)
            try:
                if re.search(r'[A-Za-z]', date_str):  # "27 May 2015" format
                    date_obj = datetime.strptime(date_str, '%d %B %Y')
                else:  # "05/27/2015" format
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                
                if 1990 <= date_obj.year <= 2030:
                    if not latest_year or date_obj.year > latest_year:
                        latest_year = date_obj.year
                        print(f"Found signature date: {date_str} → {latest_year}")
            except ValueError:
                continue

    if latest_year:
        return latest_year

    # Fallback to form date if no signature dates found
    form_date_match = re.search(r'af form \d+,\s*(\d{4})', content, re.IGNORECASE)
    if form_date_match:
        try:
            form_year = int(form_date_match.group(1))
            if 1990 <= form_year <= 2030:
                print(f"Using form date: {form_year}")
                return form_year
        except ValueError:
            pass

    # Final fallback to simple year extraction
    year_match = re.search(r'\b(19|20)\d{2}\b', content)
    if year_match:
        try:
            year = int(year_match.group())
            if 1990 <= year <= 2030:
                print(f"Using extracted year: {year}")
                return year
        except:
            pass

    return None

def get_file_year(filepath, content):
    """Determine the year from either content or file metadata"""
    # First try to get date from document content
    doc_year = extract_document_date(content)
    if doc_year:
        return str(doc_year)
    
    # Fallback to file creation date
    file_year = datetime.fromtimestamp(os.path.getctime(filepath)).year
    print(f"Using file creation date for {os.path.basename(filepath)}: {file_year}")
    return str(file_year)

def generate_simple_name(content, filepath):
    """Generate clean names from content with better fallbacks"""
    ext = os.path.splitext(filepath)[1].lower()
    basename = os.path.splitext(os.path.basename(filepath))[0]
    
    # Military document patterns
    military_patterns = [
        r'enlisted performance report.*?name.*?([a-z]+,\s*[a-z]+(?:\s*[a-z]+)?)',
        r'name:\s*([a-z]+,\s*[a-z]+(?:\s*[a-z]+)?)',
        r'subject:\s*(.*?)\n',
        r'report.*?for\s*(.*?)\n',
        r'air force\s*(.*?)\n'
    ]
    
    if any(p in content[:1000] for p in SETTINGS["categories"]["Military"]):
        for pattern in military_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                doc_type = "epr" if "performance report" in content else "document"
                return f"{name.replace(' ', '_')}_{doc_type}{ext}"
    
    # General document patterns
    patterns = [
        r'document title:?\s*([^\n]+)',
        r'title:?\s*([^\n]+)',
        r'#\s*(.*?)\n',
        r'^\s*(.*?)\s*\n',
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            title = match.group(1).strip()
            if len(title) > 5:
                break
    else:
        title = basename
    
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'\s+', '_', title.strip())
    title = re.sub(r'^[\d_]+', '', title)
    
    return f"{title[:50]}{ext}"

def categorize_file(content, filename):
    """Match content to predefined categories"""
    content = content or filename.lower()
    for category, keywords in SETTINGS["categories"].items():
        if any(keyword in content for keyword in keywords):
            return category
    return "Other"

def process_empty_folders(root_folder):
    """Handle empty folders after processing"""
    empty_root = os.path.join(root_folder, "_Empty_Folders")
    os.makedirs(empty_root, exist_ok=True)
    
    for root, dirs, _ in os.walk(root_folder, topdown=False):
        if os.path.normpath(root) == os.path.normpath(empty_root):
            continue
            
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    if SETTINGS["handle_empty_folders"] == "delete":
                        os.rmdir(dir_path)
                        print(f"Deleted empty folder: {dir_path}")
                    else:
                        dest = os.path.join(empty_root, dir_name)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        shutil.move(dir_path, dest)
                        print(f"Moved empty folder: {dir_path} → {dest}")
            except Exception as e:
                print(f"⚠️ Couldn't process folder {dir_path}: {str(e)}")

def organize_files(source_dir, dest_dir):
    try:
        print(f"\n⚡ Starting Organization Process\n")
        
        # First clean up any existing empty folders
        process_empty_folders(source_dir)
        
        for root, _, files in os.walk(source_dir):
            if not SETTINGS["search_subfolders"] and root != source_dir:
                continue
                
            for filename in files:
                if filename.lower() in SETTINGS["exclude_files"]:
                    continue
                    
                filepath = os.path.join(root, filename)
                try:
                    content = extract_text(filepath)
                    category = categorize_file(content, filename)
                    new_name = generate_simple_name(content, filepath)
                    year = get_file_year(filepath, content)
                    
                    final_path = os.path.join(dest_dir, category, year, new_name)
                    os.makedirs(os.path.dirname(final_path), exist_ok=True)
                    shutil.move(filepath, final_path)
                    print(f"Organized: {filename} → {category}/{year}/{new_name}")
                
                except Exception as e:
                    print(f"⚠️ Couldn't process {filename}: {str(e)}")
        
        # Final cleanup of empty folders
        process_empty_folders(source_dir)
        print("\n✅ Organization complete!")
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")

if __name__ == "__main__":
    organize_files(
        source_dir="C:/DnD_Organizer/test_files",
        dest_dir="C:/DnD_Organizer/sorted"
    )