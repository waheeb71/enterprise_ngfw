"""
Enterprise NGFW v2.0 - HTTP Inspector Plugin

Deep inspection of HTTP/HTTPS traffic.

Features:
- HTTP method validation
- Header analysis
- URL inspection
- Body content scanning
- File upload detection
- Suspicious pattern detection

Author: Enterprise NGFW Team
License: Proprietary
"""

import re
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, parse_qs

from inspection.framework import (
    InspectorPlugin,
    PluginPriority,
    InspectionContext,
    InspectionResult,
    InspectionAction,
    InspectionFinding
)


class HTTPInspector(InspectorPlugin):
    """
    HTTP/HTTPS traffic inspector.
    
    Performs deep inspection of HTTP traffic including:
    - Method validation
    - Header analysis
    - URL inspection
    - Content scanning
    """
    
    # Suspicious patterns in URLs
    SUSPICIOUS_URL_PATTERNS = [
        r'\.\./', # Directory traversal
        r'%2e%2e', # Encoded directory traversal
        r'<script', # XSS attempt
        r'javascript:', # JavaScript injection
        r'union\s+select', # SQL injection
        r'exec\s*\(', # Command injection
        r'eval\s*\(', # Code injection
        r'/etc/passwd', # File disclosure
        r'/proc/', # System info disclosure
    ]
    
    # Dangerous HTTP methods
    DANGEROUS_METHODS = {'TRACE', 'TRACK', 'DEBUG', 'CONNECT'}
    
    # Suspicious headers
    SUSPICIOUS_HEADERS = {
        'X-Forwarded-For': r'\d+\.\d+\.\d+\.\d+',  # IP spoofing attempts
        'X-Real-IP': r'\d+\.\d+\.\d+\.\d+',
        'User-Agent': r'(sqlmap|nikto|nmap|masscan|metasploit)',  # Scanning tools
        'Referer': r'(\.\.\/|%2e%2e)',  # Directory traversal
    }
    
    # Large file thresholds (MB)
    MAX_UPLOAD_SIZE_MB = 100
    
    def __init__(
        self,
        priority: PluginPriority = PluginPriority.HIGH,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(
            name="HTTP Inspector",
            priority=priority,
            logger=logger
        )
        
        # Compile patterns
        self._url_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SUSPICIOUS_URL_PATTERNS
        ]
        
        # Configuration
        self._block_dangerous_methods = True
        self._scan_headers = True
        self._scan_body = True
        self._max_upload_size_mb = self.MAX_UPLOAD_SIZE_MB
        
    def can_inspect(self, context: InspectionContext) -> bool:
        """Check if this is HTTP traffic"""
        # HTTP typically on ports 80, 8080, 8000, etc.
        http_ports = {80, 8080, 8000, 8888, 3000, 5000}
        
        return (
            context.protocol == 'TCP' and
            (context.dst_port in http_ports or context.src_port in http_ports)
        )
        
    def inspect(
        self,
        context: InspectionContext,
        data: bytes
    ) -> InspectionResult:
        """Inspect HTTP traffic"""
        result = InspectionResult(action=InspectionAction.ALLOW)
        
        try:
            # Parse HTTP request/response
            http_data = self._parse_http(data)
            
            if not http_data:
                return result
                
            # Store in metadata
            result.metadata['http'] = http_data
            
            # Inspect request method
            if 'method' in http_data:
                self._inspect_method(http_data, result)
                
            # Inspect URL
            if 'url' in http_data:
                self._inspect_url(http_data, result)
                
            # Inspect headers
            if 'headers' in http_data and self._scan_headers:
                self._inspect_headers(http_data, result)
                
            # Inspect body
            if 'body' in http_data and self._scan_body:
                self._inspect_body(http_data, result)
                
            # Check for file uploads
            if 'content_type' in http_data:
                self._inspect_uploads(http_data, result)
                
        except Exception as e:
            self.logger.error(f"HTTP inspection failed: {e}")
            
        return result
        
    def _parse_http(self, data: bytes) -> Optional[Dict]:
        """Parse HTTP request/response"""
        try:
            # Decode data
            text = data.decode('utf-8', errors='ignore')
            
            lines = text.split('\r\n')
            if not lines:
                return None
                
            # Parse first line (request line or status line)
            first_line = lines[0]
            http_data = {}
            
            # Check if request or response
            if first_line.startswith('HTTP/'):
                # Response
                parts = first_line.split(' ', 2)
                http_data['type'] = 'response'
                http_data['version'] = parts[0] if len(parts) > 0 else ''
                http_data['status_code'] = parts[1] if len(parts) > 1 else ''
                http_data['status_text'] = parts[2] if len(parts) > 2 else ''
            else:
                # Request
                parts = first_line.split(' ')
                if len(parts) >= 3:
                    http_data['type'] = 'request'
                    http_data['method'] = parts[0]
                    http_data['url'] = parts[1]
                    http_data['version'] = parts[2]
                    
            # Parse headers
            headers = {}
            body_start = 0
            
            for i, line in enumerate(lines[1:], 1):
                if not line:
                    body_start = i + 1
                    break
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
                    
            http_data['headers'] = headers
            
            # Get body
            if body_start < len(lines):
                http_data['body'] = '\r\n'.join(lines[body_start:])
                
            # Extract content type
            if 'Content-Type' in headers:
                http_data['content_type'] = headers['Content-Type']
                
            # Extract content length
            if 'Content-Length' in headers:
                try:
                    http_data['content_length'] = int(headers['Content-Length'])
                except:
                    pass
                    
            return http_data
            
        except Exception as e:
            self.logger.debug(f"HTTP parsing failed: {e}")
            return None
            
    def _inspect_method(self, http_data: Dict, result: InspectionResult) -> None:
        """Inspect HTTP method"""
        method = http_data.get('method', '').upper()
        
        if method in self.DANGEROUS_METHODS and self._block_dangerous_methods:
            result.action = InspectionAction.BLOCK
            result.findings.append(InspectionFinding(
                severity='HIGH',
                category='http_method',
                description=f"Dangerous HTTP method: {method}",
                plugin_name=self.name,
                confidence=1.0,
                evidence={'method': method}
            ))
            
    def _inspect_url(self, http_data: Dict, result: InspectionResult) -> None:
        """Inspect URL for suspicious patterns"""
        url = http_data.get('url', '')
        
        # Check against patterns
        for pattern in self._url_patterns:
            if pattern.search(url):
                result.action = InspectionAction.BLOCK
                result.findings.append(InspectionFinding(
                    severity='HIGH',
                    category='http_url',
                    description=f"Suspicious URL pattern detected",
                    plugin_name=self.name,
                    confidence=0.95,
                    evidence={
                        'url': url[:500],  # Truncate long URLs
                        'pattern': pattern.pattern
                    }
                ))
                break
                
        # Check URL length (potential buffer overflow)
        if len(url) > 2048:
            result.findings.append(InspectionFinding(
                severity='MEDIUM',
                category='http_url',
                description=f"Abnormally long URL: {len(url)} bytes",
                plugin_name=self.name,
                confidence=0.8,
                evidence={'url_length': len(url)}
            ))
            
    def _inspect_headers(self, http_data: Dict, result: InspectionResult) -> None:
        """Inspect HTTP headers"""
        headers = http_data.get('headers', {})
        
        for header_name, pattern_str in self.SUSPICIOUS_HEADERS.items():
            if header_name in headers:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                value = headers[header_name]
                
                if pattern.search(value):
                    result.findings.append(InspectionFinding(
                        severity='MEDIUM',
                        category='http_header',
                        description=f"Suspicious {header_name} header",
                        plugin_name=self.name,
                        confidence=0.7,
                        evidence={
                            'header': header_name,
                            'value': value[:200]
                        }
                    ))
                    
    def _inspect_body(self, http_data: Dict, result: InspectionResult) -> None:
        """Inspect HTTP body"""
        body = http_data.get('body', '')
        
        if not body:
            return
            
        # Check for common attack patterns in body
        attack_patterns = [
            (r'<script[^>]*>.*?</script>', 'XSS attempt in body'),
            (r'union\s+select', 'SQL injection in body'),
            (r'exec\s*\(', 'Command injection in body'),
        ]
        
        for pattern_str, description in attack_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
            if pattern.search(body):
                result.action = InspectionAction.BLOCK
                result.findings.append(InspectionFinding(
                    severity='HIGH',
                    category='http_body',
                    description=description,
                    plugin_name=self.name,
                    confidence=0.9,
                    evidence={'body_sample': body[:500]}
                ))
                break
                
    def _inspect_uploads(self, http_data: Dict, result: InspectionResult) -> None:
        """Inspect file uploads"""
        content_type = http_data.get('content_type', '')
        content_length = http_data.get('content_length', 0)
        
        # Check if this is a file upload
        if 'multipart/form-data' in content_type:
            size_mb = content_length / (1024 * 1024)
            
            result.findings.append(InspectionFinding(
                severity='INFO',
                category='http_upload',
                description=f"File upload detected ({size_mb:.2f} MB)",
                plugin_name=self.name,
                confidence=1.0,
                evidence={
                    'size_mb': size_mb,
                    'content_type': content_type
                }
            ))
            
            # Check size limit
            if size_mb > self._max_upload_size_mb:
                result.findings.append(InspectionFinding(
                    severity='MEDIUM',
                    category='http_upload',
                    description=f"Upload exceeds size limit",
                    plugin_name=self.name,
                    confidence=1.0,
                    evidence={
                        'size_mb': size_mb,
                        'limit_mb': self._max_upload_size_mb
                    }
                ))
