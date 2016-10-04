from setuptools import find_packages, setup


setup(
    name='conntest',
    version='1.2.1',
    license='GPL3',
    description='Try to connect to a host via SSH/RDP/VNC/VMware vCenter auth etc',
    long_description=open('README.rst').read(),
    author='Philipp Schmitt',
    author_email='philipp@schmitt.co',
    url='https://github.com/pschmitt/conntest',
    packages=find_packages(),
    install_requires=['paramiko', 'rdpy', 'shortmomi', 'opsview'],
    entry_points={
        'console_scripts': ['conntest=conntest.conntest:main']
    }
)
