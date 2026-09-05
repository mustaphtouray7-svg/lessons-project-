import io
found = False
with io.open('app.py','r',encoding='utf-8') as f:
    for i,l in enumerate(f, start=1):
        if 'query.get' in l or '.query.get(' in l or '.get_or_404' in l:
            print(i, l.rstrip())
            found = True
if not found:
    print('NO_MATCH')
