from setuptools import setup

setup(
    name='PyPUZ',
    version='0.1.0',
    author='Alex Boisvert et al.',
    author_email='crosswordnexus@gmail.com',
    packages=['pypuz'],
    py_modules=['pypuz'],
    scripts=[],
    #url='http://pypi.python.org/pypi/PackageName/',
    license='LICENSE.txt',
    description='Reading and writing crossword files in Python',
    long_description=open('README.txt').read(),
    install_requires=[],
)
