### sanic_session

sanic_session is an extension for sanic that integrates server-backed sessions with a Flask-like API.

sanic_session provides a number of *session interfaces* for you to store a client's session data. The interfaces available right now are:

* Redis (using aioredis, asyncio_redis)
* Memcache (using aiomemcache)
* MongoDB (using sanic_motor)
* In-Memory (suitable for testing and development environments)

## Installation

Install with `pip`:

`pip install sanic_session`

## Documentation

Documentation is available at [PythonHosted](https://pythonhosted.org/sanic_session/).

## Examples

A simple example uses the in-memory session interface.


```python
    from sanic import Sanic
    from sanic.response import text
    import sanic_session


    app = Sanic()
    sanic_session.install_middleware(app, 'InMemorySessionInterface')


    @app.route("/")
    async def index(request):
        # interact with the session like a normal dict
        if not request['session'].get('foo'):
            request['session']['foo'] = 0

        request['session']['foo'] += 1

        return text(request['session']['foo'])

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, debug=True)
```

Using sanic_session with Redis via asyncio_redis.

Install sanic_session to use with asyncio_redis driver: `pip install sanic_session[asyncio_redis]`


```python
    import asyncio_redis

    from sanic import Sanic
    from sanic.response import text
    import sanic_session


    app = Sanic()


    # general (for all app) redis pool
    # (should be filled asynchronously after server start)
    asyncio_redis_pool = None

    @app.listener ('before_server_start')
        async def general_before_server_start (app, loop):
            global asyncio_redis_pool
            asyncio_redis_pool = await asyncio_redis.Pool.create(host='127.0.0.1', port=6379, poolsize=2)
            sanic_session.install_middleware (app, 'AsyncioRedisSessionInterface', asyncio_redis_pool)

    @app.listener ('after_server_stop')
    async def general_after_server_stop (app, loop):
        asyncio_redis_pool.close ()


    @app.route("/")
    async def test(request):
        # interact with the session like a normal dict
        if not request['session'].get('foo'):
            request['session']['foo'] = 0

        request['session']['foo'] += 1

        response = text(request['session']['foo'])

        return response

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, debug=True)
```


Using sanic_session with Memcache via aiomemcache.

Install sanic_session to use with aiomemcache driver: `pip install sanic_session[aiomcache]`


```python
    import aiomcache
    import uvloop

    from sanic import Sanic
    from sanic.response import text
    import sanic_session

    app = Sanic()


    # create a uvloop to pass into the memcache client and sanic
    loop = uvloop.new_event_loop()

    # create a memcache client
    client = aiomcache.Client("127.0.0.1", 11211, loop=loop)

    # install sanic_session middleware with memcache client
    sanic_session.install_middleware (app, 'MemcacheSessionInterface', client)


    @app.route("/")
    async def test(request):
        # interact with the session like a normal dict
        if not request['session'].get('foo'):
            request['session']['foo'] = 0

        request['session']['foo'] += 1

        response = text(request['session']['foo'])

        return response

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, debug=True, loop=loop)
```

