import re
import os
import glob
import httpx
import subprocess
from typing import List, Tuple


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
