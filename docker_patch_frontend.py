import sys

with open('frontend/api-client.js', 'r') as f:
    content = f.read()

old = """const API_BASE_URL = (() => {
  // Use the same host as the frontend page, but port 8001
  // This works for localhost:8080 → localhost:8001
  // and for remote access: framearch-juan:8080 → framearch-juan:8001
  const host = window.location.hostname;
  return `http://${host}:8001`;
})();"""

new = """const API_BASE_URL = (() => {
  // In Docker: API and frontend share same origin
  return `${window.location.protocol}//${window.location.host}`;
})();"""

if old in content:
    content = content.replace(old, new)
    with open('frontend/api-client.js', 'w') as f:
        f.write(content)
    print('Frontend patched for Docker mode')
else:
    print('WARNING: could not patch frontend api-client.js')
    sys.exit(1)
