import os
import glob
import shutil
from typing import Any, Optional
import uuid
import hashlib
import re
from server import common
from fastapi import UploadFile

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


# Create a filename for a parsed document memory
def create_parsed_filename(collection_name: str, document_name: str):
    # @TODO If we ever submit multiple files for the same source, append a file number.
    # @TODO Actually why do we even need to keep around the parsed file after embedding?
    return f"{document_name}.md"


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
        "orc",
    )
    is_supported = file_extension.lower().endswith(supported_ext)
    print(f"{common.PRNT_EMBED} Check extension: {file_extension}", flush=True)

    return is_supported


def pre_process_documents(
    document_name: str,
    collection_name: str,
    description: str,
    tags: str,
    input_file_path: str,
    document_id: str = "",  # supplied if document already exists
):
    try:
        if not document_name or not collection_name:
            raise Exception("You must supply a collection and memory name.")
        if not os.path.exists(input_file_path):
            raise Exception("File does not exist.")
        if not check_file_support(input_file_path):
            raise Exception("Unsupported file format.")
    except (Exception, ValueError, TypeError, KeyError) as error:
        print(f"{common.PRNT_EMBED} Pre-processing failed: {error}", flush=True)
        raise Exception(error)
    else:
        # Read the supplied id or assign a new one
        source_id = document_id or str(uuid.uuid4()).replace("-", "")
        new_filename = create_parsed_filename(collection_name, source_id)
        # Create output folder for parsed file
        out_path = PARSED_DOCUMENT_PATH
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        target_output_path = os.path.join(out_path, new_filename)
        # Format tags for inclusion in document
        comma_sep_tags = re.sub("\\s+", ", ", tags.strip())
        # Finalize parsed file
        # @TODO If the file is not text, then create a text description of the contents (via VisionAi, Human, OCR)
        # Copy text contents of original file into a new file, parsed for embedding
        with open(target_output_path, "w", encoding="utf-8") as output_file, open(
            input_file_path, "r", encoding="utf-8"
        ) as input_file:
            # Check if header exists
            first_line = input_file.readline()
            if first_line != "---\n":
                # Add a header to file
                output_file.write("---\n")
                output_file.write(f"collection: {collection_name}\n")
                output_file.write(f"document: {document_name}\n")
                output_file.write(f"description: {description}\n")
                output_file.write(f"tags: {comma_sep_tags}\n")
                output_file.write("---\n\n")
            input_file.seek(0)  # set back to start of file
            # Copy each line from source file
            output_file.writelines(line for line in input_file)
            # @TODO Copied text should be parsed and edited to include markdown syntax to describe important bits (headings, attribution, links)
            # @TODO Copied contents may include things like images/graphs that need special parsing to generate an effective text description
            # parsed_text = markdown.parse(copied_text)
        # Create a checksum for validation later
        checksum = create_checksum(target_output_path)
    finally:
        # Delete uploaded file
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
            print(f"{common.PRNT_EMBED} Removed temp file upload.", flush=True)
        else:
            print(
                f"{common.PRNT_EMBED} Failed to delete temp file upload. The file does not exist.",
                flush=True,
            )

    print(
        f"{common.PRNT_EMBED} Successfully processed {target_output_path}", flush=True
    )
    return {
        "document_id": source_id,
        "file_name": new_filename,
        "path_to_file": target_output_path,
        "checksum": checksum,
    }


async def process_file_to_disk(
    app: Any,
    url_path: str,
    text_input: str,
    file: UploadFile,
    file_name: str,
    file_path: Optional[str] = "",  # local path on server
):
    # Save temp files to disk first. The filename doesnt matter much.
    tmp_folder = TMP_DOCUMENT_PATH
    tmp_input_file_path = os.path.join(tmp_folder, file_name)
    # Process file and write to disk
    if url_path:
        print(
            f"{common.PRNT_API} Downloading file from url {url_path} to {tmp_input_file_path}"
        )
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        # Download the file and save to disk
        await common.get_file_from_url(url_path, tmp_input_file_path, app)
    elif text_input:
        print(f"{common.PRNT_API} Saving raw text to file...\n{text_input}")
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        # Write to file
        with open(tmp_input_file_path, "w") as f:
            f.write(text_input)
    elif file_path:
        # Read file from local path
        print(f"{common.PRNT_API} Reading local file from disk...{file_path}")
        # Copy the file to the destination folder
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        shutil.copyfile(file_path, tmp_input_file_path)
    elif file:
        print(f"{common.PRNT_API} Saving uploaded file to disk...")
        # Read the uploaded file in chunks of 1mb,
        # store to a tmp dir for processing later
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        with open(tmp_input_file_path, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
        file.file.close()
    else:
        raise Exception("Please supply a file path or url.")
    return


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
