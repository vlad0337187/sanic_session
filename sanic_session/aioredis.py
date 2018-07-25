from .base import BaseSessionInterface


def check_aioredis_installed():
    """Check aioredis installed, if absent - raises error.
    """
    try:
        import aioredis
    except ImportError:
        raise RuntimeError("Please install aioredis: pip install sanic_session[aioredis]")


class AIORedisSessionInterface(BaseSessionInterface):
    def __init__(
            self,
            redis,
            domain: str=None,
            expiry: int = 2592000,
            httponly: bool=True,
            cookie_name: str='session',
            prefix: str='session:',
            sessioncookie: bool=False,
            pass_dependency_check: bool=False,
        ):
        """Initializes a session interface backed by Redis.
        Args:
            redis (Callable):
                aioredis connection or connection pool instance.
            domain (str, optional):
                Optional domain which will be attached to the cookie.
            expiry (int, optional):
                Seconds until the session should expire.
            httponly (bool, optional):
                Adds the `httponly` flag to the session cookie.
            cookie_name (str, optional):
                Name used for the client cookie.
            prefix (str, optional):
                Memcache keys will take the format of `prefix+session_id`;
                specify the prefix here.
            sessioncookie (bool, optional):
                Specifies if the sent cookie should be a 'session cookie', i.e
                no Expires or Max-age headers are included. Expiry is still
                fully tracked on the server side. Default setting is False.
            pass_dependency_check (bool, optional):
                Specifies, whether to check: are dependencies for
                session interface installed.
                Check can be passed, for example, when running tests.
        """
        if not pass_dependency_check:
            check_aioredis_installed()

        self.redis = redis
        self.expiry = expiry
        self.prefix = prefix
        self.cookie_name = cookie_name
        self.domain = domain
        self.httponly = httponly
        self.sessioncookie = sessioncookie

    async def _get_value(self, prefix, sid):
        return await self.redis.get(self.prefix + sid)

    async def _delete_key(self, key):
        await self.redis.delete(key)

    async def _set_value(self, key, data):
        await self.redis.setex(key, self.expiry, data)

