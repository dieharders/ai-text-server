import re
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import (
    LangchainNodeParser,
    MarkdownNodeParser,
    SentenceSplitter,
)

# from langchain.text_splitter import (
#     CharacterTextSplitter,
#     RecursiveCharacterTextSplitter,
#     Language,
# )
# import io
# import base64
# from PIL import Image  # use `pip install pillow` instead of PIL

# Unstructured lib helps make your data LLM ready - unstructured.io
# from unstructured.partition.pdf import partition_pdf
# from unstructured.staging.base import elements_to_json

OUTPUT_PDF_IMAGES_PATH = "memories/parsed/pdfImages/"


# Helpers


def combine_sentences(sentences, buffer_size=1):
    for i in range(len(sentences)):
        # Create string to hold joined sentences
        combined_sentence = ""
        # Add sentences before current one, based on buffer
        for j in range(i - buffer_size, i):
            # Check if index j is not negative
            if j >= 0:
                # Add sentence to combined str
                combined_sentence += sentences[j]["sentence"] + " "

        # Add the current sentence
        combined_sentence += sentences[i]["sentence"]

        # Add sentences after current one, based on buffer
        for j in range(i + 1, i + 1 + buffer_size):
            if j < len(sentences):
                # Add sentence to combined str
                combined_sentence += " " + sentences[j]["sentence"]

        # Then add everything to dict
        sentences[i]["combined_sentence"] = combined_sentence
    return sentences


# Uncomment when needed
# def image_to_base64(image_path: str):
#     with Image.open(image_path) as image:
#         buffered = io.BytesIO()
#         image.save(buffered, format=image.format)
#         img_str = base64.b64encode(buffered.getvalue())
#         return img_str.decode("utf-8")


# Document Splitters


def split_sentence(file_path: str):
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    if len(documents) == 0:
        raise Exception("No documents found.")
    text_splitter = SentenceSplitter(chunk_size=550, chunk_overlap=15)
    #  nodes are chunks of the source document
    nodes = text_splitter.get_nodes_from_documents(documents)
    return nodes


# Uncomment when needed
# def pdf_split(folder_path: str, filename: str):
#     image_output_path = os.path.join(folder_path, OUTPUT_PDF_IMAGES_PATH)
#     file_path = os.path.join(folder_path, filename)

#     # @TODO pip install unstructured and import partition_pdf
#     def partition_pdf():
#         return [{}]

#     # Extracts elements from pdf (tables, text, images, etc)
#     elements = partition_pdf(
#         filename=file_path,
#         # Find embedded image blocks
#         extract_images_in_pdf=True,
#         # helpers
#         strategy="hi_res",
#         infer_table_structure=True,
#         model_name="yolox",
#         chunking_strategy="by_little",
#         max_characters=4000,
#         new_after_n_chars=3800,
#         combine_text_under_n_chars=2000,
#         image_output_dir_path=image_output_path,
#     )
#     # Extract table data as html since LLM's understand them better
#     table = elements[0].metadata.text_as_html
#     # When encountering images, 2 strategies:
#     # 1. Generate a text summary and embed that text
#     # 2. Generate embeddings for image using pre-trained vision model
#     image_paths = [
#         f
#         for f in os.listdir(folder_path)
#         if os.path.isfile(os.path.join(folder_path, f))
#     ]
#     image_summaries = []
#     for img_path in image_paths:
#         image_str = image_to_base64(img_path)
#         # @TODO Feed this image url to Vision LLM to summarize
#         summary = "This is a summary"  # llm.vision({"url": f"data:image/jpeg;base64,{image_str}"})
#         image_summaries.append(summary)

#     # @TODO Return all results combined
#     return [table, image_summaries]


# Text Splitters

# Uncomment when needed
# def split_chars(text: str):
#     text_splitter = CharacterTextSplitter(
#         chunk_size=35, chunk_overlap=4, seperator="", strip_whitespace=False
#     )
#     docs = text_splitter.create_documents([text])
#     result = []
#     for document in docs:
#         result.append(document.page_content)
#     return result


# Split by similarity (advanced)
# This is handled in llama-index -> SemanticSplitterNodeParser: https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules.html#semanticsplitternodeparser
# Output a pairwise sequence of chunks and embeddings List[{chunk: string, embedding: List[int]}]
# Use this output to compare sentences together and find the largest discrepency (distance) in relationship
# for determining when to break text off for chunks.
def semantic_split(text: str):
    # Split out all sentences
    single_sentences_list = re.split(r"(?<=[.?!])\s+", text)
    # Create a document data type with helpful metadata
    sentences = [
        {"sentence": x, "index": i} for i, x in enumerate(single_sentences_list)
    ]
    combined_sentences = combine_sentences(sentences)
    return combined_sentences


# Instruct an LLM to chunk the text (advanced)
def agentic_split(text: str):
    return text


# Uncomment when needed
# Recommended for general use
# def recursive_char_split(text: str) -> List[str]:
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=550, chunk_overlap=0)
#     docs = text_splitter.create_documents([text])
#     result = []
#     for document in docs:
#         result.append(document.page_content)
#     return docs


# Uncomment when needed
# def code_split(text: str):
#     text_splitter = RecursiveCharacterTextSplitter.from_language(
#         language=Language.JS, chunk_size=65, chunk_overlap=0
#     )
#     docs = text_splitter.create_documents([text])
#     result = []
#     for document in docs:
#         result.append(document.page_content)
#     return


# Parsers


# Recommended for markdown or code documents
def markdown_document_split(chunk_size: int = 500, chunk_overlap: int = 0):
    return LangchainNodeParser(
        MarkdownNodeParser(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            keep_separator=True,
            # length_function=length_function,
        )
    )


# Split along major headings (h2) then by whole sentences
def markdown_heading_split(chunk_size: int = 500, chunk_overlap: int = 0):
    return SentenceSplitter(
        # @TODO This seems to work for now, maybe expand on this later?
        paragraph_separator="\n## ",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
