import os
from typing import List
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.readers.file import PyMuPDFReader

###########
# METHODS #
###########


def create_source_document(text: str, source_id: str, metadata: dict, embedder: str):
    # Create metadata
    document_metadata = {
        **metadata,
        "sourceId": source_id,  # track this document
        "embedder": embedder,  # track which model embedded
    }
    # Create source document
    source_doc = Document(
        id_=source_id,
        text=text,
        metadata=document_metadata,
    )
    return source_doc


def set_ignored_metadata(source_document: Document, ignore_metadata: dict):
    # Tell query engine to ignore these metadata keys
    source_document.excluded_llm_metadata_keys.append("sourceId", "embedder")
    source_document.excluded_embed_metadata_keys.append("sourceId", "embedder")
    # Insert user submitted metadata into document
    source_document.metadata.update(ignore_metadata)
    source_document.excluded_llm_metadata_keys.extend(ignore_metadata)
    source_document.excluded_embed_metadata_keys.extend(ignore_metadata)
    return source_document


###########
# LOADERS #
###########


def simple_file_loader(sources: List[str], source_id, source_metadata: dict):
    documents = []
    reader = SimpleDirectoryReader(input_files=sources)
    # Process each files nodes as they load
    for loaded_nodes in reader.iter_data():
        # Build a document from loaded file
        # Reader splits into text nodes which we use to rebuild text content
        document_node = loaded_nodes[0]
        doc_text = [d.get_content() for d in loaded_nodes]
        # Create document node
        source_doc = create_source_document(
            text="".join(doc_text), source_id=source_id, metadata=document_node.metadata
        )
        # Set ignored metadata
        source_doc = set_ignored_metadata(
            source_document=source_doc, ignore_metadata=source_metadata
        )
        # Return source `Document`
        documents.append(source_doc)
    return documents


def pdf_loader(path: str, source_id: str, source_metadata: dict, make_metadata=True):
    reader = PyMuPDFReader()
    documents = reader.load_data(
        file_path=path, metadata=make_metadata, extra_info=source_metadata
    )
    print(f"pdf::{documents}")
    # Process document
    document_results = []
    for document in documents:
        doc_text = [d.get_content() for d in documents]
        # Create document node
        source_doc = create_source_document(
            text="".join(doc_text), source_id=source_id, metadata=document.metadata
        )
        # Set ignored metadata
        source_doc = set_ignored_metadata(
            source_document=source_doc, ignore_metadata=source_metadata
        )
        document_results.append(source_doc)
    return documents


# Read in source file(s) and build a document node with metadata.
# We will use this to base our chunks on.
def documents_from_sources(
    sources: List[str], source_id, source_metadata: dict
) -> List[Document]:
    documents = []
    for source in sources:
        filename = os.path.basename(source)
        file_extension = filename.split(".")[-1]
        print(f"file_extension::{file_extension}")
        # Use loader solution based on file type
        match file_extension:
            case ".md":
                pass
            case ".txt":
                # If text file
                documents = simple_file_loader(
                    sources=[source],
                    source_id=source_id,
                    source_metadata=source_metadata,
                )
            case ".pdf":
                # If PDF
                documents = pdf_loader(
                    path=source, source_id=source_id, source_metadata=source_metadata
                )
            case _:
                # default
                raise Exception("The supplied file is not currently supported.")
    # Return list of Documents
    return documents
