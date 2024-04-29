import os
import glob
import shutil
import uuid
from typing import Any, List, Optional
import hashlib
from server import common
from fastapi import UploadFile
from llama_index.core import Document

MEMORY_FOLDER = "memories"
TMP_FOLDER = "tmp"
TMP_DOCUMENT_PATH = common.app_path(os.path.join(MEMORY_FOLDER, TMP_FOLDER))
PARSED_FOLDER = "parsed"
PARSED_DOCUMENT_PATH = common.app_path(os.path.join(MEMORY_FOLDER, PARSED_FOLDER))

# @TODO Add funcs to convert any original file's contents to text format and save to .md file.


def create_checksum(file_path: str):
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    digest = sha1.hexdigest()
    print(f"{common.PRNT_EMBED} SHA1: {digest}", flush=True)
    return digest


def create_file_name(id: str, input_file_name: str):
    file_extension = input_file_name.rsplit(".", 1)[1]
    file_name = f"{id}.{file_extension}"
    return file_name


# Create a filename for a parsed markdown document
def create_parsed_id(collection_name: str, document_name: str):
    # @TODO If we ever submit multiple files for the same source, make sure chunks have unique ids.
    doc_name = document_name or str(uuid.uuid4()).replace("-", "")
    # return f"{collection_name}--{doc_name}"
    return doc_name


def check_file_support(filePath: str):
    # Check supported file types
    input_file_path = filePath
    file_extension = input_file_path.rsplit(".", 1)[1]
    supported_ext = (
        "txt",
        "md",
        "mdx",
        "doc",
        "docx",
        "pdf",
        "rtf",
        "csv",
        "json",
        "xml",
        "xls",
        "html",
        # "orc",
    )
    is_supported = file_extension.lower().endswith(supported_ext)
    print(f"{common.PRNT_EMBED} Check extension: {file_extension}", flush=True)

    return is_supported


# @TODO Define a dynamic document parser to convert basic text contents to markdown format
def process_documents(input_documents: List[Document]):
    try:
        # Parsed document contents
        # @TODO Copied text should be parsed and edited to include markdown syntax to describe important bits (headings, attribution, links)
        # @TODO Copied contents may include things like images/graphs that need special parsing to generate an effective text description
        # @TODO Generate name, descr, tags if not present based on parsed text content ...
        # @TODO Save the file to disk as a .md
        print(
            f"{common.PRNT_EMBED} Successfully processed {input_documents}", flush=True
        )
    except (Exception, ValueError, TypeError, KeyError) as error:
        print(f"{common.PRNT_EMBED} Document processing failed: {error}", flush=True)


async def copy_file_to_disk(
    app: Any,
    url_path: str,  # web, could be a file or html
    text_input: str,  # text from client
    file: UploadFile,  # file from client
    id: str,
    file_path: Optional[str] = "",  # local path on server
) -> dict:
    try:
        file_name = ""
        tmp_input_file_path = ""
        tmp_folder = TMP_DOCUMENT_PATH
        # Save temp files to disk first
        if url_path:
            print(
                f"{common.PRNT_API} Downloading file from url {url_path} to {tmp_input_file_path}"
            )
            if not check_file_support(url_path):
                raise Exception("Unsupported file format.")
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            # Download the file and save to disk
            file_name = create_file_name(id=id, input_file_name=url_path)
            tmp_input_file_path = os.path.join(tmp_folder, file_name)
            await common.get_file_from_url(url_path, tmp_input_file_path, app)
        elif text_input:
            print(f"{common.PRNT_API} Saving raw text to file...\n{text_input}")
            # @TODO Do input sanitation here...
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            # Write to file
            file_name = create_file_name(id=id, input_file_name="content.txt")
            tmp_input_file_path = os.path.join(tmp_folder, file_name)
            with open(tmp_input_file_path, "w") as f:
                f.write(text_input)
        elif file_path:
            # Read file from local path
            print(f"{common.PRNT_API} Reading local file from disk...{file_path}")
            if not os.path.exists(file_path):
                raise Exception("File does not exist.")
            if not check_file_support(file_path):
                raise Exception("Unsupported file format.")
            # Copy the file to the destination folder
            file_name = create_file_name(id=id, input_file_name=file_path)
            tmp_input_file_path = os.path.join(tmp_folder, file_name)
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            shutil.copyfile(file_path, tmp_input_file_path)
        elif file:
            print(f"{common.PRNT_API} Saving uploaded file to disk...")
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            if not check_file_support(file.filename):
                raise Exception("Unsupported file format.")
            # Read the uploaded file in chunks of 1mb
            file_name = create_file_name(id=id, input_file_name=file.filename)
            tmp_input_file_path = os.path.join(tmp_folder, file_name)
            with open(tmp_input_file_path, "wb") as f:
                while contents := file.file.read(1024 * 1024):
                    f.write(contents)
            file.file.close()
        else:
            raise Exception("Please supply a file path or url.")
        return {
            "document_id": file_name,
            "file_name": file_name,
            "path_to_file": tmp_input_file_path,
            "checksum": create_checksum(tmp_input_file_path),
        }
    except Exception as err:
        print(f"{common.PRNT_EMBED} Failed to copy to disk: {err}")


# Wipe all parsed files
def delete_all_files():
    if os.path.exists(TMP_DOCUMENT_PATH):
        files = glob.glob(f"{TMP_DOCUMENT_PATH}/*")
        for f in files:
            os.remove(f)  # del files
        os.rmdir(TMP_DOCUMENT_PATH)  # del folder
    if os.path.exists(PARSED_DOCUMENT_PATH):
        files = glob.glob(f"{PARSED_DOCUMENT_PATH}/*.md")
        for f in files:
            os.remove(f)  # del all .md files
        os.rmdir(PARSED_DOCUMENT_PATH)  # del folder
