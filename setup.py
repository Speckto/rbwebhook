"""
Jenkins Reviewboard Bot (jrbb)
"""
from setuptools import setup, find_packages


def readfile(filename):
    """
    Reads and returns file contents
    """
    with open(filename) as docfile:
        return docfile.read()


setup(
    name='jenkinsreviewbot',
    version='0.1.0',
    description='Jenkins reviewboard review bot',
    long_description=readfile('README.md'),
    author='Neil.Potter',
    license=readfile('LICENSE.md'),
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'docs')),
    py_modules=['jrbb.jrbb_service'],
    install_requires=[
        'waitress',
        'bottle',
        'certifi',
        'chardet',
        'idna',
        'itsdangerous',
        'multi-key-dict',
        'p4python',
        'pbr',
        'python-jenkins',
        'RBTools',
        'requests',
        'six',
        'tqdm',
        'urllib3',
    ],
    entry_points={
        'console_scripts': [
            'jrbb_service=jrbb.jrbb_service:main',
            'jrbb_fetchpatch=jrbb.jrbb_fetchpatch:main',
            'jrbb_postbuildresults=jrbb.jrbb_postbuildresults:main',
            'jrbb_simulaterbcallback=jrbb.jrbb_simulaterbcallback:main',
        ]
    },
    scripts=['bin/jrbb_runitwithvenv.sh'],
    )
