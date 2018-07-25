import time
import uuid
import ujson

import pytest
from unittest.mock import Mock

from sanic.response import text
from sanic_session.asyncio_redis import AsyncioRedisSessionInterface

SID = '5235262626'
COOKIE_NAME = 'cookie'
COOKIES = {COOKIE_NAME: SID}


@pytest.fixture
def mock_dict():
    class MockDict(dict):
        pass

    return MockDict


@pytest.fixture
def mock_redis():
    class MockRedisConnection:
        pass

    return MockRedisConnection


def mock_coroutine(return_value=None):
    async def mock_coro(*args, **kwargs):
        return return_value

    return Mock(wraps=mock_coro)


@pytest.mark.asyncio
async def test_redis_should_create_new_sid_if_no_cookie(
        mocker, mock_redis, mock_dict):
    request = mock_dict()
    request.cookies = {}
    redis_connection = mock_redis()
    redis_connection.get = mock_coroutine()

    mocker.spy(uuid, 'uuid4')
    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        pass_dependency_check=True,
    )
    await session_interface.open(request)

    assert uuid.uuid4.call_count == 1, 'should create a new SID with uuid'
    assert request['session'] == {}, 'should return an empty dict as session'


@pytest.mark.asyncio
async def test_should_return_data_from_redis(mocker, mock_dict, mock_redis):
    request = mock_dict()

    request.cookies = COOKIES

    mocker.spy(uuid, 'uuid4')
    data = {'foo': 'bar'}

    redis_connection = mock_redis()
    redis_connection.get = mock_coroutine(ujson.dumps(data))

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )
    session = await session_interface.open(request)

    assert uuid.uuid4.call_count == 0, 'should not create a new SID'
    assert redis_connection.get.call_count == 1, 'should call on redis once'
    assert redis_connection.get.call_args_list[0][0][0] == \
        'session:{}'.format(SID), 'should call redis with prefix + SID'
    assert session.get('foo') == 'bar', 'session data is pulled from redis'


@pytest.mark.asyncio
async def test_should_use_prefix_in_redis_key(mocker, mock_dict, mock_redis):
    request = mock_dict()
    prefix = 'differentprefix:'
    data = {'foo': 'bar'}

    request.cookies = COOKIES

    redis_connection = mock_redis
    redis_connection.get = mock_coroutine(ujson.dumps(data))

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        prefix=prefix,
        pass_dependency_check=True,
    )
    await session_interface.open(request)

    assert redis_connection.get.call_args_list[0][0][0] == \
        '{}{}'.format(prefix, SID), 'should call redis with prefix + SID'


@pytest.mark.asyncio
async def test_should_use_return_empty_session_via_redis(
        mock_redis, mock_dict):
    request = mock_dict()
    prefix = 'differentprefix:'
    request.cookies = COOKIES

    redis_connection = mock_redis
    redis_connection.get = mock_coroutine()

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        prefix=prefix,
        pass_dependency_check=True,
    )
    session = await session_interface.open(request)

    assert session == {}


@pytest.mark.asyncio
async def test_should_attach_session_to_request(mock_redis, mock_dict):
    request = mock_dict()
    request.cookies = COOKIES

    redis_connection = mock_redis
    redis_connection.get = mock_coroutine()

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )
    session = await session_interface.open(request)

    assert session == request['session']


@pytest.mark.asyncio
async def test_should_delete_session_from_redis(mocker, mock_redis, mock_dict):
    request = mock_dict()
    response = mock_dict()
    request.cookies = COOKIES
    response.cookies = {}

    redis_connection = mock_redis
    redis_connection.get = mock_coroutine()
    redis_connection.delete = mock_coroutine()

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )

    await session_interface.open(request)
    await session_interface.save(request, response)

    assert redis_connection.delete.call_count == 1
    assert(
        redis_connection.delete.call_args_list[0][0][0] ==
        ['session:{}'.format(SID)])
    assert response.cookies == {}, 'should not change response cookies'


@pytest.mark.asyncio
async def test_should_expire_redis_cookies_if_modified(mock_dict, mock_redis):
    request = mock_dict()
    response = text('foo')
    request.cookies = COOKIES

    redis_connection = mock_redis
    redis_connection.get = mock_coroutine()
    redis_connection.delete = mock_coroutine()

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )

    await session_interface.open(request)

    request['session'].clear()
    await session_interface.save(request, response)
    assert response.cookies[COOKIE_NAME]['max-age'] == 0
    assert response.cookies[COOKIE_NAME]['expires'] == 0


@pytest.mark.asyncio
async def test_should_save_in_redis_for_time_specified(mock_dict, mock_redis):
    request = mock_dict()
    request.cookies = COOKIES
    redis_connection = mock_redis
    redis_connection.get = mock_coroutine(ujson.dumps({'foo': 'bar'}))
    redis_connection.setex = mock_coroutine()
    response = text('foo')

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )

    await session_interface.open(request)

    request['session']['foo'] = 'baz'
    await session_interface.save(request, response)

    redis_connection.setex.assert_called_with(
        'session:{}'.format(SID), 2592000,
        ujson.dumps(request['session']))


@pytest.mark.asyncio
async def test_should_reset_cookie_expiry(mocker, mock_dict, mock_redis):
    request = mock_dict()
    request.cookies = COOKIES
    redis_connection = mock_redis
    redis_connection.get = mock_coroutine(ujson.dumps({'foo': 'bar'}))
    redis_connection.setex = mock_coroutine()
    response = text('foo')
    mocker.patch("time.time")
    time.time.return_value = 1488576462.138493

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        pass_dependency_check=True,
    )

    await session_interface.open(request)
    request['session']['foo'] = 'baz'
    await session_interface.save(request, response)

    assert response.cookies[COOKIE_NAME].value == SID
    assert response.cookies[COOKIE_NAME]['max-age'] == 2592000
    assert response.cookies[COOKIE_NAME]['expires'] == "Sun, 02-Apr-2017 21:27:42 GMT"


@pytest.mark.asyncio
async def test_sessioncookie_should_omit_request_headers(mocker, mock_dict):
    request = mock_dict()
    request.cookies = COOKIES
    redis_connection = mock_redis
    redis_connection.get = mock_coroutine(ujson.dumps({'foo': 'bar'}))
    redis_connection.delete = mock_coroutine()
    redis_connection.setex = mock_coroutine()
    response = text('foo')

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        sessioncookie=True,
        pass_dependency_check=True,
    )

    await session_interface.open(request)
    await session_interface.save(request, response)

    assert response.cookies[COOKIE_NAME].value == SID
    assert 'max-age' not in response.cookies[COOKIE_NAME]
    assert 'expires' not in response.cookies[COOKIE_NAME]


@pytest.mark.asyncio
async def test_sessioncookie_delete_has_expiration_headers(mocker, mock_dict):
    request = mock_dict()
    request.cookies = COOKIES
    redis_connection = mock_redis
    redis_connection.get = mock_coroutine(ujson.dumps({'foo': 'bar'}))
    redis_connection.delete = mock_coroutine()
    redis_connection.setex = mock_coroutine()
    response = text('foo')

    session_interface = AsyncioRedisSessionInterface(
        redis_connection,
        cookie_name=COOKIE_NAME,
        sessioncookie=True,
        pass_dependency_check=True,
    )

    await session_interface.open(request)
    await session_interface.save(request, response)
    request['session'].clear()
    await session_interface.save(request, response)

    assert response.cookies[COOKIE_NAME]['max-age'] == 0
    assert response.cookies[COOKIE_NAME]['expires'] == 0
