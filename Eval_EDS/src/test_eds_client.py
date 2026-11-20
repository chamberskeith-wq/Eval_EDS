'''
Created on Nov 18, 2026

@author: keith.chambers
'''
from EvalEDSApp.eds import EDSClient, EDSConnectionProfile


profile = EDSConnectionProfile()
client = EDSClient()

# Test connectivity
print("\n--- Connection Test ---")

result = client.test_connection(profile)

print("Success:", result.success)
print("Message:", result.message)
print("HTTP status:", result.status_code)


# Retrieve configuration
print("\n--- Configuration Retrieval ---")

result = client.get_configuration(profile)

print("Success:", result.success)
print("Message:", result.message)
print("HTTP status:", result.status_code)

if result.success:
    configuration = result.response_data

    print("Components:")

    components = configuration.get(
        "System", {}
    ).get("Components", [])

    for component in components:
        print(
            component["componentId"],
            component["componentType"]
        )