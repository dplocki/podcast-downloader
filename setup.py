import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='podcast_downloader',
    author="Dawid Plocki",
    author_email="dawid.plocki@gmail.com",
    version='0.1',
    description='The script for downloading the recent mp3 from given RSS channels',
    long_description_content_type='text/markdown',
    long_description=read('README.md'),
    packages=['podcast_downloader'],
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7'
    ]
)