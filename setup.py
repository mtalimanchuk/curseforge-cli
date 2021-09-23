# -*- coding: utf-8 -*-
"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

install_requires = ['pydantic>=1.8.2,<2.0.0', 'requests>=2.26.0,<3.0.0', 'setuptools==58.0.4']

entry_points = {
    'console_scripts': ['curseforge-cli=curseforge_cli.cli:run_cli'],
}

setup_kwargs = {
    'name': 'curseforge-cli',
    'version': '0.1.1',
    'description': 'Command line addon manager for World of Warcraft, TES: Online, Minecraft and more',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'author': 'Maxim Talimanchuk',
    'author_email': 'mtalimanchuk@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/mtalimanchuk/curseforge-cli',
    'packages': find_packages(),
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4',
    'entry_points': entry_points,
}


setup(**setup_kwargs)
