from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='log_generator',
      version='1.0.0',
      description='Generates dummy logs based on configuration files',
      long_description=readme(),
      classifiers=[
          'Programming Language :: Python :: 3.7',
          'Operating System :: OS Independent',
      ],
      author='Peter Scopes',
      author_email='peter.scopes@nccgroup.trust',
      license='Copyright 2018 NCC',
      packages=find_packages(),
      install_requires=[
          'PyYAML>=3.12',
          'jsonschema>=3.0.0',
      ],
      entry_points={
          'console_scripts': ['log_generator=log_generator.generator:main']
      },
      include_package_data=True,
      zip_safe=False)
