from pathlib import Path
import re

from topic_model_constants import DATA_LABEL, DIRECTORY_NAME, NMF_NAME

DATA_LABEL_LIST = [{DATA_LABEL: "Diabetes", DIRECTORY_NAME: "pages"}]
STOP_WORD_FILE = "stop_words.txt"
TOPIC_MODEL_ALGORITHM = NMF_NAME


def page_year(path):
    match = re.match(r"diabetes_(\d{4})_", Path(path).name)
    if not match:
        raise ValueError(f"Unexpected Diabetes page name: {path}")
    return [f"{match.group(1)}-01-01"]


ADDITIONAL_LABELS_METHOD = page_year


def nonblank_pages(labels, collection, cleaning, ngram_length, remove_duplicates):
    from make_topic_models import read_documents

    documents, metadata, removed = read_documents(
        labels, collection, cleaning, ngram_length, remove_duplicates
    )
    kept = [(text, info) for text, info in zip(documents, metadata) if text.strip()]
    removed.extend(
        (text.replace("\n", " "), info["full_name"])
        for text, info in zip(documents, metadata)
        if not text.strip()
    )
    return [text for text, _ in kept], [info for _, info in kept], removed


READ_FUNCTION = nonblank_pages
