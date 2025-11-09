from difflib import SequenceMatcher
import re
from typing import Dict, Any
import logging
from config import settings

logger = logging.getLogger(__name__)

class ChangeAnalyzer:
    @staticmethod
    def analyze_iso_changes(old: str, new: str) -> Dict[str, Any]:
        """Enhanced ISO change detection"""
        if not old or not new:
            return {"significant": False, "details": "Missing content"}
        
        ratio = SequenceMatcher(None, old, new).ratio()
        change_percent = (1 - ratio) * 100
        
        old_clauses = set(re.findall(r"\b\d+\.\d+\b", old))
        new_clauses = set(re.findall(r"\b\d+\.\d+\b", new))
        clause_changes = {
            "added": list(new_clauses - old_clauses),
            "removed": list(old_clauses - new_clauses)
        }
        
        significant = (change_percent >= settings.CHANGE_THRESHOLD or 
                      bool(clause_changes["added"]) or 
                      bool(clause_changes["removed"]))
        
        return {
            "significant": significant,
            "change_percent": change_percent,
            "details": clause_changes
        }

    @staticmethod
    def analyze_gmp_changes(old: str, new: str) -> Dict[str, Any]:
        """Enhanced GMP change detection"""
        if not old or not new:
            return {"significant": False, "details": "Missing content"}
        
        ratio = SequenceMatcher(None, old, new).ratio()
        change_percent = (1 - ratio) * 100
        
        # Count requirement keywords
        keywords = ["shall", "must", "required"]
        changes = {
            kw: {"old": old.lower().count(kw), "new": new.lower().count(kw)}
            for kw in keywords
        }
        
        significant = (change_percent >= settings.CHANGE_THRESHOLD or
                      any(v["old"] != v["new"] for v in changes.values()))
        
        return {
            "significant": significant,
            "change_percent": change_percent,
            "details": changes
        }

    @classmethod
    def analyze_changes(cls, old_content: str, new_content: str, doc_name: str) -> Dict[str, Any]:
        """Route to appropriate analyzer"""
        return (cls.analyze_iso_changes(old_content, new_content) if "ISO" in doc_name
                else cls.analyze_gmp_changes(old_content, new_content))