
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE.md') as f:
    license = f.read()

setup(
    name='jenkinsreviewbot',
    version='0.1.0',
    description='Jenkins reviewboard review bot',
    long_description=readme,
    author='Neil.Potter',
    license=license,
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'docs')),
    py_modules=['jrbb_service'],
    install_requires=['bottle',
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
        ]
    }

    )
