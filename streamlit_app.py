"""
Entry point for Streamlit Cloud deployment
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import main app
from app import main

if __name__ == "__main__":
    main()