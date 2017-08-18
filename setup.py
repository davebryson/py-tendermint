from setuptools import setup

setup(
    name='Vanilla',
    version='0.1',
    url='https://github.com/davebryson/vanilla',
    license='BSD',
    author='Dave Bryson',
    author_email='debryson@gmail.com',
    description='A microframework for building blockchain applications with Tendermint',
    packages=['vanilla', 'vanilla.abci'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'rlp>=0.6.0',
        'trie>=0.2.4',
        'PyNaCl>=1.1.2',
        'pysha3>=1.0.2',
        'protobuf>=3.4.0',
        'gevent>=1.2.2',
        'colorlog>=3.0.1',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pythonpath==0.7.1'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
