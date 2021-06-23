from setuptools import setup

# # The directory containing this file
# HERE = pathlib.Path(__file__).parent

# # The text of the README file
# README = (HERE / "README.md").read_text()

with open('README.md','r') as fh:
    long_description = fh.read()

# This call to setup() does all the work
setup(
    name="SpacePyTraders",
    version="0.0.5",
    description="Access the Space Traders API with Python",
    # long_description=README,
    # long_description_content_type="text/markdown",
    url="https://github.com/ZacHooper/spacePyTraders",
    author="Zac Hooper",
    author_email="zac.g.hooper@gmail.com",
    py_modules=["client"],
    packages=["SpacePyTraders"],
    install_requires=[
        "requests ~= 2.25.1"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown"
)
