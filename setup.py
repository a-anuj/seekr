from setuptools import setup

setup(
    name="seekr",
    version="0.1",
    py_modules=[],  # not using single-file modules
    packages=["cli", "core"],   # 👈 IMPORTANT
    entry_points={
        "console_scripts": [
            "seekr=cli.main:main"   # 👈 NO seekr prefix
        ]
    },
)