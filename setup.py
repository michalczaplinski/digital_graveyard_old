from setuptools import setup

setup(name='digital_graveyard',
      version='1.0',
      description='where tweets go to die',
      author='Michal Czaplinski',
      author_email='mmczaplinski@gmail.com',
      url='http://www.python.org/sigs/distutils-sig/',
      install_requires=['Flask>=0.9','flask-wtf','flask-babel','markdown','flup','MarkupSafe'. 'TwitterAPI'],
     )
