import requests
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)

def format_iso_message(doc_name: str, changes: Dict[str, Any], url: str) -> str:
    """Format ISO-specific notification"""
    details = []
    if changes["details"]["added"]:
        details.append(f"Added clauses: {', '.join(changes['details']['added'])}")
    if changes["details"]["removed"]:
        details.append(f"Removed clauses: {', '.join(changes['details']['removed'])}")
    
    return (f"📄 *ISO Update*: {doc_name}\n"
            f"Change: {changes['change_percent']:.1f}%\n"
            f"{'\n'.join(details)}\n"
            f"<{url}|View Document>")

def format_gmp_message(doc_name: str, changes: Dict[str, Any], url: str) -> str:
    """Format GMP-specific notification"""
    details = []
    for kw, counts in changes["details"].items():
        if counts["old"] != counts["new"]:
            details.append(f"{kw}: {counts['old']} → {counts['new']}")
    
    return (f"🧪 *GMP Update*: {doc_name}\n"
            f"Change: {changes['change_percent']:.1f}%\n"
            f"{'\n'.join(details)}\n"
            f"<{url}|View Document>")

def send_notification(document_name: str, url: str, changes: Dict[str, Any]) -> None:
    """Send alerts with document-specific formatting"""
    try:
        message = (format_iso_message(document_name, changes, url) if "ISO" in document_name
                 else format_gmp_message(document_name, changes, url))
        
        # Slack Notification
        if settings.SLACK_WEBHOOK:
            try:
                requests.post(
                    settings.SLACK_WEBHOOK,
                    json={"text": message},
                    timeout=settings.REQUEST_TIMEOUT
                )
            except Exception as e:
                logger.error(f"Slack notification failed: {str(e)}")
        
        # Email Notification
        if settings.EMAIL['sender']:
            try:
                msg = MIMEMultipart()
                msg['From'] = settings.EMAIL['sender']
                msg['To'] = ', '.join(settings.EMAIL['recipients'])
                msg['Subject'] = f"Compliance Update: {document_name}"
                msg.attach(MIMEText(message.replace('*', ''), 'plain'))
                
                with smtplib.SMTP(settings.EMAIL['smtp_server'], settings.EMAIL['smtp_port']) as server:
                    server.starttls()
                    server.login(settings.EMAIL['sender'], settings.EMAIL['password'])
                    server.send_message(msg)
            except Exception as e:
                logger.error(f"Email notification failed: {str(e)}")
                
    except Exception as e:
        logger.error(f"Notification processing failed: {str(e)}")