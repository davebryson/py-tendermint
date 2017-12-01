from setuptools import setup

setup(
<<<<<<< HEAD
    name='vanilla',
    version='0.1.1',
    url='https://github.com/davebryson/vanilla',
    license='Apache 2.0',
    author='Dave Bryson',
    description='A microframework for building blockchain applications with Tendermint',
    packages=['vanilla'],
=======
    name='tendermint',
    version='0.3.0',
    url='https://github.com/davebryson/py-tendermint',
    license='Apache 2.0',
    author='Dave Bryson',
    description='A microframework for building blockchain applications with Tendermint',
    packages=['tendermint'],
>>>>>>> better_flow
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
<<<<<<< HEAD
        'abci==0.2.0',
=======
        'abci==0.3.0',
>>>>>>> better_flow
        'rlp==0.4.7',
        'trie==0.2.4',
        'PyNaCl>=1.1.2',
        'pysha3>=1.0.2',
        'colorlog>=3.0.1',
        'requests>=2.18.4',
        'click>=6.7'
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
        'Programming Language :: Python :: 3.6'
    ]
)
