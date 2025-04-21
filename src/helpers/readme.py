from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter

def split_readme_to_chunks(doc_path, chunk_size=500, chunk_overlap=50):
    with open(doc_path, "r", encoding="utf-8") as f:
        readme_text = f.read()
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(readme_text)
    return chunks