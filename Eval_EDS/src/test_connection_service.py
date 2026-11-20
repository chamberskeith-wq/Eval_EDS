'''
Created on Nov 18, 2026

@author: keith.chambers
'''
from EvalEDSApp.eds import (
    EDSConnectionProfile,
    EDSConnectionService,
)


profile = EDSConnectionProfile()

service = EDSConnectionService()

# Test using a candidate profile
print("\n--- Candidate Profile Test ---")

result = service.test_connection(profile)

print("Success:", result.success)
print("Message:", result.message)
print("Connected:", service.is_connected)
print("Active profile:", service.active_profile)


# Make the profile active
print("\n--- Set Active Profile ---")

service.set_active_profile(profile)

print("Active profile:", service.active_profile)


# Retrieve configuration using the active profile
print("\n--- Configuration Retrieval ---")

result = service.get_configuration()

print("Success:", result.success)
print("Message:", result.message)

if result.success:
    print("Components:")

    components = result.response_data.get(
        "System", {}
    ).get("Components", [])

    for component in components:
        print(
            component["componentId"],
            component["componentType"]
        )