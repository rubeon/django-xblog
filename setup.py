from setuptools import setup
from setuptools import find_packages
from pip.req import parse_requirements
import pip
import xblog

REQUIREMENTS_FILE = "xblog/requirements.txt"

requirements = [str(ir.req) for ir in parse_requirements(REQUIREMENTS_FILE,  session=pip.download.PipSession())]

setup(
    name='django-xblog',
    version=xblog.__version__,
    description="A full-featured blogging application for your Django site",
    long_description=open('README.md').read(),
    keywords='django, blog, weblog, bootstrap, metaWeblog, wordpress',
    author=xblog.__author__,
    author_email=xblog.__email__,
    url=xblog.__url__,
    packages=find_packages(),
    classifiers=[
        'Framework :: Django :: 1.8',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
    ],
    license=xblog.__license__,
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
)