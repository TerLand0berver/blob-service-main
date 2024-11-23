"""
AList storage constants.
"""

# Default configuration
DEFAULT_TIMEOUT = 30
DEFAULT_CHUNK_SIZE = 8192
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1
DEFAULT_VERIFY_SSL = True

# API endpoints
LOGIN_ENDPOINT = "/api/auth/login"
FILE_LIST_ENDPOINT = "/api/fs/list"
FILE_GET_ENDPOINT = "/api/fs/get"
FILE_MKDIR_ENDPOINT = "/api/fs/mkdir"
FILE_MOVE_ENDPOINT = "/api/fs/move"
FILE_COPY_ENDPOINT = "/api/fs/copy"
FILE_REMOVE_ENDPOINT = "/api/fs/remove"
FILE_PUT_ENDPOINT = "/api/fs/put"
FILE_FORM_ENDPOINT = "/api/fs/form"

# Response keys
TOKEN_KEY = "token"
DATA_KEY = "data"
CODE_KEY = "code"
MESSAGE_KEY = "message"

# Success codes
SUCCESS_CODE = 200

# Error codes
ERROR_CODE_AUTH = 401
ERROR_CODE_PERMISSION = 403
ERROR_CODE_NOT_FOUND = 404
ERROR_CODE_SERVER_ERROR = 500

# File types
FILE_TYPE_FILE = "file"
FILE_TYPE_FOLDER = "folder"

# Content types
DEFAULT_CONTENT_TYPE = "application/octet-stream"

# Metadata keys
META_PATH = "path"
META_SIZE = "size"
META_TYPE = "type"
META_MODIFIED = "modified"
META_IS_DIR = "is_dir"
META_THUMB = "thumb"
META_SIGN = "sign"
