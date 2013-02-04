from setuptools import setup

setup(
    name='netscramble',
    version='0.1',
    description='Simple logic puzzle game',
    url='http://tomdryer.com',
    author='Tom Dryer',
    author_email='tomdryer.com@gmail.com',
    license='BSD',
    packages=['netscramble'],
    entry_points= {
        "console_scripts": ["netscramble=netscramble.gui:main"],
    },
    include_package_data = True,
    zip_safe=False
)
