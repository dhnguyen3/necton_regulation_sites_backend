import json
import logging
from config import settings

logger = logging.getLogger(__name__)

def load_hash_store():
    try:
        if settings.DB_PATH.exists():
            with open(settings.DB_PATH, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading hash store: {str(e)}")
        return {}

def save_hash_store(hash_store):
    try:
        with open(settings.DB_PATH, 'w') as f:
            json.dump(hash_store, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving hash store: {str(e)}")

def load_previous_version(name):
    try:
        filepath = settings.SNAPSHOT_DIR / f"{name.replace(' ', '_')}.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('content')
        return None
    except Exception as e:
        logger.error(f"Error loading previous version: {str(e)}")
        return None

def save_current_version(name, content):
    try:
        filepath = settings.SNAPSHOT_DIR / f"{name.replace(' ', '_')}.json"
        with open(filepath, 'w') as f:
            json.dump({
                'name': name,
                'content': content
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving current version: {str(e)}")