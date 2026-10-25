"""Public login entry point remains usable without a database connection."""
import pytest
from fastapi.testclient import TestClient

from src.gateway.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_shared_login_and_forms_shell_are_publicly_available(client):
    for path in ('/login', '/', '/forms'):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/html')
        assert 'forms.js' in response.text


@pytest.mark.parametrize('path', ['/admin/login', '/bac-si/login'])
def test_legacy_login_bookmarks_redirect_to_shared_login(client, path):
    response = client.get(path, follow_redirects=False)
    assert response.status_code in (301, 302, 303, 307, 308)
    assert response.headers['location'] == '/login'
    shared_page = client.get(response.headers['location'])
    assert shared_page.status_code == 200
