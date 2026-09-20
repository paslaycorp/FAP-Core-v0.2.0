from setuptools import find_packages, setup

setup(
    name="fap-core",
    version="0.2.0",
    description="Fraud-Authenticity Provenance Engine",
    author="Patrick Paslay",
    packages=find_packages(),
    install_requires=["requests==2.31.0"],
    python_requires=">=3.12,<3.14",
)
