from setuptools import setup, find_packages

setup(
    name='pymt5bot',
    version='1.0',
    packages=find_packages(),
    package_data={'': ['configs/*.json']},
    include_package_data=True,
    install_requires=[
        'MetaTrader5==5.0.45',
        'pandas==2.2.0',
        'ta==0.11.0'
    ],
    entry_points={
        'console_scripts': [
            'run = pymt5bot.__main__:main',
        ],
    },
)
