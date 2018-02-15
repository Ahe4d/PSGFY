# TorqueVM Opcodes:
OPCODES = {
    83:      "OP_FUNC_DECL",
    82:      "OP_CREATE_OBJECT",
    5:      "OP_ADD_OBJECT",
    59:      "OP_END_OBJECT",
    50:      "OP_JMPIFFNOT",
    13:      "OP_JMPIFNOT",
    27:      "OP_JMPIFF",
    51:      "OP_JMPIF",
    70:      "OP_JMPIFNOT_NP",
    26:      "OP_JMPIF_NP",
    28:     "OP_JMP",
    72:     "OP_RETURN",
    34:     "OP_CMPEQ",
    35:     "OP_CMPGR",
    74:     "OP_CMPGE",
    60:     "OP_CMPLT",
    23:     "OP_CMPLE",
    36:     "OP_CMPNE",
    73:     "OP_XOR",
    48:     "OP_MOD",
    77:     "OP_BITAND",
    29:     "OP_BITOR",
    64:     "OP_NOT",
    65:     "OP_NOTF",
    78:     "OP_ONESCOMPLEMENT",
    31:     "OP_SHR",
    30:     "OP_SHL",
    71:     "OP_AND",
    37:     "OP_OR",
    68:     "OP_ADD",
    53:     "OP_SUB",
    54:     "OP_MUL",
    55:     "OP_DIV",
    56:     "OP_NEG",
    66:     "OP_SETCURVAR",
    62:     "OP_SETCURVAR_CREATE",
    67:     "OP_SETCURVAR_ARRAY",
    69:     "OP_SETCURVAR_ARRAY_CREATE",
    11:     "OP_LOADVAR_UINT",
    45:     "OP_LOADVAR_FLT",
    44:     "OP_LOADVAR_STR",
    52:     "OP_SAVEVAR_UINT",
    14:     "OP_SAVEVAR_FLT",
    12:     "OP_SAVEVAR_STR",
    39:     "OP_SETCUROBJECT",
    63:     "OP_SETCUROBJECT_NEW",
    24:     "OP_SETCURFIELD",
    25:     "OP_SETCURFIELD_ARRAY",
    42:     "OP_LOADFIELD_UINT",
    47:     "OP_LOADFIELD_FLT",
    75:     "OP_LOADFIELD_STR",
    #76:     "OP_SAVEFIELD_UINT",
    46:     "OP_SAVEFIELD_FLT",
    76:     "OP_SAVEFIELD_STR",
    38:     "OP_STR_TO_UINT",
    58:     "OP_STR_TO_FLT",
    10:     "OP_STR_TO_NONE",
    8:     "OP_FLT_TO_UINT",
    9:     "OP_FLT_TO_STR",
    81:     "OP_FLT_TO_NONE",
    0:     "OP_UINT_TO_FLT",
    2:     "OP_UINT_TO_STR",
    32:     "OP_STR_TO_NONE",
    15:     "OP_LOADIMMED_UINT",
    16:     "OP_LOADIMMED_FLT",
    18:     "OP_TAG_TO_STR",
    19:     "OP_LOADIMMED_STR",
    17:     "OP_LOADIMMED_IDENT",
    7:     "OP_CALLFUNC_RESOLVE",
    43:     "OP_CALLFUNC",
    22:     "OP_ADVANCE_STR",
    20:     "OP_ADVANCE_STR_APPENDCHAR",
    79:     "OP_ADVANCE_STR_COMMA",
    #80:     "OP_ADVANCE_STR_NUL",
    41:     "OP_REWIND_STR",
    33:     "OP_COMPARE_STR",
    80:     "OP_PUSH",
    40:     "OP_PUSH_FRAME",
    3:      "OP_UINT_TO_NONE",
    61:     "OP_BREAK",
    1337:     "OP_IGNORE",
    21:       "OP_TERMINATE_REWIND_STR",
    151:        "OP_IGNORE",
    217:        "OP_IGNORE",
    1:          "OP_ADVANCE_STR_NUL",
    100:        "OP_IGNORE",
    205:        "OP_IGNORE",
    87:         "OP_IGNORE",
    210:        "OP_IGNORE",
    343:        "OP_IGNORE",
    141:        "OP_IGNORE",
    148:        "OP_IGNORE",
    49:         "OP_LOADFIELD_UINT",
    399:        "OP_IGNORE",
    359:        "OP_IGNORE",
    174:        "OP_IGNORE",
    1273:       "OP_IGNORE",
    # From here on, values added by me to help decompilation
    0x1000:     "META_ELSE",
    0x1001:     "META_ENDIF",
    0x1002:     "META_ENDWHILE_FLT",
    0x1003:     "META_ENDWHILE",
    0x1004:     "META_ENDFUNC",
    0x1005:     "META_END_BINARYOP",
    0x1006:     "META_SKIP",
    0x1007:     "META_ENDWHILEB",
}

METADATA = {
    "META_ELSE":            0x1000,
    "META_ENDIF":           0x1001,
    "META_ENDWHILE_FLT":    0x1002,
    "META_ENDWHILE":        0x1003,
    "META_ENDFUNC":         0x1004,
    "META_END_BINARYOP":    0x1005,
    "META_SKIP":            0x1006,
    "META_ENDWHILEB":       0x1007,
}

COMPARISON = {
    "OP_CMPEQ": "==",
    "OP_CMPLT": "<",
    "OP_CMPNE": "!=",
    "OP_CMPGR": ">",
    "OP_CMPGE": ">=",
    "OP_CMPLE": "<=",
}


# Fixes opcodes for legacy Torque versions.
def translate_opcode(version, opcode):
    return opcode


def get_opcode(version, value):
    # Fix the opcode for scripts compiled with an old version.
        #if value >= 100 and value != 0x1000 and value != 0x1001 and value != 0x1002 and value != 0x1003 and value != 0x1004 and value != 0x1005:
           # return "OP_IGNORE"
    return OPCODES[value]

STRING_OPERATORS = {
    "\t":   "TAB",
    "\n":   "NL",
    " ":    "SPC"
}

CALL_TYPES = {
    #72:  "FunctionCall",
    0:  "FunctionCall",
    1:  "MethodCall",
    2:  "ParentCall"
}
