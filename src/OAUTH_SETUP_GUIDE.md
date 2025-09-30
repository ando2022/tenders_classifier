# SIMAP.ch OAuth 2.0 Setup Guide

## 🔐 OAuth 2.0 Authentication with SIMAP.ch

The SIMAP.ch API uses **OAuth 2.0 with PKCE (Proof Key for Code Exchange)** for secure authentication. This guide will help you set up authentication with your existing SIMAP account.

## 📋 Prerequisites

- ✅ Existing SIMAP.ch account mapped to a company
- ✅ Access to the company's SIMAP account
- ✅ Python environment with required dependencies

## 🚀 Step-by-Step Setup

### Step 1: Get Client ID from SIMAP Support

Since you have a working SIMAP account, you need to request API access:

#### Contact SIMAP Support
1. **Visit SIMAP Support**: Go to the SIMAP website and find the support/contact section
2. **Request API Access**: Send a request for machine-to-machine API access
3. **Provide Company Details**: Include your company information and intended use

#### Information to Include in Your Request:
```
Subject: API Access Request for [Your Company Name]

Dear SIMAP Support Team,

I am requesting OAuth 2.0 API access for our company's SIMAP account. Here are the details:

- Company Name: [Your Company Name]
- Account Email: [Your registered email]
- Account Type: Company account
- Intended Use: Automated tender monitoring and opportunity identification
- Technical Requirements: OAuth 2.0 with PKCE for secure API access
- Redirect URI: http://localhost:8080/callback

Please provide the necessary OAuth client credentials and documentation.

Best regards,
[Your Name]
[Your Contact Information]
```

### Step 2: Configure Environment Variables

Once you receive your client ID from SIMAP support:

```bash
# Set your client ID
export SIMAP_CLIENT_ID="your_client_id_here"

# Optional: Customize redirect URI (default: http://localhost:8080/callback)
export SIMAP_REDIRECT_URI="http://localhost:8080/callback"

# Optional: Customize scope (default: openid profile)
export SIMAP_SCOPE="openid profile"
```

### Step 3: Test OAuth Authentication

Run the OAuth authentication example:

```bash
python src/oauth_example.py
```

This will:
1. Check for your client ID
2. Open a browser window for SIMAP login
3. Guide you through the 2FA process
4. Complete the OAuth flow

### Step 4: Use the API Client

After successful authentication, you can use the API client:

```python
from src.simap import SimapAPI

# Initialize client (will use stored tokens)
client = SimapAPI()

# Check if authenticated
if client.is_authenticated():
    # Get tenders
    tenders = client.get_tenders(limit=10)
    
    # Search for opportunities
    results = client.search_tenders(
        query="economics OR policy OR research",
        limit=20
    )
```

## 🔄 OAuth Flow Details

### What Happens During Authentication:

1. **Authorization Request**: Client generates PKCE challenge
2. **Browser Redirect**: User is redirected to SIMAP login page
3. **User Login**: User logs in with SIMAP credentials
4. **2FA Process**: User completes two-factor authentication
5. **Callback**: User is redirected back with authorization code
6. **Token Exchange**: Client exchanges code for access token
7. **Token Storage**: Tokens are saved for future use

### Security Features:

- **PKCE (Proof Key for Code Exchange)**: Prevents authorization code interception
- **2FA Required**: All actions require two-factor authentication
- **Token Refresh**: Automatic token refresh when expired
- **Secure Storage**: Tokens stored in environment variables

## 🛠️ Troubleshooting

### Common Issues:

#### 1. "No client ID found"
```bash
# Solution: Set the client ID
export SIMAP_CLIENT_ID="your_client_id_here"
```

#### 2. "Authentication failed"
- Check your SIMAP account credentials
- Ensure 2FA is working (check email for codes)
- Verify the redirect URI matches your client configuration

#### 3. "Token expired"
```python
# The client will automatically refresh tokens
# If refresh fails, re-authenticate:
client.authenticate()
```

#### 4. "Browser didn't open"
- Manually open the authorization URL
- Copy the code from the callback URL
- Paste it when prompted

## 📚 API Usage Examples

### Basic Usage:
```python
from src.simap import SimapAPI

# Initialize and authenticate
client = SimapAPI()
if not client.is_authenticated():
    client.authenticate()

# Get recent tenders
tenders = client.get_tenders(limit=20)

# Search for specific opportunities
results = client.search_tenders(
    query="economics OR policy",
    limit=50
)
```

### Advanced Usage:
```python
# Filter by date range
from datetime import datetime, timedelta

date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
date_to = datetime.now().strftime('%Y-%m-%d')

filtered_tenders = client.get_tenders(
    limit=100,
    date_from=date_from,
    date_to=date_to,
    search_term="consulting OR advisory"
)
```

## 🔒 Security Best Practices

1. **Never commit tokens**: Use environment variables
2. **Rotate tokens**: Re-authenticate periodically
3. **Secure storage**: Store tokens securely in production
4. **Monitor usage**: Track API usage and costs

## 📞 Support

If you encounter issues:

1. **Check SIMAP Documentation**: https://int.simap.ch/api-doc
2. **Contact SIMAP Support**: Use the official support channels
3. **Review OAuth Flow**: Ensure all steps are completed correctly
4. **Check Network**: Verify internet connectivity and firewall settings

## ✅ Next Steps

After successful OAuth setup:

1. **Test API Calls**: Run `python src/oauth_example.py`
2. **Explore Data**: Use the search and filtering capabilities
3. **Integrate with BAK Workflow**: Implement opportunity identification
4. **Monitor Performance**: Track API usage and response times

## 🎯 BAK Economics Integration

The OAuth authentication enables you to:

- **Automated Tender Monitoring**: Set up scheduled checks for new opportunities
- **Keyword-based Filtering**: Use BAK Economics keywords for relevant tenders
- **Opportunity Scoring**: Implement the scoring system for tender evaluation
- **Data Integration**: Connect with your existing BAK Economics workflows

Your SIMAP API integration is now ready for production use with secure OAuth 2.0 authentication! 🚀
