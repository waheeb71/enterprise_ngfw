"""
Enterprise NGFW v2.0 - SMTP Inspector Plugin

Deep inspection of SMTP/email traffic.

Features:
- SMTP command validation
- Email header analysis
- Attachment detection
- Spam detection
- Phishing detection
- Sender verification

Author: Enterprise NGFW Team
License: Proprietary
"""

import re
import base64
import logging
from typing import Dict, List, Optional, Set
from email import policy
from email.parser import BytesParser

from inspection.framework import (
    InspectorPlugin,
    PluginPriority,
    InspectionContext,
    InspectionResult,
    InspectionAction,
    InspectionFinding
)


class SMTPInspector(InspectorPlugin):
    """
    SMTP traffic inspector.
    
    Detects:
    - Malicious attachments
    - Phishing attempts
    - Spam characteristics
    - Suspicious commands
    """
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.scr', '.bat', '.cmd', '.com', '.pif',
        '.vbs', '.js', '.jar', '.msi', '.dll',
        '.ps1', '.psm1',  # PowerShell
    }
    
    # Phishing indicators in subject/body
    PHISHING_KEYWORDS = [
        'verify your account',
        'confirm your identity',
        'suspended account',
        'unusual activity',
        'click here immediately',
        'urgent action required',
        'reset your password',
        'wire transfer',
        'bitcoin',
        'cryptocurrency',
    ]
    
    # Spam indicators
    SPAM_KEYWORDS = [
        'you have won',
        'claim your prize',
        'limited time offer',
        'act now',
        'free money',
        'make money fast',
        'work from home',
        'no credit check',
    ]
    
    def __init__(
        self,
        priority: PluginPriority = PluginPriority.HIGH,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(
            name="SMTP Inspector",
            priority=priority,
            logger=logger
        )
        
        # Configuration
        self._max_attachment_size_mb = 25
        self._block_dangerous_extensions = True
        self._scan_attachments = True
        
    def can_inspect(self, context: InspectionContext) -> bool:
        """Check if this is SMTP traffic"""
        smtp_ports = {25, 587, 465}  # SMTP, submission, SMTPS
        
        return (
            context.protocol == 'TCP' and
            (context.dst_port in smtp_ports or context.src_port in smtp_ports)
        )
        
    def inspect(
        self,
        context: InspectionContext,
        data: bytes
    ) -> InspectionResult:
        """Inspect SMTP traffic"""
        result = InspectionResult(action=InspectionAction.ALLOW)
        
        try:
            # Try to parse as SMTP commands first
            smtp_data = self._parse_smtp_commands(data)
            
            if smtp_data:
                result.metadata['smtp'] = smtp_data
                self._inspect_commands(smtp_data, result)
                
            # Try to parse as email message
            email_data = self._parse_email(data)
            
            if email_data:
                result.metadata['email'] = email_data
                
                # Inspect headers
                self._inspect_headers(email_data, result)
                
                # Inspect subject/body
                self._inspect_content(email_data, result)
                
                # Inspect attachments
                if self._scan_attachments:
                    self._inspect_attachments(email_data, result)
                    
        except Exception as e:
            self.logger.error(f"SMTP inspection failed: {e}")
            
        return result
        
    def _parse_smtp_commands(self, data: bytes) -> Optional[Dict]:
        """Parse SMTP commands"""
        try:
            text = data.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            
            smtp_data = {
                'commands': [],
                'responses': []
            }
            
            for line in lines:
                if not line:
                    continue
                    
                # Check if command (client to server)
                if line and line[0].isalpha():
                    parts = line.split(' ', 1)
                    command = parts[0].upper()
                    args = parts[1] if len(parts) > 1 else ''
                    
                    smtp_data['commands'].append({
                        'command': command,
                        'args': args
                    })
                    
                # Check if response (server to client)
                elif line and line[0].isdigit():
                    smtp_data['responses'].append(line)
                    
            return smtp_data if smtp_data['commands'] or smtp_data['responses'] else None
            
        except Exception as e:
            self.logger.debug(f"SMTP command parsing failed: {e}")
            return None
            
    def _parse_email(self, data: bytes) -> Optional[Dict]:
        """Parse email message"""
        try:
            # Parse email
            parser = BytesParser(policy=policy.default)
            msg = parser.parsebytes(data)
            
            email_data = {
                'from': msg.get('From', ''),
                'to': msg.get('To', ''),
                'subject': msg.get('Subject', ''),
                'date': msg.get('Date', ''),
                'message_id': msg.get('Message-ID', ''),
                'headers': dict(msg.items()),
                'body': '',
                'attachments': []
            }
            
            # Get body
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == 'text/plain':
                        try:
                            email_data['body'] += part.get_content()
                        except:
                            pass
                            
                    # Check for attachments
                    elif part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename:
                            email_data['attachments'].append({
                                'filename': filename,
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
            else:
                try:
                    email_data['body'] = msg.get_content()
                except:
                    pass
                    
            return email_data
            
        except Exception as e:
            self.logger.debug(f"Email parsing failed: {e}")
            return None
            
    def _inspect_commands(self, smtp_data: Dict, result: InspectionResult) -> None:
        """Inspect SMTP commands"""
        dangerous_commands = {'DEBUG', 'EXPN', 'VRFY'}
        
        for cmd_data in smtp_data.get('commands', []):
            command = cmd_data['command']
            
            if command in dangerous_commands:
                result.findings.append(InspectionFinding(
                    severity='MEDIUM',
                    category='smtp_command',
                    description=f"Suspicious SMTP command: {command}",
                    plugin_name=self.name,
                    confidence=0.8,
                    evidence={'command': command}
                ))
                
    def _inspect_headers(self, email_data: Dict, result: InspectionResult) -> None:
        """Inspect email headers"""
        headers = email_data.get('headers', {})
        
        # Check for spoofed sender
        from_addr = email_data.get('from', '').lower()
        
        # Check for missing important headers
        important_headers = ['From', 'To', 'Date', 'Message-ID']
        missing = [h for h in important_headers if h not in headers]
        
        if missing:
            result.findings.append(InspectionFinding(
                severity='MEDIUM',
                category='smtp_headers',
                description=f"Missing email headers: {', '.join(missing)}",
                plugin_name=self.name,
                confidence=0.7,
                evidence={'missing_headers': missing}
            ))
            
        # Check for suspicious domains in From
        suspicious_domains = ['@mailinator.com', '@tempmail.com', '@guerrillamail.com']
        
        for domain in suspicious_domains:
            if domain in from_addr:
                result.findings.append(InspectionFinding(
                    severity='MEDIUM',
                    category='smtp_sender',
                    description="Temporary/suspicious email domain",
                    plugin_name=self.name,
                    confidence=0.85,
                    evidence={'from': from_addr, 'domain': domain}
                ))
                break
                
    def _inspect_content(self, email_data: Dict, result: InspectionResult) -> None:
        """Inspect email subject and body"""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        content = f"{subject} {body}"
        
        # Check for phishing
        phishing_score = 0
        matched_phishing = []
        
        for keyword in self.PHISHING_KEYWORDS:
            if keyword in content:
                phishing_score += 1
                matched_phishing.append(keyword)
                
        if phishing_score >= 2:
            result.action = InspectionAction.BLOCK
            result.findings.append(InspectionFinding(
                severity='HIGH',
                category='smtp_phishing',
                description=f"Potential phishing email detected",
                plugin_name=self.name,
                confidence=min(0.9, 0.5 + (phishing_score * 0.1)),
                evidence={
                    'matched_keywords': matched_phishing,
                    'score': phishing_score
                }
            ))
            
        # Check for spam
        spam_score = 0
        matched_spam = []
        
        for keyword in self.SPAM_KEYWORDS:
            if keyword in content:
                spam_score += 1
                matched_spam.append(keyword)
                
        if spam_score >= 3:
            result.findings.append(InspectionFinding(
                severity='MEDIUM',
                category='smtp_spam',
                description="Potential spam email detected",
                plugin_name=self.name,
                confidence=min(0.85, 0.5 + (spam_score * 0.1)),
                evidence={
                    'matched_keywords': matched_spam,
                    'score': spam_score
                }
            ))
            
        # Check for suspicious URLs
        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, content)
        
        if len(urls) > 10:
            result.findings.append(InspectionFinding(
                severity='MEDIUM',
                category='smtp_content',
                description=f"Excessive URLs in email: {len(urls)}",
                plugin_name=self.name,
                confidence=0.7,
                evidence={'url_count': len(urls)}
            ))
            
    def _inspect_attachments(
        self,
        email_data: Dict,
        result: InspectionResult
    ) -> None:
        """Inspect email attachments"""
        attachments = email_data.get('attachments', [])
        
        for attachment in attachments:
            filename = attachment.get('filename', '').lower()
            size = attachment.get('size', 0)
            
            # Check dangerous extensions
            if self._block_dangerous_extensions:
                for ext in self.DANGEROUS_EXTENSIONS:
                    if filename.endswith(ext):
                        result.action = InspectionAction.BLOCK
                        result.findings.append(InspectionFinding(
                            severity='CRITICAL',
                            category='smtp_attachment',
                            description=f"Dangerous file attachment: {filename}",
                            plugin_name=self.name,
                            confidence=1.0,
                            evidence={
                                'filename': filename,
                                'extension': ext
                            }
                        ))
                        break
                        
            # Check size
            size_mb = size / (1024 * 1024)
            
            if size_mb > self._max_attachment_size_mb:
                result.findings.append(InspectionFinding(
                    severity='MEDIUM',
                    category='smtp_attachment',
                    description=f"Large attachment: {size_mb:.2f} MB",
                    plugin_name=self.name,
                    confidence=0.8,
                    evidence={
                        'filename': filename,
                        'size_mb': size_mb,
                        'limit_mb': self._max_attachment_size_mb
                    }
                ))
