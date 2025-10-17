"""Setup script for Audiobook Generator"""
from setuptools import setup, find_packages

setup(
    name="audiobook-generator",
    version="0.1.0",
    description="Convert PDF books to audiobooks using AI",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.2.0",
        "langchain>=0.3.0",
        "edge-tts>=7.2.0",
        "pyttsx3>=2.90",
        "pypdf2>=3.0.0",
        "ebooklib>=0.18",
        "typer>=0.12.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "audiobook-gen=cli.main:app",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
