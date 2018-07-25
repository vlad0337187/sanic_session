from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except:
    long_description = ''


# Set requirements here
requirements = ('sanic', 'ujson')

extras_require = {
    'aioredis': ['aioredis>=1.0.0'],
    'asyncio_redis': ['asyncio_redis'],
    'mongo': ['sanic_motor', 'pymongo'],
    'aiomcache': ['aiomcache>=0.5.2'],
}

setup(
    name='sanic_session',
    version='0.2.5',
    description='Provides server-backed sessions for Sanic using Redis, Memcache, Mongo, in-memory.',
    long_description=long_description,
    url='(https://github.com/vlad1777d/sanic_session',
    author='Suby Raman',
    license='MIT',
    packages=['sanic_session'],
    # Kludge: Specifying requirements for setup and install works around
    # problem with easyinstall finding sanic_motor instead of sanic.
    # See similar problem:
    #   https://stackoverflow.com/questions/27497470/setuptools-finds-wrong-package-during-install
    #   https://github.com/numpy/numpy/issues/2434
    setup_requires=requirements,
    install_requires=requirements,
    zip_safe=False,
    keywords=['sessions', 'sanic', 'redis', 'memcache'],
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: Session',
    ]
)
