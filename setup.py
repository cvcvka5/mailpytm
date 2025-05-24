from setuptools import setup, find_packages

setup(
    name="mailpytm",                     # Your package name on PyPI
    version="1.0.0",                   # Initial version
    author="cvcvka5",
    author_email="cvcvka5@gmail.com",
    description="A Python client for the mail.tm temporary email service API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cvcvka5/mailpytm",  # Replace with your repo URL
    packages=find_packages(),          # Finds mailtm and any other packages
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
