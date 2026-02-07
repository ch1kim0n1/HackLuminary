from setuptools import setup, find_packages

setup(
    name="hackluminary",
    version="1.0.0",
    description="CLI-first, local-only tool for generating hackathon presentations",
    author="MindCore",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0,<9",
        "Jinja2>=3.0.0,<4",
        "Markdown>=3.3.0,<4",
    ],
    entry_points={
        "console_scripts": [
            "hackluminary=hackluminary.cli:main",
        ],
    },
    python_requires=">=3.8",
)
