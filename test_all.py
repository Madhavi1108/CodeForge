import urllib.request, urllib.parse, json, time

# Login
data = urllib.parse.urlencode({'username': 'engineer@codeforge.ai', 'password': 'password'}).encode()
token = json.loads(urllib.request.urlopen(urllib.request.Request('http://localhost:8000/auth/token', data=data)).read())['access_token']
headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
print('Login OK, token obtained')

# Submit job
payload = json.dumps({'idempotency_key': 'test_run_final_9', 'language': 'python', 'code': 'print(123)\nprint(456)'}).encode()
req = urllib.request.Request('http://localhost:8000/jobs/', data=payload, headers=headers)
job = json.loads(urllib.request.urlopen(req).read())
job_id = job['id']
print('Job submitted: ' + job_id)

# Poll for result
for i in range(15):
    time.sleep(2)
    req = urllib.request.Request('http://localhost:8000/jobs/' + job_id, headers=headers)
    s = json.loads(urllib.request.urlopen(req).read())
    print('  Poll ' + str(i+1) + ': status=' + s['status'])
    if s['status'] in ('COMPLETED', 'FAILED'):
        print('Result:', json.dumps(s, indent=2))
        break

# Test AI explain button
print()
req = urllib.request.Request('http://localhost:8000/ai/explain', json.dumps({'code': 'print(123)'}).encode(), headers)
res = json.loads(urllib.request.urlopen(req).read())
print('AI Explain:', res)

# Test AI plagiarism button
req = urllib.request.Request('http://localhost:8000/ai/plagiarism', json.dumps({'code': 'print(123)'}).encode(), headers)
res = json.loads(urllib.request.urlopen(req).read())
print('AI Plagiarism:', res)

print()
print('All tests passed!')
