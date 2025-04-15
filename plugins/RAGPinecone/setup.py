from setuptools import setup, find_packages

setup(
    name="rag-pinecone-gamesdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pinecone-client>=2.2.1",
        "langchain>=0.0.267",
        "langchain-community>=0.0.1",
        "langchain-pinecone>=0.0.1",
        "langchain-openai>=0.0.2",
        "openai>=1.1.1",
        "python-dotenv>=1.0.0",
        "unstructured>=0.10.0",
        "pdf2image>=1.16.3",
        "pytesseract>=0.3.10",
        "docx2txt>=0.8",
        "pandas>=2.0.0",
        "beautifulsoup4>=4.12.0",
        "markdown>=3.4.3",
        "rank_bm25>=0.2.2",
        "spacy>=3.0.0",
        "gdown",
    ],
    python_requires=">=3.9",
) 


#python -m spacy download en_core_web_sm
