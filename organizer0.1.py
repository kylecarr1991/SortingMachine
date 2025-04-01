import os
import re
import shutil
import pytesseract
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import PyPDF2

class DocumentOrganizer:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configurable patterns
        self.title_patterns = [
            r'document\s*title:\s*(.+)',
            r'form\s*(?:name|number):?\s*([A-Z0-9-]+)',
            r'title:\s*(.+)',
            r'^#\s*(.+)$',
            r'^[A-Z][A-Za-z0-9\s-]{10,}$'  # Standalone line in all caps
        ]
        
        self.recipient_patterns = [
            r'to:\s*(.+)',
            r'recipient:\s*(.+)',
            r'addressed\s*to:\s*(.+)',
            r'dear\s*(.+?)[,;\n]'
        ]
        
        self.date_patterns = [
            r'date\s*(?:of\s*issue)?:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'signed\s*on:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'effective\s*date:\s*(\d{4}-\d{2}-\d{2})',
            r'(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2},? \d{4}\b)',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]

    def extract_text(self, filepath):
        """Universal text extraction with OCR fallback"""
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        
        try:
            # PDFs
            if ext == '.pdf':
                text = self._extract_pdf_text(filepath)
            
            # Images
            elif ext in ('.png', '.jpg', '.jpeg', '.bmp'):
                text = pytesseract.image_to_string(Image.open(filepath))
            
            # Text-based files
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(100000)  # Read first 100KB
                    
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

    def _extract_pattern(self, text, patterns):
        """Helper to extract structured data"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def get_document_metadata(self, filepath):
        """Extracts title, recipient, and date from content"""
        text = self.extract_text(filepath)
        
        return {
            'title': self._extract_pattern(text, self.title_patterns),
            'recipient': self._extract_pattern(text, self.recipient_patterns),
            'date': self._parse_date(self._extract_pattern(text, self.date_patterns)),
            'text': text
        }

    def _parse_date(self, date_str):
        """Convert extracted date string to YYYY-MM-DD"""
        if not date_str:
            return None
            
        try:
            # Handle "27 May 2015" format
            if re.search(r'[a-z]', date_str, re.IGNORECASE):
                return datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
            
            # Handle "05/27/2015" format
            elif '/' in date_str:
                return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
            
            # Handle "2023-12-01" format
            elif '-' in date_str:
                return date_str[:10]  # Take first 10 chars
                
        except ValueError:
            return None

    def generate_filename(self, metadata, original_name):
        """Smart naming based on content"""
        parts = []
        
        # 1. Add title/form number if found
        if metadata['title']:
            clean_title = re.sub(r'[^\w-]', '_', metadata['title'])[:50]
            parts.append(clean_title)
        
        # 2. Add recipient if found
        if metadata['recipient']:
            clean_recipient = re.sub(r'[^\w-]', '_', metadata['recipient'].split('\n')[0])[:30]
            parts.append(f"to_{clean_recipient}")
        
        # 3. Add date if found
        if metadata['date']:
            parts.append(metadata['date'])
        
        # 4. Fallback to original name (sanitized)
        if not parts:
            base = os.path.splitext(original_name)[0]
            clean_base = re.sub(r'[^\w-]', '_', base)[:50]
            parts.append(clean_base)
        
        # Add extension
        ext = os.path.splitext(original_name)[1].lower()
        return f"{'_'.join(parts)}{ext}"

    def organize_file(self, src_path, dest_folder):
        """Process and move a single file"""
        try:
            metadata = self.get_document_metadata(src_path)
            new_name = self.generate_filename(metadata, os.path.basename(src_path))
            
            # Create dated subfolder
            date_folder = metadata['date'][:7] if metadata['date'] else "undated"
            dest_path = os.path.join(dest_folder, date_folder, new_name)
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(src_path, dest_path)
            return True
            
        except Exception as e:
            print(f"❌ Failed to process {os.path.basename(src_path)}: {str(e)}")
            return False