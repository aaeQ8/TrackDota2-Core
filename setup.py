from setuptools import setup, find_packages

setup(
    name="trackdota2",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "youtube-dl >= 2021.6.6",
        "boto3>=1.18.63",
        "opencv_python>=4.5.3.56",
        "numpy>=1.21.2",
        "requests>=2.22.0",
        "beautifulsoup4>=4.10.0",
        "matplotlib>=3.4.3",
        "Pillow>=8.4.0",
        "scikit_learn>=1.0",
    ],
)
