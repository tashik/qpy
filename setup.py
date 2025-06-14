from setuptools import setup, find_packages

setup(
    name="qpy-bridge",
    version="0.1.0",
    description="A Python client for QLUA socket bridge",
    author="Natalya Andriets, aka tashik",
    author_email="patrinat@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.8",
)
