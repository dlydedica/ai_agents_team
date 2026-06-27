from setuptools import setup, find_packages

setup(
    name="ai-devcorp",
    version="1.0.0",
    description="AI DevCorp — корпорация AI-агентов для ваших проектов",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="AI DevCorp Team",
    url="https://github.com/dlydedica/ai_agents_team",
    packages=find_packages(),
    py_modules=["team"],
    python_requires=">=3.11",
    install_requires=[
        "mcp>=1.0.0",
        "portalocker>=2.0.0",
    ],
    extras_require={
        "dashboard": ["fastapi>=0.100.0", "uvicorn>=0.20.0", "jinja2>=3.0.0"],
        "dev": ["pytest", "flake8", "black", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "ai-devcorp=team:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: AI",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
)
