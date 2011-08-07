##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

from setuptools import setup
from setuptools import find_packages
import os.path

version = open(os.path.join("Products","LongRequestLogger",
                            "version.txt")).read().strip()
description = "Dumps sequential stack traces of long-running Zope2 requests"

setup(name='Products.LongRequestLogger',
      version=version,
      description=description,
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Zope2",
        "Intended Audience :: System Administrators",
        ],
      keywords='performance zope2 plone erp5',
      author='Nexedi SA',
      author_email='erp5-dev@erp5.org',
      url='http://www.erp5.com/',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      extras_require=dict(
           # With Python versions < 2.5, we need the threadframe module 
           python24=['threadframe'],
           # we need to work with Zope 2.8 buildouts that might not provide a 
           # Zope2 egg (fake or otherwise). So we declare the full dependency
           # here.
           standalone=['Zope2'],
      ),
)
