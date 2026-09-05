import urllib.request
import urllib.parse
import http.cookiejar

BASE = 'http://127.0.0.1:5000'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path):
    url = BASE + path
    try:
        r = opener.open(url, timeout=10)
        print(f'GET {path} =>', r.getcode())
        return r
    except Exception as e:
        print(f'GET {path} FAILED:', e)
        return None

def post(path, data):
    url = BASE + path
    data_enc = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data_enc)
    try:
        r = opener.open(req, timeout=10)
        print(f'POST {path} =>', r.getcode())
        return r
    except urllib.error.HTTPError as e:
        print(f'POST {path} HTTPError:', e.code)
        return e
    except Exception as e:
        print(f'POST {path} FAILED:', e)
        return None

if __name__ == '__main__':
    get('/')
    get('/register')
    get('/login')
    get('/lessons')
    get('/lesson/1')

    # register new user
    post('/register', {'username':'apitest3','email':'apitest3@example.com','password':'testpass'})
    # login
    post('/login', {'email':'apitest3@example.com','password':'testpass'})
    # dashboard
    get('/dashboard')

    # admin login
    post('/login', {'email':'admin@local','password':'admin123'})
    get('/admin')

    print('Script finished')
