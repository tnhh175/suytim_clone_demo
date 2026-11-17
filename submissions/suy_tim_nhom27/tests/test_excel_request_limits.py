"""Exercise the Excel upload boundary through the production ASGI app without a DB."""

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from src.gateway.main import create_app
from test_auth import FakePool, _ADMIN_ID, _DOCTOR_ID


_MIB = 1024 * 1024
_ROUTES = (('excel/inspect', 6 * _MIB), ('excel/preview', 6 * _MIB), ('commit', 16 * _MIB))


@pytest.fixture
def app():
    pool = FakePool()
    for token, user_id in (('qa-doctor', _DOCTOR_ID), ('qa-admin', _ADMIN_ID)):
        pool.sessions[hashlib.sha256(token.encode()).hexdigest()] = {
            'user_id': user_id,
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'revoked_at': None,
        }
    return create_app(pool=pool, forms_only=True)


def post(app, route, *, token=None, length=None, chunks=()):
    path = '/api/forms/imports/' + route
    headers = [(b'content-type', b'application/json')]
    if token is not None:
        headers.append((b'authorization', f'Bearer {token}'.encode()))
    if length is not None:
        headers.append((b'content-length', str(length).encode()))
    scope = {
        'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
        'method': 'POST', 'scheme': 'http', 'path': path,
        'query_string': b'', 'headers': headers,
        'client': ('192.0.2.20', 12345), 'server': ('127.0.0.1', 8000),
    }
    messages = []
    incoming = iter(chunks)

    async def receive():
        chunk = next(incoming, None)
        assert chunk is not None, 'The route read past the allowed request body'
        body, more_body = chunk
        return {'type': 'http.request', 'body': body, 'more_body': more_body}

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    response = messages[0]
    body = b''.join(message.get('body', b'') for message in messages[1:])
    return response['status'], dict(response['headers']), json.loads(body)


@pytest.mark.parametrize('route,cap', _ROUTES)
def test_oversize_content_length_rejected_before_reading_body(app, route, cap):
    status, _, body = post(app, route, token='qa-doctor', length=cap + 1)
    assert status == 413
    assert body == {'detail': 'Dữ liệu nhập vượt giới hạn kích thước yêu cầu'}


@pytest.mark.parametrize('route,_cap', _ROUTES)
@pytest.mark.parametrize('token,expected', [(None, 401), ('revoked-or-invalid', 401), ('qa-admin', 403)])
def test_excel_checks_auth_before_reading_body(app, route, _cap, token, expected):
    status, headers, _ = post(app, route, token=token)
    assert status == expected
    if expected == 401:
        assert headers[b'www-authenticate'] == b'Bearer'


@pytest.mark.parametrize('route,cap', _ROUTES)
@pytest.mark.parametrize('length', [None, 34], ids=['no-length', 'understated-length'])
def test_chunked_upload_stops_at_wire_limit_despite_missing_or_false_length(app, route, cap, length):
    chunk = b' ' * _MIB
    # Frame after the limit is optional and should never be consumed, even for invalid JSON.
    chunks = [(chunk, True)] * (cap // _MIB) + [(b'!', True)]
    status, _, body = post(app, route, token='qa-doctor', length=length, chunks=chunks)
    assert status == 413
    assert body == {'detail': 'Dữ liệu nhập vượt giới hạn kích thước yêu cầu'}


def test_upload_at_exact_inspect_cap_still_reaches_request_validation(app):
    cap = 6 * _MIB
    content = b'{"filename":"file.xls","content_base64":""}'
    status, _, body = post(app, 'excel/inspect', token='qa-doctor', length=cap,
                           chunks=[(content, True), (b' ' * (cap - len(content)), False)])
    assert status == 422
    assert body['detail']['path'] == '/filename'
