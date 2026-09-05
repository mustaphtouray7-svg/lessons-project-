import urllib.request, urllib.parse, http.cookiejar, re, sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
base = 'http://127.0.0.1:5000'

# GET login page
r = opener.open(base + '/login')
html = r.read().decode('utf-8')
m = re.search(r'name="csrf_token" value="([^\"]+)"', html)
if not m:
    print('NO_CSRF_LOGIN')
    sys.exit(2)
ltoken = m.group(1)

# login as admin
post = {
    'csrf_token': ltoken,
    'email': 'admin@local',
    'password': 'admin123',
}
req = urllib.request.Request(base + '/login', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
# verify admin access
r = opener.open(base + '/admin')
if r.getcode() != 200:
    print('ADMIN_ACCESS_FAIL', r.getcode())
    sys.exit(3)

html = r.read().decode('utf-8')
# extract csrf token for admin forms
m = re.search(r'name="csrf_token" value="([^\"]+)"', html)
if not m:
    print('NO_ADMIN_CSRF')
    sys.exit(4)
csrf = m.group(1)

# add lesson
title = 'Automated Lesson'
description = 'Desc'
content = 'Some content'
video = ''
post = {'csrf_token': csrf, 'title': title, 'description': description, 'content': content, 'video_url': video}
req = urllib.request.Request(base + '/admin/add', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
# fetch admin to confirm added
r = opener.open(base + '/admin')
html = r.read().decode('utf-8')
if title not in html:
    print('ADD_FAIL')
    sys.exit(5)
print('ADD_OK')

# find the lesson id from edit form action
m = re.search(r'action="/admin/edit/(\d+)"', html)
if not m:
    print('NO_LESSON_ID')
    sys.exit(6)
lesson_id = m.group(1)

# edit lesson
new_title = title + ' EDIT'
post = {'csrf_token': csrf, 'title': new_title, 'description': description, 'content': content+' edited', 'video_url': video}
req = urllib.request.Request(base + f'/admin/edit/{lesson_id}', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
# confirm edit
r = opener.open(base + '/admin')
html = r.read().decode('utf-8')
if new_title not in html:
    print('EDIT_FAIL')
    sys.exit(7)
print('EDIT_OK')

# delete lesson
post = {'csrf_token': csrf}
req = urllib.request.Request(base + f'/admin/delete/{lesson_id}', data=urllib.parse.urlencode(post).encode('utf-8'))
req.add_header('Content-Type','application/x-www-form-urlencoded')
resp = opener.open(req)
# confirm deletion
r = opener.open(base + '/admin')
html = r.read().decode('utf-8')
if new_title in html:
    print('DELETE_FAIL')
    sys.exit(8)
print('DELETE_OK')

print('ADMIN_FLOW_OK')
