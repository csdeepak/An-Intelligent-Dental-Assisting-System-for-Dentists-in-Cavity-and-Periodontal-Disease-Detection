from setuptools import setup, find_packages

setup(
    name="dental-ai-pipeline",
    version="0.1.0",
    description="Automated OPG Analysis — Caries & Bone Loss Detection",
    author="Deepak",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "matplotlib>=3.7.0",
        "PyYAML>=6.0",
        "tqdm>=4.65.0",
    ],
)
