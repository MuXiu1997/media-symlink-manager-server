def avoid_invalid_filename_chars(filename: str) -> str:
    invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
    for c in invalid_chars:
        filename = filename.replace(c, "")
    return filename
