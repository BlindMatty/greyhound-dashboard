import urllib.request, json, subprocess

# Get token from git credential manager
result = subprocess.run(
    ['git', 'credential', 'fill'],
    input='protocol=https\nhost=github.com\n',
    capture_output=True, text=True
)
token = None
for line in result.stdout.splitlines():
    if line.startswith('password='):
        token = line.split('=', 1)[1]
        break

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
}

# Enable GitHub Pages from main branch root
data = json.dumps({
    'source': {
        'branch': 'main',
        'path': '/'
    }
}).encode()

req = urllib.request.Request(
    'https://api.github.com/repos/BlindMatty/greyhound-dashboard/pages',
    data=data,
    headers=headers
)

try:
    resp = urllib.request.urlopen(req)
    r = json.loads(resp.read())
    print(f"Pages enabled: {r.get('html_url', 'success')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if '409' in str(e.code) or 'already' in body.lower():
        print("Pages already enabled")
    else:
        print(f"Error {e.code}: {body}")

# Check pages status
try:
    req2 = urllib.request.Request(
        'https://api.github.com/repos/BlindMatty/greyhound-dashboard/pages',
        headers=headers
    )
    resp2 = urllib.request.urlopen(req2)
    r2 = json.loads(resp2.read())
    print(f"URL: {r2.get('html_url')}")
    print(f"Status: {r2.get('status')}")
except Exception as e:
    print(f"Status check: {e}")
