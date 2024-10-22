from setuptools import setup, find_packages

setup(
    name='api',
    version='0.0.1',
    author='Josh Price',
    author_email='joshkprice717@gmail.com',
    description="A python client library for Union Pacific's API",
    packages=find_packages(),
    install_requires=[
        'requests>=2.0.0',
        'python-dotenv>=1.0.0',
        'urllib>=2.2.0',
    ],
)

# run 'python setup.py install'