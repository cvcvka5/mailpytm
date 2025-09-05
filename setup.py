from setuptools import setup, find_packages

setup(
    name="mailpytm",
    version="1.1.0",
    author="Ulus Vatansever",
    author_email="ulusvatansever@gmail.com",
    description="A Python client for the mail.tm temporary email service API",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cvcvka5/mailpytm",
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        "requests>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
)
