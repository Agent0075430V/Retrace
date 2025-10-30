import os
import sys
import django

# Add project root to path so 'Retrace' package can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

# create test user
u, created = User.objects.get_or_create(username='apitest_img_script', defaults={'email':'apitest_img_script@example.com'})
if created:
    u.set_password('testpass')
    u.save()

t, _ = Token.objects.get_or_create(user=u)
print('token', t.key)
client = APIClient(); client.credentials(HTTP_AUTHORIZATION='Token ' + t.key)

# create a simple red image in memory
img = Image.new('RGB', (64, 64), color=(255, 0, 0))
buf = BytesIO(); img.save(buf, format='JPEG'); buf.seek(0)
# Use SimpleUploadedFile so filename and content-type are provided
image_content = buf.getvalue()
uploaded = SimpleUploadedFile('test.jpg', image_content, content_type='image/jpeg')

# POST lost with image
resp_lost = client.post('/api/ai/lost/', {'name': 'ImgLostScript', 'description': 'desc', 'email': 'owner@example.com', 'image': uploaded}, format='multipart')
print('create lost', resp_lost.status_code, resp_lost.content)

# Reset buffer for second upload
buf.seek(0)
uploaded2 = SimpleUploadedFile('test2.jpg', image_content, content_type='image/jpeg')
resp_found = client.post('/api/ai/found/', {'name': 'ImgFoundScript', 'description': 'desc', 'email': 'finder@example.com', 'image': uploaded2}, format='multipart')
print('create found', resp_found.status_code, resp_found.content)

# Check matches
resp_matches = client.get('/api/ai/matches/')
print('matches', resp_matches.status_code, resp_matches.content)

# Trigger manual match for the lost created
if resp_lost.status_code == 201:
    lost_id = resp_lost.json().get('id')
    resp_manual = client.post(f'/api/ai/lost/{lost_id}/match/')
    print('manual match', resp_manual.status_code, resp_manual.content)
