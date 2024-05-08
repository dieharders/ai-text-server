import os
import uuid
from datetime import datetime, timezone
from typing import List, Tuple
from llama_index.core import Document
from llama_index.core.schema import IndexNode, TextNode
from core import common


# Chunks are created from each document and will inherit their metadata
def chunks_from_documents(
    documents: List[Document], parsed_nodes: List[TextNode], source_record: dict
) -> Tuple[List[str], List[IndexNode]]:
    chunk_nodes = []
    chunks_ids = []

    for doc in documents:
        source_id = source_record.get("id")
        # Set metadata on each chunk node
        for chunk_ind, parsed_node in enumerate(parsed_nodes):
            # Create metadata for chunk
            chunk_metadata = dict(
                sourceId=source_id,
                order=chunk_ind,
                # description="", # @TODO Ai generate based on chunk's text content
                # tags="", # @TODO Ai generate based on chunk's description
                # name="", # @TODO Ai generate based on chunk's text description above
            )
            # Set metadatas
            excluded_llm_metadata_keys = doc.excluded_llm_metadata_keys
            excluded_llm_metadata_keys.append("order")
            excluded_embed_metadata_keys = doc.excluded_embed_metadata_keys
            excluded_embed_metadata_keys.append("order")
            # Create chunk
            chunk_node = IndexNode(
                id_=f"{source_id}--{uuid.uuid4()}",  # Optional, ID will be base + parent
                text=parsed_node.text or "None",
                index_id=str(source_id),
                metadata=chunk_metadata,
            )
            # Tell query engine to ignore these metadata keys
            chunk_node.excluded_llm_metadata_keys = excluded_llm_metadata_keys
            chunk_node.excluded_embed_metadata_keys = excluded_embed_metadata_keys
            # Once your metadata is converted into a string using metadata_seperator
            # and metadata_template, the metadata_templates controls what that metadata
            # looks like when joined with the text content
            chunk_node.metadata_seperator = "::"
            chunk_node.metadata_template = "{key}=>{value}"
            chunk_node.text_template = (
                "Metadata: {metadata_str}\n-----\nContent: {content}"
            )
            # Return chunk `IndexNode`
            chunk_nodes.append(chunk_node)
            chunks_ids.append(chunk_node.node_id)  # or id_
    print(f"{common.PRNT_EMBED} Added {len(chunk_nodes)} chunks to collection")
    return [chunks_ids, chunk_nodes]


# Create a document record for a Collection to track
# @TODO Perhaps we can do the same with a `docstore` ?
def create_source_record(document: Document) -> dict:
    metadata = document.metadata
    file_name = metadata.get("fileName") or ""
    extension = os.path.splitext(file_name)[1]
    file_type = extension[1:] or ""  # Remove the dot from the extension
    name = metadata.get("name") or ""
    description = (
        metadata.get("description") or ""
    )  # "Summarization of source contents."
    tags = metadata.get("tags") or ""
    checksum = metadata.get("checksum") or ""
    file_path = metadata.get("filePath") or ""
    file_size = metadata.get("fileSize") or 0
    total_pages = metadata.get("total_pages")
    created_at = datetime.now(timezone.utc).strftime("%B %d %Y - %H:%M:%S") or ""
    modified_last = (
        metadata.get("last_modified_date") or metadata.get("modifiedLast") or ""
    )
    # Create an object to store metadata
    source_record = dict(
        id=document.id_,
        checksum=checksum,  # the hash of the parsed file
        fileType=file_type,  # type of the source (ingested) file
        filePath=file_path,  # path to parsed file
        fileName=file_name,  # name of parsed file
        fileSize=file_size,  # bytes
        name=name,  # document name
        description=description,
        tags=tags,
        createdAt=created_at,
        modifiedLast=modified_last,
        chunkIds=[],  # filled in after chunks created
    )
    if total_pages:
        source_record.update(totalPages=total_pages)
    # Return result
    print(f"{common.PRNT_EMBED} Created document record:\n{source_record}", flush=True)
    return source_record
