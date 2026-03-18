from setuptools import setup, find_packages

setup(
    name="rlforge",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "numpy>=1.24.0",
        "gymnasium>=0.29.0",
    ],
    python_requires=">=3.8",
    description="Python SDK for the RLForge RL Environment Platform",
    author="Kualia AI",
    url="https://rlforge.ai",
)
