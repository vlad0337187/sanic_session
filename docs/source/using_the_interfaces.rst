.. _using_the_interfaces:

Using the interfaces
=====================

Redis
-----------------
`Redis <https://redis.io/>`_ is a popular and widely supported key-value store. In order to interface with redis, you will need to add :code:`asyncio_redis` to your project. Do so with pip:

:code:`pip install asyncio_redis`

To integrate Redis with :code:`sanic_session` you need to pass a getter method into the :code:`RedisSessionInterface` which returns a connection pool. This is required since there is no way to synchronously create a connection pool. An example is below:

.. code-block:: python

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

Memcache
-----------------
`Memcache <https://memcached.org/>`_ is another popular key-value storage system. In order to interface with memcache, you will need to add :code:`aiomcache` to your project. Do so with pip:

:code:`pip install aiomcache`

To integrate memcache with :code:`sanic_session` you need to pass an :code:`aiomcache.Client` into the session interface, as follows:


.. code-block:: python

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

In-Memory
-----------------

:code:`sanic_session` comes with an in-memory interface which stores sessions in a Python dictionary available at :code:`session_interface.session_store`. This interface is meant for testing and development purposes only. **This interface is not suitable for production**.

.. code-block:: python

    from sanic import Sanic
    from sanic.response import text
    import sanic_session


    app = Sanic()


    # install sanic_session middleware
    sanic_session.install_middleware (app, 'InMemorySessionInterface')


    @app.route("/")
    async def index(request):
        # interact with the session like a normal dict
        if not request['session'].get('foo'):
            request['session']['foo'] = 0

        request['session']['foo'] += 1

        return text(request['session']['foo'])

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, debug=True)
