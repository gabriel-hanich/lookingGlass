from setuptools import setup, find_packages

setup(
    name="notes",
    version="0.1.0",
    packages=find_packages(),
    py_modules=['notes'],
    entry_points={
        'console_scripts': [
            'notes = notes:cli',
        ],
    },
)
