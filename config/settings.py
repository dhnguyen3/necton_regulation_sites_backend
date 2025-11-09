import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # System Paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DB_PATH = self.DATA_DIR / "compliance.db"
        self.SNAPSHOT_DIR = self.DATA_DIR / "snapshots"
        
        # Create directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.SNAPSHOT_DIR.mkdir(exist_ok=True)
        
        # Document Sources
        self.DOCUMENTS = {
            "ISO 13485": "file:///C:/standards/ISO_13485.pdf",
            "ISO 9001": "file:///C:/standards/ISO_9001.pdf",
            "WHO GMP": "https://www.who.int/publications/i/item/WHO-TRS-1019-annex2",
            "EU GMP": "https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-4_en"
        }
        
        # System Settings
        self.REQUEST_TIMEOUT = 30
        self.MAX_RETRIES = 3
        self.USER_AGENT = "ComplianceMonitor/2.0"
        self.CHANGE_THRESHOLD = 0.1
        
        # Notification Settings
        self.SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
        self.EMAIL = {
            'sender': os.getenv("EMAIL_SENDER"),
            'password': os.getenv("EMAIL_PASSWORD"),
            'recipients': os.getenv("EMAIL_RECIPIENTS", "").split(','),
            'smtp_server': "smtp.gmail.com",
            'smtp_port': 587
        }

settings = Settings()