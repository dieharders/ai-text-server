import os
import glob
import json
from fastapi import APIRouter, Depends
from core import classes, common
from storage import classes as storage_classes
from nanoid import generate as uuid

router = APIRouter()


BOT_SETTINGS_FILE_NAME = "bots.json"
TOOL_SETTINGS_BASE_PATH = os.path.join(common.APP_SETTINGS_PATH, "tools", "defs")


# Save tool settings
@router.post("/tool-settings")
def save_tool_definition(settings: dict) -> classes.EmptyToolSettingsResponse:
    # Paths
    new_id = uuid()
    file_name = f"{new_id}.json"
    file_path = os.path.join(TOOL_SETTINGS_BASE_PATH, file_name)
    # Save tool to file
    common.store_tool_definition(
        operation="w",
        folderpath=TOOL_SETTINGS_BASE_PATH,
        filepath=file_path,
        data={**settings, "id": new_id},
    )

    return {
        "success": True,
        "message": f"Saved tool settings.",
        "data": None,
    }


# Get all tool settings
@router.get("/tool-settings")
def get_all_tool_definitions() -> classes.GetToolSettingsResponse:
    # Save tool to file
    tools = common.store_tool_definition(
        operation="r",
        folderpath=TOOL_SETTINGS_BASE_PATH,
    )
    numTools = len(tools)

    return {
        "success": True,
        "message": f"Returned {numTools} tool(s) definitions.",
        "data": tools,
    }


# Delete tool setting
@router.delete("/tool-settings")
def delete_tool_definition_by_id(id: str) -> classes.EmptyToolSettingsResponse:
    # Remove tool file
    common.store_tool_definition(
        operation="d",
        folderpath=TOOL_SETTINGS_BASE_PATH,
        id=id,
    )

    return {
        "success": True,
        "message": f"Removed tool definition.",
        "data": None,
    }


# Save bot settings
@router.post("/bot-settings")
def save_bot_settings(settings: dict) -> classes.BotSettingsResponse:
    # Paths
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)
    # Save to memory
    results = common.save_bot_settings_file(
        common.APP_SETTINGS_PATH, file_path, settings
    )

    return {
        "success": True,
        "message": f"Saved bot settings to {file_path}",
        "data": results,
    }


# Delete bot settings
@router.delete("/bot-settings")
def delete_bot_settings(name: str) -> classes.BotSettingsResponse:
    new_settings = []
    # Paths
    base_path = common.APP_SETTINGS_PATH
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(base_path, file_name)
    try:
        # Try to open the file (if it exists)
        if os.path.exists(base_path):
            prev_settings = None
            with open(file_path, "r") as file:
                prev_settings = json.load(file)
                for setting in prev_settings:
                    if name == setting.get("model").get("botName"):
                        # Delete setting dict
                        del_index = prev_settings.index(setting)
                        del prev_settings[del_index]
                        # Save new settings
                        new_settings = prev_settings
                        break
            # Save new settings to file
            with open(file_path, "w") as file:
                if new_settings is not None:
                    json.dump(new_settings, file, indent=2)
    except FileNotFoundError:
        return {
            "success": False,
            "message": "Failed to delete bot setting. File does not exist.",
            "data": None,
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Failed to delete bot setting. Invalid JSON format or empty file.",
            "data": None,
        }

    msg = "Removed bot setting."
    print(f"{common.PRNT_API} {msg}")
    return {
        "success": True,
        "message": f"Success: {msg}",
        "data": new_settings,
    }


# Load bot settings
@router.get("/bot-settings")
def get_bot_settings() -> classes.BotSettingsResponse:
    # Paths
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)

    # Check if folder exists
    if not os.path.exists(common.APP_SETTINGS_PATH):
        return {
            "success": False,
            "message": "Failed to return settings. Folder does not exist.",
            "data": [],
        }

    # Try to open the file (if it exists)
    loaded_data = []
    try:
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, return empty
        return {
            "success": False,
            "message": "Failed to return settings. File does not exist.",
            "data": [],
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Invalid JSON format or empty file.",
            "data": [],
        }

    return {
        "success": True,
        "message": f"Returned bot settings",
        "data": loaded_data,
    }


# Load (one or all) chat thread(s)
@router.get("/chat-thread")
async def get_chat_thread(
    params: storage_classes.GetChatThreadRequest = Depends(),
) -> storage_classes.GetChatThreadResponse:
    folder_path = common.app_path("threads")
    threadId = params.threadId
    file_name = f"{threadId}.json"
    file_path = os.path.join(folder_path, file_name)
    data = []
    try:
        # Create folder/file
        if not os.path.exists(folder_path):
            print(f"{common.PRNT_API} Folder does not exist: {folder_path}", flush=True)
            os.makedirs(folder_path)
        if threadId:
            # Try to open thread file by id
            with open(file_path, "r") as file:
                thread_data = json.load(file)
                data.append(thread_data)
        else:
            # Return each thread file and add contents
            for name in os.listdir(folder_path):
                path = os.path.join(folder_path, name)
                with open(path, "r") as file:
                    file_data = json.load(file)
                    data.append(file_data)
    except FileNotFoundError as err:
        return {
            "success": False,
            "message": f"Failed to load chat thread, FileNotFoundError.\n{err}",
            "data": [],
        }
    except json.JSONDecodeError as err:
        return {
            "success": False,
            "message": f"Failed to load chat thread, JSONDecodeError.\n{err}",
            "data": [],
        }
    except Exception as err:
        return {
            "success": False,
            "message": f"Failed to load chat thread.\n{err}.",
            "data": [],
        }
    # Results
    return {
        "success": True,
        "message": f"Loaded chat thread(s).",
        "data": data,
    }


# Save chat thread
@router.post("/chat-thread")
async def save_chat_thread(params: storage_classes.SaveChatThreadRequest):
    thread_id = params.threadId
    thread = params.thread
    # Path
    folder_path = common.app_path("threads")
    file_name = f"{thread_id}.json"
    file_path = os.path.join(folder_path, file_name)
    # Create folder/file
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    try:
        # Save the data to the file, this will overwrite all values
        with open(file_path, "w") as file:
            json.dump(thread, file, indent=2)
    except Exception as err:
        return {
            "success": False,
            "message": f"Failed to save chat thread to {file_path} \n{err}",
            "data": None,
        }

    return {
        "success": True,
        "message": f"Saved chat thread to {file_path}",
        "data": None,
    }


# Delete (one or all) chat thread(s)
@router.delete("/chat-thread")
async def delete_chat_thread(
    params: storage_classes.DeleteChatThreadRequest = Depends(),
):
    thread_id = params.threadId
    folder_path = common.app_path("threads")
    if not os.path.exists(folder_path):
        raise Exception("Folder does not exist")
    try:
        if thread_id:
            # Path
            file_name = f"{thread_id}.json"
            file_path = os.path.join(folder_path, file_name)
            # Delete thread file by id
            os.remove(file_path)
            print(f"{common.PRNT_API} Removed single file: {file_path}")
        else:
            # Pattern to match all files
            pattern = os.path.join(folder_path, "*")
            # Get all file paths in the directory
            files = glob.glob(pattern)
            # Remove all thread files in dir
            for path in files:
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"{common.PRNT_API} Removed file from dir: {path}")
    except Exception as err:
        return {
            "success": False,
            "message": f"Failed to remove chat thread.\n{err}",
            "data": None,
        }
    return {
        "success": True,
        "message": f"Removed chat thread(s)",
        "data": None,
    }
