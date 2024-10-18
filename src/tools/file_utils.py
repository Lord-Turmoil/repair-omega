def file_get_line_count(filename: str):
    """
    Get the number of lines in a file.
    Return -1 if the file does not exist.
    """
    with open(filename, "r") as f:
        lines = f.readlines()
    return len(lines)


def file_get_content(filename: str, start_line: int, end_line: int):
    """
    Get the content of a file from start_line to end_line (both inclusive).
    Return empty string if the file does not exist or the range is invalid.
    """
    with open(filename, "r") as f:
        lines = f.readlines()
    end_line = min(end_line, len(lines) - 1)
    if start_line < 1:
        start_line = 1
    if end_line < start_line:
        return ""
    return "".join(lines[start_line - 1 : end_line])


def file_get_decorated_content(filename: str, start_line: int, end_line: int):
    """
    Get the content of a file from start_line to end_line (both inclusive)
    with line_number in each line.
    """
    with open(filename, "r") as f:
        lines = f.readlines()
    end_line = min(end_line, len(lines) - 1)
    if start_line < 1:
        start_line = 1
    if end_line < start_line:
        return ""
    content = ""
    for i, line in enumerate(lines[start_line - 1 : end_line], start_line):
        content += f"{i:3} {line}"
    return content
