from setuptools import setup, find_packages

with open("README.adoc", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="adoc-link-checker",  # Nom cohérent avec le README
    version="0.1.0",           # Version harmonisée
    author="dhrions",
    description="Un outil en ligne de commande pour vérifier les liens brisés dans les fichiers AsciiDoc.",
    long_description=long_description,
    long_description_content_type="text/asciidoc",
    url="https://github.com/dhrons/utils",
    packages=find_packages(),
    install_requires=[
        "certifi==2025.8.3",
        "charset-normalizer==3.4.3",
        "click==8.2.1",
        "idna==3.10",
        "requests==2.32.5",
        "urllib3==2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "adoc-link-checker=adoc-link-checker.cli:cli",  # Nom cohérent
        ],
    },
    python_requires=">=3.8",
    license="MIT",  # À adapter selon ta licence
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Text Processing :: Markup :: AsciiDoc",
    ],
    keywords="asciidoc link checker broken links",
    project_urls={
        "Bug Tracker": "https://github.com/dhrons/utils/issues",
        "Source Code": "https://github.com/dhrons/utils",
    },
)
