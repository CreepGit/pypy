import requests

# Application credentials
client_id = 'f09afd48-1772-491d-a014-5e3becd01038'
client_secret = 'Y0H8Q~5.FIk~CAB4lr96BhL8EVSWsfk3nJeQzbXJ'
redirect_uri = 'http://localhost:8000/callback'  # This should match the redirect URI configured in your Azure application

# Authentication endpoints
authorization_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

# User's email API endpoint
email_api_url = 'https://graph.microsoft.com/v1.0/me/messages'

# Step 1: Authentication - Obtain the authorization code
authorization_code = input('Enter the authorization code: ')

# Step 2: Authentication - Exchange the authorization code for an access token
data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': 'authorization_code',
    'code': authorization_code,
    'redirect_uri': redirect_uri
}

response = requests.post(token_url, data=data)
access_token = response.json()['access_token']

# Step 3: Make an API request using the access token
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

response = requests.get(email_api_url, headers=headers)
emails = response.json()['value']

# Print the retrieved emails
for email in emails:
    print(f"Subject: {email['subject']}")
    print(f"Sender: {email['sender']['emailAddress']['name']} ({email['sender']['emailAddress']['address']})")
    print('---')

print('Email retrieval successful!')
