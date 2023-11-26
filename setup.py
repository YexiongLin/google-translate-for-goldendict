#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: YEXIONG LIN'
# Created on 2022-10-30 12:59:00

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="google-translate-for-goldendict",
    version="1.4.1",
    author="Yexiong Lin",
    author_email="yexiong_lin@hnu.edu.cn",
    description="Add Google translate to GoldenDict",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YexiongLin/google-translate-for-goldendict",
    packages=setuptools.find_packages(),
    install_requires=['requests'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
