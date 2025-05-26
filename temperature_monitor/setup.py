from setuptools import setup, find_packages

with open("backend/requirements.txt", "r") as f:
    backend_requirements = [line.strip() for line in f.readlines() if line.strip()]
with open("frontend/requirements.txt", "r") as f:
    frontend_requirements = [line.strip() for line in f.readlines() if line.strip()]
all_requirements = backend_requirements + [req for req in frontend_requirements if req not in backend_requirements]

setup(
    name="temperature_monitor",
    version="0.1.0",  # This will be managed by the version updater
    description="Temperature monitoring application",
    author="rafaldem",
    author_email="<162693211+rafaldem@users.noreply.github.com>",
    packages=find_packages(include=["backend", "frontend", "scripts"]),
    install_requires=all_requirements,
    entry_points={
        "console_scripts": [
            "update-version=scripts.version_updater.update_version:main",
        ],
    },
    python_requires=">=3.7",  # Updated to match frontend requirement
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
        ]
    },
)
