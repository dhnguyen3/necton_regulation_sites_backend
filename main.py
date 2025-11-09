#!/usr/bin/env python3
import logging
from config import settings
from core.fetcher import get_document_content
from core.analyzer import ChangeAnalyzer
from services.notifier import send_notification
from config import settings  # This now imports the settings instance directly
from storage import (
    load_hash_store,
    save_hash_store,
    load_previous_version,
    save_current_version
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def monitor_documents():
    """Main monitoring workflow"""
    hash_store = load_hash_store()
    
    for name, url in settings.DOCUMENTS.items():
        try:
            content = get_document_content(url, is_iso=("ISO" in name))
            if not content:
                continue
                
            current_hash = hash(content)
            if hash_store.get(name) != current_hash:
                changes = ChangeAnalyzer.analyze_changes(
                    load_previous_version(name),
                    content,
                    name
                )
                if changes["significant"]:
                    send_notification(name, url, changes)
                hash_store[name] = current_hash
                save_current_version(name, content)
                
        except Exception as e:
            logging.error(f"Error processing {name}: {str(e)}")
    
    save_hash_store(hash_store)

if __name__ == "__main__":
    monitor_documents()