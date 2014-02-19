from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
        name='ckanext-ceres',
        version=version,
        description="Ceres extension adding additional fields and controls",
        long_description="""\
        """,
        classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        keywords='',
        author='Justin Merz',
        author_email='jrmerz@gmail.com',
        url='http://ceres.ca.gov',
        license='',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        namespace_packages=['ckanext', 'ckanext.ceres'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
                # -*- Extra requirements: -*-
        ],
        entry_points=\
        """
        [ckan.plugins]
        # Add plugins here, eg
        ceres_plugin=ckanext.ceres.plugin:CeresPlugin
        esri_harvester=ckanext.ceres.harvesters:ESRIHarvester
        """,
)
