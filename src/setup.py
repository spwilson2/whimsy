from setuptools import setup, find_packages

setup(
    name = 'whimsy',
    version = '0.0.0-dev',
    author = 'Sean Wilson',
    author_email = 'spwilson2@wisc.edu',
    license = 'BSD',
    entry_points=
    '''
    [console_scripts]
    whimsy=whimsy.main:main
    ''',
    #{
    #    'console_scripts': ['whimsy = whimsy.main']
    #    },
    packages=find_packages(),
)
