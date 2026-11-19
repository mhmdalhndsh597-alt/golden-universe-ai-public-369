from setuptools import find_packages, setup


setup(
    name="golden-universe-ai",
    version="1.0.0",
    description="Python SDK for the Golden Universe AI Center",
    packages=find_packages(),
    install_requires=["httpx>=0.27.0"],
    python_requires=">=3.10",
)
