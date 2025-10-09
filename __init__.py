#!/usr/bin/env python3
"""
Healthcare Transmission System Package
=====================================

Modern, well-architected healthcare data transmission system
with SMS API integration, OpenHIM compliance, and proper separation of concerns.
"""

__version__ = "1.0.0"
__author__ = "Healthcare Transmission Team"

from .src.core.factory import (
    create_development_system,
    create_production_system,
    HealthcareTransmissionFactory
)
from .src.core.models import (
    OpenHIMMessage,
    DataType,
    TransmissionProtocol,
    NetworkCondition,
    MessageStatus,
    HealthcarePatient,
    LabResult,
    Prescription
)

__all__ = [
    'create_development_system',
    'create_production_system',
    'HealthcareTransmissionFactory',
    'OpenHIMMessage',
    'DataType',
    'TransmissionProtocol',
    'NetworkCondition',
    'MessageStatus',
    'HealthcarePatient',
    'LabResult',
    'Prescription'
]