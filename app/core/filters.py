def match_extension(filename: str, ext: str):
    return not ext or filename.endswith(ext)


def match_name(filename: str, name: str):
    return not name or name in filename.lower()