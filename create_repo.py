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

if not token:
    print("Could not get GitHub token from git credential manager")
    exit(1)

data = json.dumps({
    'name': 'greyhound-dashboard',
    'description': 'Greyhound racing predictions dashboard',
    'private': False
}).encode()

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=data,
    headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
)

try:
    resp = urllib.request.urlopen(req)
    r = json.loads(resp.read())
    print(f"Created: {r['html_url']}")
except urllib.error.HTTPError as e:
    body = json.loads(e.read().decode())
    if e.code == 422 and 'already exists' in str(body):
        print("Repo already exists — that's fine")
    else:
        print(f"Error {e.code}: {body}")
