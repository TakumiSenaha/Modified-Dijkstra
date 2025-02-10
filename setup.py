# This file is Sample setup.py file for a Python project.

from setuptools import find_packages, setup

setup(
    name="modified_dijkstra",
    version="1.0.0",
    description="An implementation of Modified Dijkstra Algorithm for finding the maximum load path.",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/modified-dijkstra",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "networkx",
        "matplotlib",
        "pytest",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
