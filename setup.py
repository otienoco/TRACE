from setuptools import setup, find_packages

setup(
    name="trace-repurposing",
    version="1.0.0",
    description="TRACE: TWAS-driven Repurposing through AI-assisted Curation of Evidence",
    author="Christopher O. Otieno",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.40.0",
        "huggingface_hub>=0.19.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
        "scikit-learn>=1.3.0",
        "safetensors>=0.4.0",
        "tokenizers>=0.19.0",
        "tqdm>=4.65.0",
        "PyYAML>=6.0",
    ],
)
