"""PyCloudSim setup script."""

from setuptools import setup, find_packages

setup(
    name="pycloudsim",
    version="1.0.0",
    author="PyCloudSim Contributors",
    description="Python-native cloud computing simulation framework inspired by Java CloudSim",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests*", "experiments*"]),
    install_requires=[
        "rich>=13.0.0",
        "matplotlib>=3.7.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
    ],
)
