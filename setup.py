from setuptools import setup, find_packages
setup(name="fap-core", version="0.2.0", description="Fraud-Authenticity Provenance Engine", author="Patrick Paslayat", packages=find_packages(), install_requires=["requests>=2.31.0", "pytest>=8.0.0"], python_requires=">=3.9")
