import re
import os
import json
import glob
import httpx
import subprocess
from typing import Any, List, Tuple
from server.classes import (
    CHAT_MODES,
    InstalledTextModelMetadata,
    InstalledTextModel,
    ModelConfig,
    DEFAULT_CHAT_MODE,
    DEFAULT_CONTEXT_WINDOW,
)

INSTALLED_TEXT_MODELS = "installed_text_models"
DEFAULT_MAX_TOKENS = 128


# This will return a context window that is suited for a particular mode.
# This impacts how long a conversation you can have before the context_window limit is reached (and issues/hallucinations begin) for a given Ai model.
def calc_max_tokens(
    max_tokens: int = 0,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    mode: str = DEFAULT_CHAT_MODE,
):
    system_msg_buffer = 100
    # Use what is provided, otherwise calculate a value
    if max_tokens > 0:
        return max_tokens
    if mode == CHAT_MODES.INSTRUCT.value:
        # Cant be too high or it fails
        context_buffer = context_window // 2
        # Largest possible since every request is a one-off response
        return context_window - context_buffer - system_msg_buffer
    else:
        # should prob be a factor (ctx/8) of the context window. Providing a few back and forth convo before limit is reached.
        context_factor = 8
        result = (context_window // context_factor) - system_msg_buffer
        if result <= 0:
            result = DEFAULT_MAX_TOKENS
        return result


def kill_text_inference(app):
    if hasattr(app, "text_inference_process"):
        if app.text_inference_process.poll() != None:
            app.text_inference_process.kill()
            app.text_inference_process = None


def parse_mentions(input_string) -> Tuple[List[str], str]:
    # Pattern match words starting with @ at the beginning of the string
    pattern = r"^@(\w+)"

    # Find the match at the beginning of the string
    matches = re.findall(pattern, input_string)

    # Check if there is a match
    if matches:
        # Remove the matched words from the original string
        base_query = re.sub(pattern, "", input_string)
        print(f"Found mentions starting with @: {matches}")
        return [matches, base_query]
    else:
        return [[], input_string]


# Open a native file explorer at location of given source
def file_explore(path: str):
    FILEBROWSER_PATH = os.path.join(os.getenv("WINDIR"), "explorer.exe")

    # explorer would choke on forward slashes
    path = os.path.normpath(path)

    if os.path.isdir(path):
        subprocess.run([FILEBROWSER_PATH, path])
    elif os.path.isfile(path):
        subprocess.run([FILEBROWSER_PATH, "/select,", path])


async def get_file_from_url(url: str, pathname: str, app):
    # example url: https://raw.githubusercontent.com/dieharders/ai-text-server/master/README.md
    client: httpx.Client = app.requests_client
    CHUNK_SIZE = 1024 * 1024  # 1mb
    TOO_LONG = 751619276  # about 700mb limit in "bytes"
    headers = {
        "Content-Type": "application/octet-stream",
    }
    # @TODO Verify stored checksum before downloading
    head_res = client.head(url)
    total_file_size = head_res.headers.get("content-length")
    if int(total_file_size) > TOO_LONG:
        raise Exception("File is too large")
    # Stream binary content
    with client.stream("GET", url, headers=headers) as res:
        res.raise_for_status()
        if res.status_code != httpx.codes.OK:
            raise Exception("Something went wrong fetching file")
        if int(res.headers["Content-Length"]) > TOO_LONG:
            raise Exception("File is too large")
        with open(pathname, "wb") as file:
            # Write data to disk
            for block in res.iter_bytes(chunk_size=CHUNK_SIZE):
                file.write(block)
    return True


# Determine if the input string is acceptable as an id
def check_valid_id(input: str):
    l = len(input)
    # Cannot be empty
    if not l:
        return False
    # Check for sequences reserved for our parsing scheme
    matches_double_hyphen = re.findall("--", input)
    if matches_double_hyphen:
        print(f"[homebrew api] Found double hyphen in 'id': {input}")
        return False
    # All names must be 3 and 63 characters
    if l > 63 or l < 3:
        return False
    # No hyphens at start/end
    if input[0] == "-" or input[l - 1] == "-":
        print("[homebrew api] Found hyphens at start/end in [id]")
        return False
    # No whitespace allowed
    matches_whitespace = re.findall("\s", input)
    if matches_whitespace:
        print("[homebrew api] Found whitespace in [id]")
        return False
    # Check special chars. All chars must be lowercase. Dashes acceptable.
    m = re.compile(r"[a-z0-9-]*$")
    if not m.match(input):
        print("[homebrew api] Found invalid special chars in [id]")
        return False
    # Passes
    return True


# Verify the string contains only lowercase letters, numbers, and a select special chars and whitespace
# In-validate by checking for "None" return value
def parse_valid_tags(tags: str):
    try:
        # Check for correct type of input
        if not isinstance(tags, str):
            raise Exception("'Tags' must be a string")
        # We dont care about empty string for optional input
        if not len(tags):
            return tags
        # Remove commas
        result = tags.replace(",", "")
        # Allow only lowercase chars, numbers and certain special chars and whitespaces
        m = re.compile(r"^[a-z0-9$*-]+( [a-z0-9$*-]+)*$")
        if not m.match(result):
            raise Exception("'Tags' input value has invalid chars.")
        # Remove any whitespace, hyphens from start/end
        result = result.strip()
        result = result.strip("-")

        # Remove invalid single words
        array_values = result.split(" ")
        result_array = []
        for word in array_values:
            # Words cannot have dashes at start/end
            p_word = word.strip("-")
            # Single char words not allowed
            if len(word) > 1:
                result_array.append(p_word)
        result = " ".join(result_array)
        # Remove duplicate tags
        result = dedupe_substrings(result)
        # Return a sanitized string
        return result
    except Exception as e:
        print(f"[homebrew api] {e}")
        return None


def delete_vector_store(target_file_path: str, folder_path):
    path_to_delete = os.path.join(folder_path, target_file_path)
    if os.path.exists(path_to_delete):
        files = glob.glob(f"{path_to_delete}/*")
        for f in files:
            os.remove(f)  # del files
        os.rmdir(path_to_delete)  # del folder


def dedupe_substrings(input_string):
    unique_substrings = set()
    str_array = input_string.split(" ")
    result = []

    for substring in str_array:
        if substring not in unique_substrings:
            unique_substrings.add(substring)
            result.append(substring)

    # Return as space seperated
    return " ".join(result)


def get_settings_file(folderpath: str, filepath: str):
    # Check if folder exists
    if not os.path.exists(folderpath):
        raise Exception("Folder does not exist.")

    # Try to open the file (if it exists)
    loaded_data = {}
    try:
        with open(filepath, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        print("File does not exist.", flush=True)
    except json.JSONDecodeError:
        print("Invalid JSON format or empty file.", flush=True)

    return loaded_data

def save_bot_settings_file(folderpath: str, filepath: str, data: Any):
    # Create folder/file
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)

    # Try to open the file (if it exists)
    try:
        with open(filepath, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, create an empty
        existing_data = []
    except json.JSONDecodeError:
        existing_data = []

    # Update the existing data
    existing_data.append(data)

    # Save the updated data to the file, this will overwrite all values
    with open(filepath, "w") as file:
        json.dump(existing_data, file, indent=2)

    return existing_data

def save_settings_file(folderpath: str, filepath: str, data: Any):
    # Create folder/file
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)

    # Try to open the file (if it exists)
    try:
        with open(filepath, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, create an empty dictionary
        existing_data = {}
    except json.JSONDecodeError:
        existing_data = {}

    # Update the existing data with the new variables
    for key, val in data.items():
        existing_data[key] = val

    # Save the updated data to the file, this will overwrite all values in the key's dict.
    with open(filepath, "w") as file:
        json.dump(existing_data, file, indent=2)

    return existing_data


# Return metadata for the currently loaded model
def get_model_metadata(
    id: str, folderpath: str, filepath: str
) -> InstalledTextModelMetadata:
    metadata = {}
    # Gets all installation metadata
    settings: InstalledTextModel = get_settings_file(folderpath, filepath)
    models = settings[INSTALLED_TEXT_MODELS]
    for item in models:
        if item["id"] == id:
            metadata = item
            break
    return metadata


# Gets the llm model configuration data
def get_model_config(id: str, folderpath, filepath) -> ModelConfig:
    configs = get_settings_file(folderpath, filepath)
    config = configs[id]
    return config
