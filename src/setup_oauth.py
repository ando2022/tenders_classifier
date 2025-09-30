"""
OAuth Setup Helper for SIMAP.ch API

This script helps you set up OAuth 2.0 authentication with SIMAP.ch
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if OAuth environment is properly configured"""
    print("🔍 Checking OAuth Environment Setup...")
    print("=" * 50)
    
    # Check for client ID
    client_id = os.getenv('SIMAP_CLIENT_ID')
    if client_id:
        print(f"✅ Client ID found: {client_id[:8]}...")
    else:
        print("❌ Client ID not found")
        print("\nTo get a client ID:")
        print("1. Contact SIMAP support to register your application")
        print("2. Provide your company details and intended use")
        print("3. Set the SIMAP_CLIENT_ID environment variable")
        return False
    
    # Check for access token
    access_token = os.getenv('SIMAP_ACCESS_TOKEN')
    if access_token:
        print(f"✅ Access token found: {access_token[:8]}...")
        return True
    else:
        print("ℹ️  No access token found (this is normal for first-time setup)")
        return True

def setup_environment_variables():
    """Help user set up environment variables"""
    print("\n🔧 Environment Variables Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("ℹ️  No .env file found, creating one...")
        env_file.write_text("# SIMAP OAuth Configuration\n")
    
    # Get client ID from user
    client_id = input("Enter your SIMAP Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return False
    
    # Update .env file
    env_content = env_file.read_text()
    
    # Update or add client ID
    if 'SIMAP_CLIENT_ID=' in env_content:
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('SIMAP_CLIENT_ID='):
                lines[i] = f'SIMAP_CLIENT_ID={client_id}'
                break
        env_content = '\n'.join(lines)
    else:
        env_content += f'\nSIMAP_CLIENT_ID={client_id}\n'
    
    # Add other optional settings
    if 'SIMAP_REDIRECT_URI=' not in env_content:
        env_content += 'SIMAP_REDIRECT_URI=http://localhost:8080/callback\n'
    
    if 'SIMAP_SCOPE=' not in env_content:
        env_content += 'SIMAP_SCOPE=openid profile\n'
    
    env_file.write_text(env_content)
    print("✅ Environment variables configured")
    
    # Set environment variable for current session
    os.environ['SIMAP_CLIENT_ID'] = client_id
    os.environ['SIMAP_REDIRECT_URI'] = 'http://localhost:8080/callback'
    os.environ['SIMAP_SCOPE'] = 'openid profile'
    
    return True

def test_oauth_flow():
    """Test the OAuth authentication flow"""
    print("\n🧪 Testing OAuth Flow")
    print("=" * 50)
    
    try:
        from simap import SimapAPI
        
        # Initialize client
        client = SimapAPI()
        
        if client.is_authenticated():
            print("✅ Already authenticated!")
            return True
        
        print("Starting OAuth authentication flow...")
        print("This will open a browser window for SIMAP login.")
        
        # Start authentication
        success = client.authenticate()
        
        if success:
            print("✅ OAuth authentication successful!")
            return True
        else:
            print("❌ OAuth authentication failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ OAuth test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 SIMAP.ch OAuth 2.0 Setup Helper")
    print("=" * 60)
    
    # Step 1: Check environment
    if not check_environment():
        print("\n📝 Setting up environment variables...")
        if not setup_environment_variables():
            print("❌ Environment setup failed")
            return
    
    # Step 2: Test OAuth flow
    print("\n🧪 Testing OAuth authentication...")
    if test_oauth_flow():
        print("\n🎉 OAuth setup completed successfully!")
        print("\nYou can now use the SIMAP API client:")
        print("  python src/oauth_example.py")
        print("  python src/simap.py")
    else:
        print("\n❌ OAuth setup failed")
        print("Please check your client ID and try again")

if __name__ == "__main__":
    main()
