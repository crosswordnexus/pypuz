from setuptools import setup, find_packages

setup(
    name='pypuz',
    version='2024.1.25.1',
    author='Alex Boisvert et al.',
    author_email='crosswordnexus@gmail.com',
    packages=find_packages(),
    #url='http://pypi.python.org/pypi/PackageName/',
    license='LICENSE.txt',
    description='Reading and writing crossword files in Python',
    long_description=open('README.txt').read(),
    install_requires=[],
)
