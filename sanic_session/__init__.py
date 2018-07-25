from .aioredis import AIORedisSessionInterface
from .asyncio_redis import AsyncioRedisSessionInterface
from .memcache import MemcacheSessionInterface
from .in_memory import InMemorySessionInterface


def install_middleware(app, interface, *args, **kwargs):
    """Installs middleware to application, which will be launched every request.
    'app' - sanic 'Application' instance to add middleware.
    'interface' - name of interface to use.
    Can be:
        InMemorySessionInterface,
        AIORedisSessionInterface, AsyncioRedisSessionInterface,
        MemcacheSessionInterface, MongoDBSessionInterface
    """
    if interface == 'InMemorySessionInterface':
        session_interface = InMemorySessionInterface(*args, **kwargs)
    elif interface == 'AIORedisSessionInterface':
        session_interface = AIORedisSessionInterface(*args, **kwargs)
    elif interface == 'AsyncioRedisSessionInterface':
        session_interface = AsyncioRedisSessionInterface(*args, **kwargs)
    elif interface == 'MemcacheSessionInterface':
        session_interface = MemcacheSessionInterface(*args, **kwargs)
    elif interface == 'MongoDBSessionInterface':
        session_interface = MongoDBSessionInterface(*args, **kwargs)

    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['session'] = session_interface

    async def add_session_to_request(request):
        """Before each request initialize a session using the client's request.
        """
        await session_interface.open(request)

    async def save_session(request, response):
        """After each request save the session,
        pass the response to set client cookies.
        """
        await session_interface.save(request, response)

    # open session before other middleware:
    app.request_middleware.appendleft(add_session_to_request)
    app.response_middleware.append(save_session)
