from setuptools import setup, find_packages

with open("README") as f:
    long_description = f.read()


def local_scheme(version):
    """Skip the local version (eg. +xyz of 0.6.1.dev4+gdf99fe2)
    to be able to upload to Test PyPI"""
    return ""

setup(name='twitter',
      description="An API and command-line toolset for Twitter (twitter.com)",
      long_description=long_description,
      long_description_content_type="text/markdown",
      python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Programming Language :: Python :: 3.10",
          "Programming Language :: Python :: 3.11",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
          "Topic :: Communications :: Chat :: Internet Relay Chat",
          "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
          "Topic :: Utilities",
          "License :: OSI Approved :: MIT License",
          ],
      keywords='twitter, IRC, command-line tools, web 2.0',
      author='Mike Verdone',
      author_email='mike.verdone+twitterapi@gmail.com',
      url='https://mike.verdone.ca/twitter/',
      license='MIT License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      use_scm_version={"local_scheme": local_scheme},
      setup_requires=["setuptools_scm"],
      install_requires=["certifi"],
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
