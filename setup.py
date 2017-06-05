#!/usr/bin/env python3

import os.path
from distutils.core import setup

exec(open('./cancelot/metadata.py').read())

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='cancelot',
      version=__version__,
      description='ENS bid monitoring and cancellation utilities',
      long_description=read('README.rst'),
      author='Noel Maersk',
      author_email='veox+packages+spamremove@veox.pw',
      url=__url__,
      packages=['cancelot'],
      classifiers=[
          'Programming Language :: Python :: 3',
      ],
)
