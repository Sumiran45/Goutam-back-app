import re
from typing import Any, Dict, List
from fastapi import HTTPException


def validate_phone_number(phone: str) -> bool:
    """Validate Indian phone number format"""
    pattern = r'^(\+91|91|0)?[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_pincode(pincode: str) -> bool:
    """Validate Indian pincode format"""
    return len(pincode) == 6 and pincode.isdigit()


def validate_availability_slots(availability: List[Dict[str, Any]]) -> bool:
    """Validate doctor availability slots don't overlap"""
    for i, slot1 in enumerate(availability):
        for j, slot2 in enumerate(availability[i + 1:], i + 1):
            if slot1['day'] == slot2['day']:
                start1, end1 = slot1['start_time'], slot1['end_time']
                start2, end2 = slot2['start_time'], slot2['end_time']

                # Check for overlap
                if (start1 < end2 and start2 < end1):
                    return False
    return True
