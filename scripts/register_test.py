import urllib.request, urllib.parse, http.cookiejar, re, sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
base = 'http://127.0.0.1:5000'

# GET register page
r = opener.open(base + '/register')
html = r.read().decode('utf-8')
#m = re.search(r'name="csrf_token" value="([^"]+)"', html)
m = re.search(r'name="csrf_token" value="([^\"]+)"', html)
if not m:
    print('NO_CSRF')
    sys.exit(2)

token = m.group(1)
print('CSRF:', token[:10] + '...')

# prepare registration data
import time
username = f'testuser{int(time.time())}'
email = f'{username}@example.local'
password = 'Testpass123'
data = {
    'csrf_token': token,
    'username': username,
    'email': email,
    'password': password,
    'confirm': password,
}
post_data = urllib.parse.urlencode(data).encode('utf-8')
req = urllib.request.Request(base + '/register', data=post_data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
resp = opener.open(req)
body = resp.read().decode('utf-8')
if 'تم إنشاء الحساب بنجاح' in body or resp.geturl().endswith('/login'):
    print('REGISTER_OK')
    print('username:', username, 'email:', email)
    sys.exit(0)
else:
    print('REGISTER_FAILED')
    print(body[:500])
    sys.exit(3)
