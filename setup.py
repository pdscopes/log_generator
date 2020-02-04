from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='log_generator',
      version='1.0.2',
      description='Generates dummy logs based on configuration files',
      long_description=readme(),
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Operating System :: OS Independent',
      ],
      author='Peter Scopes',
      author_email='peter.scopes@nccgroup.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'PyYAML>=5.1.1',
          'jsonschema>=3.0.0',
      ],
      entry_points={
          'console_scripts': ['log-generator=log_generator.generate:main']
      },
      include_package_data=True,
      platforms='any',
      zip_safe=False)
