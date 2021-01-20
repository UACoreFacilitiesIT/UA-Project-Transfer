import os
from setuptools import setup, find_packages


def readme(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with open(full_path, 'r') as file:
        return file.read()


setup(
    name="ua_project_transfer",
    version="1.1.8",
    author="Stephen Stern, Rafael Lopez, Etienne Thompson",
    author_email="sterns1@email.arizona.edu",
    packages=find_packages(),
    include_package_data=True,
    long_description=readme("README.md"),
    long_description_content_type='text/markdown',
    url="https://github.com/UACoreFacilitiesIT/UA-Project-Transfer",
    license="MIT",
    description=(
        "Converts iLab service requests to Illumina Clarity Projects."),
    install_requires=[
        "bs4",
        "lxml",
        "requests",
        "ua-stache-api",
        "ua-clarity-tools",
        "ua-ilab-tools",
    ],
)
