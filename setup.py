"""Setup script for ion_transport package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []

if requirements_file.exists():
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Skip virtual_lab since it needs special handling
                if "virtual_lab" not in line:
                    requirements.append(line)

setup(
    name="ion_transport",
    version="0.4.0",
    description="Multi-Agent Virtual Lab for Ion Transport Research",
    author="Ion Transport Research Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
