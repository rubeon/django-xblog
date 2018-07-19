import pip
import xblog

from setuptools import setup
from setuptools import find_packages

# try: # for pip >= 10
#     from pip._internal.req import parse_requirements
# except ImportError: # for pip <= 9.0.3
#    from pip.req import parse_requirements


REQUIREMENTS_FILE = "xblog/requirements.txt"

# requirements = [str(ir.req) for ir in parse_requirements(REQUIREMENTS_FILE,  session=pip.download.PipSession())]

REQUIREMENTS = open(REQUIREMENTS_FILE).readlines()

setup(
    name='django-xblog',
    version=xblog.__version__,
    description="A full-featured blogging application for your Django site",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords='django, blog, weblog, bootstrap, metaWeblog, wordpress',
    author=xblog.__author__,
    author_email=xblog.__email__,
    url=xblog.__url__,
    packages=find_packages(),
    classifiers=(
        'Framework :: Django :: 1.8',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
    ),
    license=xblog.__license__,
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
      
)
