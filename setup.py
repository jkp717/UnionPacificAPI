from setuptools import setup, find_packages

setup(
    name='UnionPacificAPI',
    version='0.0.1',
    author='Josh Price',
    author_email='joshkprice717@gmail.com',
    description="A python client library for Union Pacific's API",
    packages=find_packages(),
    install_requires=[
        'requests>=2.32.0',
        'python-dotenv>=1.0.0',
        'urllib3>=2.2.3',
        'dacite>=1.8.0'
    ],
)

# run 'python setup.py install'