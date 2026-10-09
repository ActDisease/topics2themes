"""Additive page-reader hooks for Svenska Läkartidningen collections."""

from pathlib import Path
import re


PAGE = re.compile(r"^svenska_lakartidningen_(\d{4})_.+\.txt$")


def page_year(path):
    name = Path(path).name
    match = PAGE.fullmatch(name)
    if not match or name.endswith("_comments.txt"):
        raise ValueError(f"Unexpected journal page: {path}")
    return [f"{match.group(1)}-01-01"]


def nonblank_pages_without_comments(labels, collection, cleaning, ngram_length, remove_duplicates):
    from make_topic_models import read_documents

    documents, metadata, removed = read_documents(
        labels, collection, cleaning, ngram_length, remove_duplicates
    )
    texts, information = [], []
    comments = blanks = 0
    for text, info in zip(documents, metadata):
        if Path(info["full_name"]).name.endswith("_comments.txt"):
            comments += 1
        elif not text.strip():
            blanks += 1
        else:
            page_year(info["full_name"])
            texts.append(text)
            information.append(info)
            continue
        removed.append((text.replace("\n", " "), info["full_name"]))
    print(f"Excluded {comments} comment files and {blanks} blank pages; kept {len(texts)} pages", flush=True)
    return texts, information, removed
