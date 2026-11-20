'''
Created on Nov 18, 2026

@author: keith.chambers
'''

from EvalEDSApp.eds import EDSConnectionProfile
from common.configuration import ConfigValidationError


print("\n--- EDS Connection Profile Tests ---")

# Test 1: Default profile
profile = EDSConnectionProfile()

print("\nTest 1: Default profile")
print(profile)

try:
    profile.validate()
    print("PASS: Default profile is valid.")
except ConfigValidationError as exc:
    print(f"FAIL: {exc}")


# Test 2: Invalid port
print("\nTest 2: Invalid port")

profile = EDSConnectionProfile(port=70000)

try:
    profile.validate()
    print("FAIL: Invalid port was accepted.")
except ConfigValidationError as exc:
    print(f"PASS: Invalid port rejected: {exc}")


print("\n--- Tests Complete ---")
