import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objettoqt",
    version="0.3.1",
    author="Bruno Nicko",
    author_email="brunonicko@gmail.com",
    description="Utilities to use Objetto with Qt",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/brunonicko/objettoqt",
    packages=setuptools.find_packages(),
    install_requires=[
        "enum34; python_version < '3.4'",
        "pyrsistent",
        "qualname",
        "six",
        "slotted",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    python_requires=">=2.7",
)
