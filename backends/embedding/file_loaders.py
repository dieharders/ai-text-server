from typing import List
from llama_index.core import SimpleDirectoryReader, Document


def documents_from_sources(
    sources: List[str], source_id, source_metadata: dict
) -> List[Document]:
    documents = []
    reader = SimpleDirectoryReader(input_files=sources)
    # Process each files nodes as they load
    for loaded_nodes in reader.iter_data():
        # Build a document from loaded file (reader splits into text nodes)
        document_node = loaded_nodes[0]
        doc_text = [d.get_content() for d in loaded_nodes]
        # Create metadata
        chunk_metadata = {
            **document_node.metadata,
            "sourceId": source_id,
        }
        # Create source document
        source_doc = Document(
            id_=source_id,
            text="".join(doc_text),
            metadata=chunk_metadata,
        )
        # Tell query engine to ignore these metadata keys
        source_doc.excluded_llm_metadata_keys.append("sourceId")
        source_doc.excluded_embed_metadata_keys.append("sourceId")
        # Insert user submitted metadata into document
        source_doc.metadata.update(source_metadata)
        source_doc.excluded_llm_metadata_keys.extend(source_metadata)
        source_doc.excluded_embed_metadata_keys.extend(source_metadata)
        # Return source `Document`
        documents.append(source_doc)
    # Return a list of Documents
    return documents
