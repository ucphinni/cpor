#!/usr/bin/env python3
"""
Test script to verify Google Cloud Pub/Sub access for Nest events.
"""
import os
import json
import asyncio
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
SUBSCRIPTION_ID = os.getenv('PUBSUB_SUBSCRIPTION_ID')
CLIENT_ID = os.getenv('NEST_CLIENT_ID')
CLIENT_SECRET = os.getenv('NEST_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('NEST_REFRESH_TOKEN')

def get_credentials():
    """Create credentials object for Pub/Sub."""
    return Credentials.from_authorized_user_info({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': [
            'https://www.googleapis.com/auth/pubsub',
            'https://www.googleapis.com/auth/sdm.service'
        ]
    })

def test_pubsub_connection():
    """Test Pub/Sub connection and list subscriptions."""
    print("Testing Pub/Sub connection...")
    print(f"Project ID: {GCP_PROJECT_ID}")
    print(f"Subscription: {SUBSCRIPTION_ID}")
    
    try:
        # Create credentials
        credentials = get_credentials()
        
        # Create subscriber client
        subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        
        # List all subscriptions in the project
        project_path = f"projects/{GCP_PROJECT_ID}"
        print(f"\nListing subscriptions in project: {project_path}")
        
        subscriptions = subscriber.list_subscriptions(
            request={"project": project_path}
        )
        
        print("\nAvailable subscriptions:")
        for subscription in subscriptions:
            print(f"  - {subscription.name}")
            
        # Test specific subscription
        if SUBSCRIPTION_ID:
            print(f"\nTesting subscription: {SUBSCRIPTION_ID}")
            try:
                subscription = subscriber.get_subscription(
                    request={"subscription": SUBSCRIPTION_ID}
                )
                print(f"Subscription found: {subscription.name}")
                print(f"Topic: {subscription.topic}")
                print(f"Ack deadline: {subscription.ack_deadline_seconds}s")
                return True
            except Exception as e:
                print(f"Error accessing subscription: {e}")
                return False
        else:
            print("No PUBSUB_SUBSCRIPTION_ID configured")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def listen_for_messages(timeout=30):
    """Listen for Pub/Sub messages for a specified timeout."""
    print(f"\nListening for messages for {timeout} seconds...")
    
    try:
        credentials = get_credentials()
        subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        
        def callback(message):
            print(f"\nReceived message:")
            print(f"  Data: {message.data.decode('utf-8')}")
            print(f"  Attributes: {dict(message.attributes)}")
            print(f"  Message ID: {message.message_id}")
            message.ack()
        
        # Pull messages
        flow_control = pubsub_v1.types.FlowControl(max_messages=100)
        streaming_pull_future = subscriber.subscribe(
            SUBSCRIPTION_ID, 
            callback=callback,
            flow_control=flow_control
        )
        
        print(f"Listening for messages on {SUBSCRIPTION_ID}...")
        
        try:
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()
            print(f"No messages received within {timeout} seconds")
        
    except Exception as e:
        print(f"Error listening for messages: {e}")

def main():
    """Main function to test Pub/Sub."""
    print("Testing Google Cloud Pub/Sub for Nest events...")
    
    # Test connection first
    if test_pubsub_connection():
        print("\n✅ Pub/Sub connection successful!")
        
        # Ask user if they want to listen for messages
        print("\nTo test real-time messages, trigger a Nest device event")
        print("(e.g., change thermostat temperature, motion detection)")
        
        listen_for_messages(30)
    else:
        print("\n❌ Pub/Sub connection failed!")
        print("\nTroubleshooting steps:")
        print("1. Ensure Pub/Sub API is enabled in Google Cloud Console")
        print("2. Verify your subscription exists and is properly configured")
        print("3. Check that your OAuth token has pubsub scope")

if __name__ == '__main__':
    main()
