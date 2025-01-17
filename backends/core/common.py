import re
import sys
import os
import json
import glob
import httpx
import subprocess
from typing import Any, List, Optional, Tuple
from core.classes import (
    CHAT_MODES,
    InstalledTextModelMetadata,
    InstalledTextModel,
    ModelConfig,
    DEFAULT_CHAT_MODE,
    DEFAULT_CONTEXT_WINDOW,
)
from huggingface_hub import (
    scan_cache_dir,
    try_to_load_from_cache,
    _CACHED_NO_EXIST,
    HFCacheInfo,
    CachedFileInfo,
)


# Pass relative string to get absolute path
def app_path(relative_path):
    return os.path.join(os.getcwd(), relative_path)


# Pass a relative path to resource and return the correct absolute path. Works for dev and for PyInstaller
# If you use pyinstaller, it bundles deps into a folder alongside the binary (not --onefile mode).
# This path is set to sys._MEIPASS and any python modules or added files are put in here (runtime writes, db still go where they should).
def dep_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


MODEL_METADATAS_FILENAME = "installed_models.json"
APP_SETTINGS_FOLDER = "settings"
APP_SETTINGS_PATH = app_path(APP_SETTINGS_FOLDER)
TOOL_FOLDER = "tools"
TOOL_FUNCS_FOLDER = "functions"
TOOL_PATH = app_path(TOOL_FOLDER)
TOOL_DEFS_PATH = os.path.join(TOOL_PATH, "defs")
TOOL_PREBUILT_PATH = os.path.join(TOOL_FOLDER, TOOL_FUNCS_FOLDER)
TOOL_FUNCS_PATH = os.path.join(TOOL_PATH, TOOL_FUNCS_FOLDER)
MODEL_METADATAS_FILEPATH = os.path.join(APP_SETTINGS_PATH, MODEL_METADATAS_FILENAME)
TEXT_MODELS_CACHE_DIR = "text_models"
INSTALLED_TEXT_MODELS = "installed_text_models"  # key in json file
DEFAULT_SETTINGS_DICT = {"current_download_path": "", INSTALLED_TEXT_MODELS: []}
DEFAULT_MAX_TOKENS = 128


# Colors for logging
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


PRNT_APP = f"{bcolors.HEADER}[OBREW]{bcolors.ENDC}"
PRNT_API = f"{bcolors.HEADER}[API]{bcolors.ENDC}"
PRNT_EMBED = f"{bcolors.OKCYAN}[EMBEDDING]{bcolors.ENDC}"


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
        print(f"{PRNT_API} Found mentions starting with @: {matches}", flush=True)
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


def check_cached_file_exists(cache_dir: str, repo_id: str, filename: str):
    filepath = try_to_load_from_cache(
        cache_dir=cache_dir, repo_id=repo_id, filename=filename
    )
    if isinstance(filepath, str):
        # file exists and is cached
        print(f"{PRNT_API} File exists: {filepath}", flush=True)
    elif filepath is _CACHED_NO_EXIST:
        # non-existence of file is cached
        err = "File non-existence has been recorded."
        print(f"{PRNT_API} {err}", flush=True)
        raise Exception(err)
    else:
        # file is not cached
        err = "File not cached."
        print(f"{PRNT_API} {err}", flush=True)
        raise Exception(err)


# Find the specified model repo and return all revisions
def scan_cached_repo(cache_dir: str, repo_id: str) -> Tuple[HFCacheInfo, list]:
    # Pass nothing to scan the default dir
    model_cache_info = scan_cache_dir(cache_dir)
    repos = model_cache_info.repos
    repoIndex = next(
        (x for x, info in enumerate(repos) if info.repo_id == repo_id), None
    )
    target_repo = list(repos)[repoIndex]
    repo_revisions = list(target_repo.revisions)
    return [model_cache_info, repo_revisions]


def get_cached_blob_path(repo_revisions: list, filename: str):
    for r in repo_revisions:
        files: List[CachedFileInfo] = list(r.files)
        for file in files:
            if file.file_name == filename:
                # CachedFileInfo: file.blob_path same as -> file.file_path.resolve()
                actual_path = str(file.blob_path)
                return actual_path


# Determine if the input string is acceptable as an id
def check_valid_id(input: str):
    l = len(input)
    # Cannot be empty
    if not l:
        return False
    # Check for sequences reserved for our parsing scheme
    matches_double_hyphen = re.findall("--", input)
    if matches_double_hyphen:
        print(f"{PRNT_API} Found double hyphen in 'id': {input}")
        return False
    # All names must be 3 and 63 characters
    if l > 63 or l < 3:
        return False
    # No hyphens at start/end
    if input[0] == "-" or input[l - 1] == "-":
        print(f"{PRNT_API} Found hyphens at start/end in 'id'")
        return False
    # No whitespace allowed
    matches_whitespace = re.findall("\\s", input)
    if matches_whitespace:
        print(f"{PRNT_API} Found whitespace in 'id'")
        return False
    # Check special chars. All chars must be lowercase. Dashes acceptable.
    m = re.compile(r"[a-z0-9-]*$")
    if not m.match(input):
        print(f"{PRNT_API} Found invalid special chars in 'id'")
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
        print(f"{PRNT_API} {e}")
        return None


class SaveTextModelRequestArgs(dict):
    repoId: str
    savePath: Optional[dict] = {}
    isFavorited: Optional[bool] = False
    numTimesRun: Optional[int] = 0


