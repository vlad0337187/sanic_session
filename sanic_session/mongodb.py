from datetime import datetime, timedelta

from .base import BaseSessionInterface


def check_sanic_motor_installed():
    """Check sanic_motor installed, if absent - raises error.
    """
    try:
        import sanic_motor
    except ImportError:
        msg = "Please install Mongo dependencies: pip install sanic_session[mongo]"
        raise RuntimeError(msg)


def get_base_model():
    """Get base model for session storing.
    """
    try:
        from sanic_motor import BaseModel

        class _SessionModel(BaseModel):
            """Collection for session storing.
            Collection name (default session)
            Fields:
                sid
                expiry
                data:
                    User's session data
            """
            pass

    except ImportError:  # pragma: no cover
        _SessionModel = None

    return _SessionModel


_SessionModel = get_base_model()


class MongoDBSessionInterface(BaseSessionInterface):
    def __init__(
            self, app, coll: str='session',
            domain: str=None,
            expiry: int=30*24*60*60,
            httponly: bool=True,
            cookie_name: str='session',
            sessioncookie: bool=False,
            pass_dependency_check: bool=False):

        """Initializes the interface for storing client sessions in MongoDB.
        Args:
            app (sanic.Sanic):
                Sanic instance to register listener('after_server_start')
            coll (str, optional):
                MongoDB collection name for session
            domain (str, optional):
                Optional domain which will be attached to the cookie.
            expiry (int, optional):
                Seconds until the session should expire.
            httponly (bool, optional):
                Adds the `httponly` flag to the session cookie.
            cookie_name (str, optional):
                Name used for the client cookie.
            sessioncookie (bool, optional):
                Specifies if the sent cookie should be a 'session cookie', i.e
                no Expires or Max-age headers are included. Expiry is still
                fully tracked on the server side. Default setting is False.
        """
        if not pass_dependency_check:
            check_sanic_motor_installed()

        self.expiry = expiry
        self.cookie_name = cookie_name
        self.domain = domain
        self.httponly = True
        self.sessioncookie = sessioncookie
        # prefix not needed for mongodb as mongodb uses uuid4 natively
        self.prefix = ''

        # set collection name
        _SessionModel.__coll__ = coll

        @app.listener('after_server_start')
        async def apply_session_indexes(app, loop):
            """Create indexes in session collection
            if doesn't exist.
            Indexes:
                sid:
                    For faster lookup.
                expiry:
                    For document expiration.
            """
            await _SessionModel.create_index('sid')
            await _SessionModel.create_index('expiry', expireAfterSeconds=0)

    async def _get_value(self, prefix, key):
        await _SessionModel.find_one({'sid': key}, as_raw=True)

    async def _delete_key(self, key):
        await _SessionModel.delete_one({'sid': key})

    async def _set_value(self, key, data):
        expiry = datetime.utcnow() + timedelta(seconds=self.expiry)
        await _SessionModel.replace_one(
            {'sid': key},
            {
                'sid': key,
                'expiry': expiry,
                'data': data
            },
            upsert=True
        )
