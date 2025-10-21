#!/usr/bin/env python3
"""Test logging utilities"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

from shared.logging import setup_logger, log_with_context

print("=" * 60)
print("TESTING LOGGING MODULE")
print("=" * 60)

# Test text logging
print("\n1. Text Logger:")
text_logger = setup_logger('test_text', level='INFO', format_type='text')
text_logger.info("This is an info message")
text_logger.warning("This is a warning")
text_logger.error("This is an error")

# Test JSON logging
print("\n2. JSON Logger:")
json_logger = setup_logger('test_json', level='DEBUG', format_type='json')
json_logger.debug("Debug message with JSON format")
json_logger.info("Info message with JSON format")

# Test context logging
print("\n3. Context Logging:")
log_with_context(
    text_logger,
    'info',
    'Processing request',
    user_id='12345',
    request_id='req-abc',
    duration_ms=125
)

print("\n" + "=" * 60)
print("✅ LOGGING MODULE TEST PASSED")
print("=" * 60)
