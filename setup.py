import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="emu-power",
    version="1.4",
    author="Steven Bertolucci",
    author_email="srbertol@mtu.edu",
    description="A Python3 API to interface with Rainforest Automation's EMU-2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Steve0320/Emu-Api",
    packages=setuptools.find_packages(),
    install_requires=[
        'pyserial'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6'
)
