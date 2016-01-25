from setuptools import setup
from setuptools import find_packages

import xblog

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
    install_requires=[
        'Django==1.8.8',
        'html2text',
        'BeautifulSoup',
        'django-markdown-deux',
        'Pillow',
        'pytz'
    ]
    
    
    
)