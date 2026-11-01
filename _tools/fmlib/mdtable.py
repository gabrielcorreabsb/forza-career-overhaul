"""Markdown tables for generated data (the repo keeps tables as .md, never .csv).

`write_parts` splits a big table into files of at most `max_bytes` (the
pre-commit hook refuses files above 5 MB): the first part takes the requested
name, the others get `-2`, `-3`, ... before `.md`.
"""

import os

MAX_BYTES = int(4.5 * 1024 * 1024)


def cell(value):
    """One table cell: no pipes or newlines can break the row."""
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|") \
        .replace("\r", " ").replace("\n", " ")


def row_line(values):
    return "| " + " | ".join(cell(v) for v in values) + " |"


def header_lines(cols):
    return [row_line(cols), "|" + "---|" * len(cols)]


def table(cols, rows):
    """Lines of one Markdown table (rows are sequences in `cols` order)."""
    return header_lines(cols) + [row_line(r) for r in rows]


def part_path(base_path, idx):
    return base_path if idx == 1 else base_path[:-3] + "-%d.md" % idx


def write_parts(base_path, title, intro, cols, rows, max_bytes=MAX_BYTES):
    """Write `rows` as one or more .md files; returns the paths written.

    title  -- H1 of every part ("(part N)" is appended after the first)
    intro  -- list of lines placed under the title of every part
    """
    paths = []
    head = header_lines(cols)

    def flush(lines, idx):
        path = part_path(base_path, idx)
        name = title if idx == 1 else "%s (part %d)" % (title, idx)
        text = "\n".join(["# " + name, ""] + list(intro) + [""] + head
                         + lines) + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        paths.append(path)

    fixed = len("\n".join(["# " + title + " (part 99)", ""] + list(intro)
                          + [""] + head).encode("utf-8")) + 2
    idx, chunk, size = 1, [], fixed
    for r in rows:
        line = row_line(r)
        n = len(line.encode("utf-8")) + 1
        if chunk and size + n > max_bytes:
            flush(chunk, idx)
            idx, chunk, size = idx + 1, [], fixed
        chunk.append(line)
        size += n
    if chunk or not paths:
        flush(chunk, idx)
    return paths


def remove_parts(base_path):
    """Delete a previous run's parts of `base_path` (base, -2, -3, ...)."""
    idx = 1
    while True:
        path = part_path(base_path, idx)
        if not os.path.isfile(path):
            if idx > 1:
                return
        else:
            os.remove(path)
        idx += 1
