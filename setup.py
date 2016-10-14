# See license.txt for license details.
# Copyright (c) 2016 Chris Withers

import os

from setuptools import setup, find_packages

base_dir = os.path.dirname(__file__)

setup(
    name='shoehorn',
    version='0.1.3',
    author='Chris Withers',
    author_email='chris@withers.org',
    license='MIT',
    description="Shoehorn structured logs into or out of standard library logging",
    # long_description=open('docs/description.rst').read(),
    # url='https://github.com/cjw296/chide',
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude='tests'),
    zip_safe=False,
    include_package_data=True,
    extras_require=dict(
        test=[
            'coveralls',
            'manuel',
            'nose',
            'nose-cov',
            'nose-fixes',
            'testfixtures',
            ],
        build=['sphinx', 'pkginfo', 'setuptools-git', 'twine', 'wheel']
    ),
)