# Index the path of the downloaded model in a file
def save_text_model(data: SaveTextModelRequestArgs):
    repo_id = data["repoId"]
    folderpath = APP_SETTINGS_PATH
    filepath = MODEL_METADATAS_FILEPATH
    existing_data = DEFAULT_SETTINGS_DICT

    try:
        # Create folder
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        # Try to open the file (if it exists)
        with open(filepath, "r") as file:
            existing_data = json.load(file)
    except (Exception, FileNotFoundError):
        # If the file doesn't exist yet, create an empty dictionary
        existing_data = DEFAULT_SETTINGS_DICT

    # Update the existing data with the new variables
    models_list: List = existing_data[INSTALLED_TEXT_MODELS]
    modelIndex = next(
        (x for x, item in enumerate(models_list) if item["repoId"] == repo_id), None
    )
    if modelIndex is None:
        # Assign new data
        new_data = data
        new_data["savePath"] = {}
        new_data["numTimesRun"] = 0
        new_data["isFavorited"] = False
        models_list.append(data)
    else:
        model = models_list[modelIndex]
        # Assign updated data
        for key, val in data.items():
            if key == "savePath":
                new_save_paths: dict = data[key]
                prev_save_paths: dict = model[key]
                model[key] = {
                    **prev_save_paths,
                    **new_save_paths,
                }
            else:
                model[key] = val
        models_list[modelIndex] = model

    # Save the updated data to the file, this will overwrite all values in the key's dict.
    with open(filepath, "w") as file:
        json.dump(existing_data, file, indent=2)
    return existing_data


# Deletes all files associated with a revision (model)
def delete_text_model_revisions(repo_id: str):
    filepath = MODEL_METADATAS_FILEPATH

    try:
        # Try to open the file (if it exists)
        with open(filepath, "r") as file:
            metadata = json.load(file)
        # Remove model entry from metadata
        models_list: List = metadata[INSTALLED_TEXT_MODELS]
        modelIndex = next(
            (x for x, item in enumerate(models_list) if item["repoId"] == repo_id), None
        )
        del models_list[modelIndex]
        # Save updated metadata
        with open(filepath, "w") as file:
            json.dump(metadata, file, indent=2)
    except FileNotFoundError:
        print(f"{PRNT_API} File not found.", flush=True)
    except json.JSONDecodeError:
        print(f"{PRNT_API} JSON parsing error.", flush=True)


# Delete a single (quant) file for the model
def delete_text_model(filename: str, repo_id: str):
    filepath = MODEL_METADATAS_FILEPATH

    try:
        # Try to open the file (if it exists)
        with open(filepath, "r") as file:
            metadata = json.load(file)
        # Remove model entry from metadata
        models_list: List = metadata[INSTALLED_TEXT_MODELS]
        modelIndex = next(
            (x for x, item in enumerate(models_list) if item["repoId"] == repo_id), None
        )
        model = models_list[modelIndex]
        del model["savePath"][filename]
        # Save updated metadata
        with open(filepath, "w") as file:
            json.dump(metadata, file, indent=2)
    except FileNotFoundError:
        print(f"{PRNT_API} File not found.", flush=True)
    except json.JSONDecodeError:
        print(f"{PRNT_API} JSON parsing error.", flush=True)


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
    loaded_data = None

    try:
        # Check if folder exists
        if not os.path.exists(folderpath):
            print(f"{PRNT_API} Folder does not exist: {folderpath}", flush=True)
            os.makedirs(folderpath)
        # Try to open the file (if it exists)
        with open(filepath, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        print(f"{PRNT_API} File does not exist.", flush=True)
        loaded_data = None
    except json.JSONDecodeError:
        print(f"{PRNT_API} Invalid JSON format or empty file.", flush=True)
        loaded_data = None
    return loaded_data


def store_tool_definition(
    operation: str,
    folderpath: str,
    filepath: Optional[str] = None,
    id: Optional[str] = None,
    data: Optional[Any] = None,
):
    # Create folder/file
    if not os.path.exists(folderpath):
        if operation == "d":
            # Dir does not exist to delete
            return
        os.makedirs(folderpath)

    match operation:
        # Write new tool
        case "w":
            # Try to open the file (if it exists)
            try:
                with open(filepath, "r") as file:
                    existing_data = json.load(file)
            except FileNotFoundError:
                # If the file doesn't exist yet, create an empty
                existing_data = {}
            except json.JSONDecodeError:
                existing_data = {}
            # Update the existing data
            existing_data = {**existing_data, **data}
            # Save the updated data to the file, this will overwrite all values
            with open(filepath, "w") as file:
                json.dump(existing_data, file, indent=2)
        # Read all tools
        case "r":
            try:
                existing_data = []
                files = os.listdir(folderpath)
                for file_name in files:
                    file_path = os.path.join(folderpath, file_name)
                    if os.path.isfile(file_path) and file_path.endswith(".json"):
                        with open(file_path, "r") as file:
                            prev_data = json.load(file)
                            existing_data.append(prev_data)
            except:
                existing_data = []
            return existing_data
        # Delete tool by id
        case "d":
            if not id:
                return
            files = os.listdir(folderpath)
            for file_name in files:
                file_path = os.path.join(folderpath, file_name)
                file_id = file_name.split(".")[0]
                if file_id == id:
                    os.remove(file_path)


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


def save_settings_file(folderpath: str, filepath: str, data: dict):
    try:
        # Create folder/file
        if not os.path.exists(folderpath):
            print(f"{PRNT_API} Folder does not exist: {folderpath}", flush=True)
            os.makedirs(folderpath)
        # Try to open the file (if it exists)
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
        if item["repoId"] == id:
            metadata = item
            break
    return metadata


# Gets the llm model configuration data
def get_model_config(id: str, folderpath, filepath) -> ModelConfig:
    configs = get_settings_file(folderpath, filepath)
    config = configs[id]
    return config


def get_file_extension_from_path(path: str):
    split_path = path.rsplit(".", 1)
    end = len(split_path)
    file_extension = split_path[end - 1]
    return file_extension
