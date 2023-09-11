from msal import ConfidentialClientApplication, PublicClientApplication
from msal.authority import AuthorityBuilder, WORLD_WIDE
from typing import Optional

tenant_id = "d0efd9a1-732f-49d6-93cd-ad6ef86f7def"
username = 'viranomaisasiat.jarjestelma@uuva.fi'
password = 'WGpfi086!2#dDZc-'
client_id = 'f09afd48-1772-491d-a014-5e3becd01038'
authority = f'https://login.microsoftonline.com/{tenant_id}'
testisalaisuus_value = r"2s~8Q~OF_nZEN.RaoBHVbJoP9R-ppJeFwmmxBa3m"
scopes = ['User.Read']

scopes += ['Mail.Read']

pca = ConfidentialClientApplication(client_id, authority=authority, client_credential=testisalaisuus_value)
token = None # type: ignore

accounts = pca.get_accounts()
if accounts:
    result = pca.acquire_token_silent(scopes, account=accounts[0])
    token = result.get('access_token') # type: ignore

# If a token could not be obtained silently, fallback to interactive authentication
if not token:
    result = pca.acquire_token_by_username_password(
        username=username,
        password=password,        
        scopes=scopes,
    )
    if 'access_token' in result:
        token = result['access_token']
    else:
        print(result.get('error', ''))
        print(result.get('error_description', 'Authentication failed.'))
        print(":(")
    token = result.get('access_token') # type: ignore

if not token:
    print("NO TOKEN")
    quit()

token: str
print(token)

print()
import requests
graph_data = requests.get(  # Use token to call downstream service
    "https://graph.microsoft.com/v1.0/me/messages/",
    headers={'Authorization': 'Bearer ' + token},
).json()
print(graph_data)

"""https://login.microsoftonline.com/d0efd9a1-732f-49d6-93cd-ad6ef86f7def/adminconsent?client_id=f09afd48-1772-491d-a014-5e3becd01038"""

# Client secret value for "testisalaisuus"
# CMJ8Q~q.zhL2DLY0l_I1e.f_pB6MBRJpT__BPa5S
# ID = 398f8445-d70c-4430-9add-d126b306c5eb

# uwu owo
# 2s~8Q~OF_nZEN.RaoBHVbJoP9R-ppJeFwmmxBa3m
# ID = 4e80597d-a7be-4c5e-b3b9-7f5bbe94be4c

# New client secret
# xWw8Q~zzeGianvf~UtlHDUxzUp_CuEk6jQaA8aLH

# print(app)
# print(app.__dict__)


# username = 'viranomaisasiat.jarjestelma@uuva.fi'
# password = 'WGpfi086!2#dDZc-'

# token = app.acquire_token_by_username_password(
#     username=username,
#     password=password,
#     scopes=["User.Read"],
# )

# print(token)


# import imaplib

# username = 'viranomaisasiat.jarjestelma@uuva.fi'
# password = 'WGpfi086!2#dDZc-'
# print("CONNECTING")
# MAIL = imaplib.IMAP4_SSL('outlook.office365.com', port=993)
# print("START TLS")
# MAIL.starttls()
# # MAIL2 = imaplib.IMAP4('outlook.office365.com', port=993)
# print("LOGGING IN")
# MAIL.login(username, password)
# # MAIL2.login(username, password)
# print("LOGGED IN")
# MAIL.select("INBOX")

# print(MAIL)
# print(MAIL2)

# Server name: outlook.office365.com
# Port: 993
# Encryption method: TLS

