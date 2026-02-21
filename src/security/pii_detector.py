"""
PII (Personally Identifiable Information) Detection & Redaction
Protects sensitive data in healthcare context
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Types of PII to detect"""
    SSN = "social_security_number"
    CREDIT_CARD = "credit_card"
    PHONE = "phone_number"
    EMAIL = "email_address"
    MEDICAL_ID = "medical_record_number"
    LICENSE_NUMBER = "license_number"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "street_address"


@dataclass
class PIIDetection:
    """Record of detected PII"""
    pii_type: PIIType
    original_value: str
    redacted_value: str
    start_pos: int
    end_pos: int


@dataclass
class PIIScanResult:
    """Result of PII scan"""
    contains_pii: bool
    detected_pii: List[PIIDetection]
    redacted_text: str
    original_text: str
    redaction_count: int


class PIIDetector:
    """
    Detects and redacts PII in user inputs and agent responses
    
    Critical for HIPAA compliance in healthcare context
    """
    
    def __init__(self):
        # PII detection patterns
        self.patterns = {
            PIIType.SSN: [
                r'\b\d{3}-\d{2}-\d{4}\b',  # 123-45-6789
                r'\b\d{9}\b'                # 123456789
            ],
            
            PIIType.CREDIT_CARD: [
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # 1234 5678 9012 3456
                r'\b\d{13,16}\b'  # 13-16 digit numbers
            ],
            
            PIIType.PHONE: [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
                r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'   # (123) 456-7890
            ],
            
            PIIType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            
            PIIType.MEDICAL_ID: [
                r'\bMRN[-:]?\s*\d{6,10}\b',  # MRN: 12345678
                r'\bMEDICAL\s+ID[-:]?\s*\d{6,10}\b'
            ],
            
            PIIType.LICENSE_NUMBER: [
                r'\b[A-Z]{2}-[A-Z]{2,3}-\d{6}\b'  # CA-RN-123456 (already in our system)
            ],
            
            PIIType.DATE_OF_BIRTH: [
                r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b',  # MM/DD/YYYY
                r'\b(19|20)\d{2}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])\b'   # YYYY-MM-DD
            ]
        }
        
        # Redaction templates
        self.redaction_templates = {
            PIIType.SSN: "***-**-####",
            PIIType.CREDIT_CARD: "**** **** **** ####",
            PIIType.PHONE: "***-***-####",
            PIIType.EMAIL: "***@***.***",
            PIIType.MEDICAL_ID: "MRN: ********",
            PIIType.LICENSE_NUMBER: "**-**-######",
            PIIType.DATE_OF_BIRTH: "**/**/****",
            PIIType.ADDRESS: "[ADDRESS REDACTED]"
        }
    
    def scan(self, text: str, redact: bool = True) -> PIIScanResult:
        """
        Scan text for PII
        
        Args:
            text: Input text to scan
            redact: Whether to redact detected PII
            
        Returns:
            PIIScanResult with detections and redacted text
        """
        
        detections = []
        redacted_text = text
        
        # Scan for each PII type
        for pii_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    original_value = match.group()
                    
                    # Skip if it's a medical license we're intentionally processing
                    if pii_type == PIIType.LICENSE_NUMBER and self._is_intentional_license(text):
                        continue
                    
                    # Create redacted value
                    if redact:
                        redacted_value = self._create_redaction(original_value, pii_type)
                        redacted_text = redacted_text.replace(original_value, redacted_value)
                    else:
                        redacted_value = original_value
                    
                    detections.append(PIIDetection(
                        pii_type=pii_type,
                        original_value=original_value,
                        redacted_value=redacted_value,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
        
        return PIIScanResult(
            contains_pii=len(detections) > 0,
            detected_pii=detections,
            redacted_text=redacted_text,
            original_text=text,
            redaction_count=len(detections)
        )
    
    def _create_redaction(self, original: str, pii_type: PIIType) -> str:
        """
        Create a redacted version of PII
        
        Strategy: Show last 4 digits for verification, mask the rest
        """
        template = self.redaction_templates.get(pii_type, "[REDACTED]")
        
        # For numeric PII, preserve last 4 digits
        if pii_type in [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.PHONE]:
            # Extract just digits
            digits = re.sub(r'\D', '', original)
            if len(digits) >= 4:
                last_four = digits[-4:]
                template = template.replace('####', last_four)
        
        return template
    
    def _is_intentional_license(self, text: str) -> bool:
        """
        Check if license number is intentionally being discussed
        (e.g., in credentialing context)
        """
        intentional_keywords = [
            'verify license',
            'license verification',
            'credentialing',
            'license number',
            'check license'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in intentional_keywords)


# Test the PII detector
if __name__ == "__main__":
    print("🧪 Testing PII Detector\n")
    
    detector = PIIDetector()
    
    test_cases = [
        (
            "My SSN is 123-45-6789 and I can be reached at 555-123-4567.",
            "Multiple PII types"
        ),
        (
            "Please update my contact info: john.doe@email.com and 415-555-1234.",
            "Email and phone"
        ),
        (
            "Patient MRN: 87654321, DOB: 03/15/1985",
            "Medical record number and DOB"
        ),
        (
            "My credit card 4532-1234-5678-9010 was charged incorrectly.",
            "Credit card number"
        ),
        (
            "Please verify license CA-RN-123456 for credentialing.",
            "Intentional license (should not redact)"
        ),
        (
            "What is the PTO policy?",
            "No PII (safe query)"
        )
    ]
    
    for i, (query, description) in enumerate(test_cases, 1):
        print("="*60)
        print(f"Test {i}: {description}")
        print("="*60)
        print(f"Original: \"{query}\"")
        print()
        
        result = detector.scan(query, redact=True)
        
        if result.contains_pii:
            print(f"PII Detected: ⚠️  YES ({result.redaction_count} item(s))")
            print(f"Redacted: \"{result.redacted_text}\"")
            print()
            print("Detected PII:")
            for detection in result.detected_pii:
                print(f"  • {detection.pii_type.value}: {detection.original_value} → {detection.redacted_value}")
        else:
            print(f"PII Detected: ✅ NO")
            print(f"Text: \"{result.redacted_text}\"")
        
        print()
    
    print("="*60)
    print("✅ PII Detection Tests Complete")
    print("="*60)