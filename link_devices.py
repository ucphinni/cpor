#!/usr/bin/env python3
"""
Create a device linking authorization URL for Google Device Access.
This URL will prompt the user to authorize their Google Home devices 
for use with the Device Access project.
"""

# Your Device Access project configuration
CLIENT_ID = "572931968974-a8j2o61lsdet2ilc4n9lhp17l0npp3oj.apps.googleusercontent.com"
PROJECT_ID = "fdb963af-b95c-47c2-978e-8cc889b05b8d"
REDIRECT_URI = "http://localhost:8081/"

def create_device_linking_url():
    """Create the authorization URL for device linking."""
    
    base_url = "https://nestservices.google.com/partnerconnections"
    
    # Parameters for device linking
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/sdm.service",
        "project_id": PROJECT_ID
    }
    
    # Build the URL
    param_string = "&".join([f"{key}={value}" for key, value in params.items()])
    authorization_url = f"{base_url}?{param_string}"
    
    print("Device Linking Authorization URL:")
    print("=" * 50)
    print(authorization_url)
    print("=" * 50)
    print()
    print("Instructions:")
    print("1. Copy the URL above and paste it into your browser")
    print("2. Sign in with ucphinni@gmail.com (the account that has your Nest devices)")
    print("3. You should see a prompt to authorize access to your Nest devices")
    print("4. Accept the authorization to link your devices to the Device Access project")
    print("5. After success, your devices should appear in the API responses")
    print()
    print("Note: This is different from the previous OAuth flow - this specifically")
    print("links your Google Home devices to the Device Access project.")
    
    return authorization_url

if __name__ == "__main__":
    create_device_linking_url()
