from setuptools import setup, find_packages
import sys, os

version = '1.12.1'

install_requires = [
    # -*- Extra requirements: -*-
    ]

setup(name='twitter',
      version=version,
      description="An API and command-line toolset for Twitter (twitter.com)",
      long_description=open("./README", "r").read(),
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Topic :: Communications :: Chat :: Internet Relay Chat",
          "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
          "Topic :: Utilities",
          "License :: OSI Approved :: MIT License",
          ],
      keywords='twitter, IRC, command-line tools, web 2.0',
      author='Mike Verdone',
      author_email='mike.verdone+twitterapi@gmail.com',
      url='http://mike.verdone.ca/twitter/',
      license='MIT License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      twitter=twitter.cmdline:main
      twitterbot=twitter.ircbot:main
      twitter-log=twitter.logger:main
      twitter-archiver=twitter.archiver:main
      twitter-follow=twitter.follow:main
      twitter-stream-example=twitter.stream_example:main
      """,
      )
