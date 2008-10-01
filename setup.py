from setuptools import setup, find_packages
import sys, os

version = '0.4'

setup(name='twitter',
      version=version,
      description="An API and command-line toolset for Twitter (twitter.com)",
      long_description="""\
An API and command-line toolset for Twitter (twitter.com). Includes:

  * a lightweight Twitter API access class.
  * a twitter command-line tool for setting your status and getting your
    friends' status
  * a twitter IRC bot for announcing status updates to an IRC channel

""",
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
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
      install_requires=[
          # -*- Extra requirements: -*-
          "simplejson>=1.7.1",
          "dateutil>=1.1",
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      twitter=twitter.cmdline:main
      twitterbot=twitter.ircbot:main
      """,
      )
