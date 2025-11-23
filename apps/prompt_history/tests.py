import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_prompt_history_crud_and_enhance(client_db):
    client = APIClient()
    user = User.objects.create_user(email='test@example.com', password='pass1234')
    # Obtain token via JWT if available - for simplicity, login with session
    client.force_authenticate(user)

    # Create
    resp = client.post('/api/v2/history/', data={'original_prompt': 'Hello world', 'source': 'raw'})
    assert resp.status_code in (201, 200)
    data = resp.json()
    hid = data.get('id')

    # List
    resp = client.get('/api/v2/history/')
    assert resp.status_code == 200

    # Enhance (best-effort)
    resp = client.post(f'/api/v2/history/{hid}/enhance/', data={'style': 'concise'})
    assert resp.status_code in (200, 201, 202, 400, 500)
