import os
from setuptools import setup, find_packages

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name = "geocoding",
    version = "0.0.1",
    author = "Johannes Lohse, Catherine Taelman",
    author_email = "jlo031@uit.no",
    description = ("Geocoding for different satellite sensors."),
    license = "The Ask Johannes Before You Do Anything License",
    long_description=read('README.md'),
    install_requires = [
        'numpy',
        'scipy',
        'ipython',
        'loguru',
        'lxml',
        'python-dotenv',
    ],
    packages = find_packages(where='src'),
    package_dir = {'': 'src'},
    package_data = {'': ['*.xml', '.env']},
    entry_points = {
        'console_scripts': [
        ]
    },
    include_package_data=True,
)
