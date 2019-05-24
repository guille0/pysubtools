import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pysubtools',
    version='0.1',
    author="Guillermo Vicente",
    author_email="guillermovicente@protonmail.com",
    description="A library for editing subtitle files.",
    keywords='subtitles ass srt',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guille0/pysubtools",
    packages=['pysubtools'],
    zip_safe=False,
    install_requires=[
        'matplotlib',
        'pillow',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Video",
    ],

 )