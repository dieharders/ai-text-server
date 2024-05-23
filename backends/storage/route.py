import os
import json
from fastapi import APIRouter
from core import classes, common
from storage import classes as storage_classes

router = APIRouter()


PLAYGROUND_SETTINGS_FILE_NAME = "playground.json"
BOT_SETTINGS_FILE_NAME = "bots.json"


# Load playground settings
@router.get("/playground-settings")
def get_playground_settings() -> classes.GetPlaygroundSettingsResponse:
    # Paths
    file_name = PLAYGROUND_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)
    loaded_data = {}

    # Check if folder exists
    if not os.path.exists(common.APP_SETTINGS_PATH):
        print("Path does not exist.", flush=True)
        os.makedirs(common.APP_SETTINGS_PATH)

    try:
        # Open the file
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, fail
        print("No file exists.", flush=True)

    return {
        "success": True,
        "message": f"Returned app settings",
        "data": loaded_data,
    }


# Save playground settings
@router.post("/playground-settings")
def save_playground_settings(data: dict) -> classes.GenericEmptyResponse:
    # Paths
    file_name = PLAYGROUND_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)

    # Save to disk
    common.save_settings_file(common.APP_SETTINGS_PATH, file_path, data)

    return {
        "success": True,
        "message": f"Saved settings to {file_path}",
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


# Load chat thread
@router.get("/chat-thread")
def get_chat_thread(
    params: storage_classes.GetChatThreadRequest,
) -> storage_classes.GetChatThreadResponse:
    folder_path = common.app_path("threads")
    file_name = f"{params.threadId}.json"
    file_path = os.path.join(folder_path, file_name)
    try:
        # Create folder/file
        if not os.path.exists(folder_path):
            print(f"{common.PRNT_API} Folder does not exist: {folder_path}", flush=True)
            os.makedirs(folder_path)
        # Try to open the file (if it exists)
        with open(file_path, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        # file doesn't exist
        return {
            "success": False,
            "message": f"Failed to load chat thread from {file_path}, FileNotFoundError",
            "data": None,
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": f"Failed to load chat thread from {file_path}, JSONDecodeError",
            "data": None,
        }

    return {
        "success": True,
        "message": f"Loaded chat thread from {file_path}",
        "data": existing_data,
    }


# Save chat thread
@router.post("/chat-thread")
def save_chat_thread(params: storage_classes.SaveChatThreadRequest):
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
