import os
import re
import shutil
import pytesseract
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import PyPDF2
from docx import Document

class DocumentOrganizer:
    # Your original settings preserved exactly
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
        "handle_empty_folders": "delete",  # "delete" or "move"
        "exclude_files": [".DS_Store", "Thumbs.db"],
        "tesseract_path": r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        "date_patterns": [
            r'(?:date|effective date|signed|created):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:date|effective date|signed|created):?\s*(\d{4}-\d{1,2}-\d{1,2})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+\d{4}',
            r'\b(20\d{2})\b',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'signed:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'af form \d+,\s*(\d{4})'
        ]
    }

    def __init__(self, config_overrides=None):
        self.config = {**self.SETTINGS, **(config_overrides or {})}
        pytesseract.pytesseract.tesseract_cmd = self.config["tesseract_path"]

    def extract_text(self, filepath):
        """Universal text extraction with multiple fallbacks"""
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        
        try:
            # PDFs
            if ext == '.pdf':
                text = self._extract_pdf_text(filepath)
            
            # Word Documents
            elif ext == '.docx':
                doc = Document(filepath)
                text = '\n'.join([para.text for para in doc.paragraphs])
            
            # Images
            elif ext in ('.png', '.jpg', '.jpeg', '.bmp'):
                text = pytesseract.image_to_string(Image.open(filepath))
            
            # Text files
            else:
                with open(filepath, 'rb') as f:
                    raw = f.read(50000)  # Read first 50KB
                    for encoding in ['utf-8', 'latin-1', 'windows-1252']:
                        try:
                            text = raw.decode(encoding, errors='ignore')
                            break
                        except UnicodeDecodeError:
                            continue
                            
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {str(e)}")
        
        return text.lower() if text else ""

    def _extract_pdf_text(self, filepath):
        """Hybrid PDF text extraction"""
        text = ""
        
        # Try native text first
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:3]:  # First 3 pages
                    text += page.extract_text() + "\n"
            if text.strip(): 
                return text
        except:
            pass
        
        # Fallback to OCR
        try:
            images = convert_from_path(filepath, dpi=300, first_page=1, last_page=3)
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            print(f"⚠️ PDF OCR failed: {str(e)}")
        
        return text

    def _extract_dates(self, text):
        """Find all potential dates in text"""
        dates = []
        for pattern in self.config["date_patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            dates.extend(m.group(1) for m in matches if m.group(1))
        return dates

    def _parse_date(self, date_str):
        """Convert extracted date to YYYY-MM-DD format"""
        if not date_str:
            return None
            
        try:
            # Handle "27 May 2015" format
            if re.search(r'[a-z]', date_str, re.IGNORECASE):
                return datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
            
            # Handle numeric formats
            for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                try:
                    return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
            # Handle year-only
            if re.match(r'^\d{4}$', date_str):
                return f"{date_str}-01-01"
                
        except Exception:
            return None

    def _get_best_date(self, text, filepath):
        """Determine the most relevant document date"""
        # 1. Try to find dates in text
        extracted_dates = self._extract_dates(text)
        for date_str in extracted_dates:
            parsed = self._parse_date(date_str)
            if parsed:
                return parsed
        
        # 2. Fallback to filesystem dates
        return datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d')

    def _categorize(self, text):
        """Match content to your predefined categories"""
        for category, keywords in self.config["categories"].items():
            if any(kw in text for kw in keywords):
                return category
        return "Uncategorized"

    def _generate_filename(self, text, original_name):
        """Create descriptive filenames"""
        # Extract form numbers (e.g., "AF Form 123")
        form_match = re.search(r'(?:form|document)\s*(?:no|number)?:?\s*([A-Z0-9-]+)', text, re.I)
        form_num = f"Form_{form_match.group(1)}" if form_match else ""

        # Extract titles (e.g., "Title: Quarterly Report")
        title_match = re.search(r'title:\s*(.+)', text, re.I)
        title = re.sub(r'[^\w-]', '_', title_match.group(1).strip())[:50] if title_match else ""

        # Extract recipient (e.g., "To: John Smith")
        recipient_match = re.search(r'to:\s*(.+?)(?:\n|$)', text, re.I)
        recipient = re.sub(r'[^\w-]', '_', recipient_match.group(1).strip())[:30] if recipient_match else ""

        # Combine components
        name_parts = filter(None, [
            form_num,
            title,
            f"to_{recipient}" if recipient else ""
        ])
        
        base_name = '_'.join(name_parts) if any(name_parts) else os.path.splitext(original_name)[0]
        ext = os.path.splitext(original_name)[1]
        return f"{base_name[:150]}{ext}"

    def _process_empty_folders(self, root):
        """Handle empty folders per config"""
        empty_root = os.path.join(root, "_Empty_Folders")
        
        for folder, _, _ in os.walk(root, topdown=False):
            if folder == empty_root:
                continue
                
            try:
                if not os.listdir(folder):
                    if self.config["handle_empty_folders"] == "delete":
                        os.rmdir(folder)
                    else:
                        os.makedirs(empty_root, exist_ok=True)
                        shutil.move(folder, os.path.join(empty_root, os.path.basename(folder)))
            except Exception as e:
                print(f"⚠️ Couldn't process {folder}: {str(e)}")

    def organize_files(self, source_dir, dest_dir):
        """Main organization method"""
        try:
            # Clean empty folders first
            self._process_empty_folders(source_dir)
            
            # Process files
            for root, _, files in os.walk(source_dir):
                if not self.config["search_subfolders"] and root != source_dir:
                    continue
                    
                for filename in files:
                    if filename in self.config["exclude_files"]:
                        continue
                        
                    filepath = os.path.join(root, filename)
                    try:
                        text = self.extract_text(filepath)
                        category = self._categorize(text)
                        date = self._get_best_date(text, filepath)
                        new_name = self._generate_filename(text, filename)
                        
                        # Build destination path
                        dest_path = os.path.join(
                            dest_dir,
                            category,
                            date[:4] if self.config["archive_years"] else "",
                            new_name
                        )
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.move(filepath, dest_path)
                        
                    except Exception as e:
                        print(f"⚠️ Failed to process {filename}: {str(e)}")
            
            # Final empty folder cleanup
            self._process_empty_folders(source_dir)
            return True
            
        except Exception as e:
            print(f"❌ Fatal error: {str(e)}")
            return False