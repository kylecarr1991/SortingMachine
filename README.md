Here's a concise **GitHub-optimized** `README.md` focused on developers:

```markdown
# DocOrganizer

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Automated document categorization and renaming using OCR and content analysis.

## Features
- 📂 Content-based file organization
- ✨ Automatic metadata extraction (titles, recipients, dates)
- 🖼️ Supports PDFs, Word docs, images, and text files
- 🚀 Optional GUI or CLI interface

## Quick Start
```bash
# Install (Windows)
install_portable_python.bat

# Run GUI
python dnd_organizer_gui.py

# Or CLI
python organizer.py --source ./input --destination ./sorted
```

## Developer Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure Tesseract path in `organizer.py` if needed

## Key Files
| File | Purpose |
|------|---------|
| `organizer.py` | Core sorting logic |
| `dnd_organizer_gui.py` | Optional Tkinter GUI |
| `installer.py` | Dependency installer |
| `install_portable_python.bat` | Portable setup script |

## Customization
Override default settings in `organizer.py`:
```python
SETTINGS = {
    "categories": {
        "Legal": ["contract", "nda"],
        "Financial": ["invoice", "receipt"]
    }
}
```

## Contributing
PRs welcome! Please:
1. Keep the portable installer working
2. Maintain backward compatibility
3. Add tests for new features

---
*"Finally tamed my document chaos!"* - Happy User
```
