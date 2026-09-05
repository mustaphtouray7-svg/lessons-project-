import urllib.request, urllib.parse, http.cookiejar, re, sys, time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
base = 'http://127.0.0.1:5000'

# GET register page
r = opener.open(base + '/register')
html = r.read().decode('utf-8')
m = re.search(r'name="csrf_token" value="([^\"]+)"', html)
if not m:
    print('NO_CSRF')
    sys.exit(2)

token = m.group(1)
username = f'webtest{int(time.time())}'
email = f'{username}@example.local'
password = 'Testpass123'

# register
post = {
    'csrf_token': token,
    'username': username,
    'email': email,
    'password': password,
    'confirm': password,
}
req = urllib.request.Request(base + '/register', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
body = resp.read().decode('utf-8')
if 'تم إنشاء الحساب بنجاح' not in body and not resp.geturl().endswith('/login'):
    print('REGISTER_FAILED')
    sys.exit(3)

print('REGISTER_OK', username, email)

# GET login page to obtain csrf
r = opener.open(base + '/login')
html = r.read().decode('utf-8')
m = re.search(r'name="csrf_token" value="([^\"]+)"', html)
if not m:
    print('NO_CSRF_LOGIN')
    sys.exit(4)
ltoken = m.group(1)

# login
post = {
    'csrf_token': ltoken,
    'email': email,
    'password': password,
}
req = urllib.request.Request(base + '/login', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
# after login expect redirect to dashboard
if resp.geturl().endswith('/dashboard'):
    print('LOGIN_OK')
else:
    # fetch dashboard to verify
    r = opener.open(base + '/dashboard')
    if r.getcode() == 200:
        print('LOGIN_OK')
    else:
        print('LOGIN_FAILED')
        sys.exit(5)

# logout
r = opener.open(base + '/logout')
if r.geturl().endswith('/') or r.getcode() == 200:
    print('LOGOUT_OK')
else:
    print('LOGOUT_MAYBE_OK')

sys.exit(0)
