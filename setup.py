from setuptools import setup, find_packages
setup(
    name='milesight_to_bacnet',
    sdk_version='1.1.14',
    version='0.0.5',
    author='rbs',
    author_email='',
    description='Read milesight sensor mqtt published data to BACnet',
    license='',
    packages = find_packages('src'),
    package_dir={ '' : 'src'},
    zip_safe=False,
    install_requires=[
        'bacpypes'
    ],
    entry_points = """
        [console_scripts]
        milesight_to_bacnet = Application:main
        """
)