from setuptools import setup, find_packages

setup(
    name='lookingglass',
    version='0.0.1',
    py_modules=['glass'],
    include_package_data=True,
    install_requires=[
        'Click',
        'click_prompt'  
    ],
    entry_points={
        'console_scripts': [
            'glass = glass:cli',
        ],
    },
)