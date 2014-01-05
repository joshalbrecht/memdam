
import re

import memdam.common.field

BASE_FIELD_PATTERN = r"[a-z][a-z0-9]*(_[a-z0-9]+)*"
FIELD_TYPE_PATTERN = '(' + '|'.join([r.lower() for r in memdam.common.field.FieldType.names.values()]) + ')'
UUID_HEX_PATTERN = r"[0-9a-f]{32}"
EXTENSION_PATTERN = r"[a-z0-9_]+"
BLOB_FILE_NAME_REGEX = re.compile("^" + UUID_HEX_PATTERN + r"\." + EXTENSION_PATTERN + "$")
EVENT_FIELD_REGEX = re.compile("^" + BASE_FIELD_PATTERN + "__" + FIELD_TYPE_PATTERN + "(__" + BASE_FIELD_PATTERN + "){0,1}$")
