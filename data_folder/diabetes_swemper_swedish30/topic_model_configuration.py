"""Exploration candidate, not a replacement for the original NMF baseline.

NLTK Swedish stopwords minus negators and the lexical verb 'sitta';
30 requested topics; a broader top-document export. All core modeling
code and the original stability/vocabulary-frequency settings are unchanged.
"""

from data_folder.diabetes_swemper.topic_model_configuration import (
    ADDITIONAL_LABELS_METHOD,
    DATA_LABEL_LIST,
    READ_FUNCTION,
    TOPIC_MODEL_ALGORITHM,
)

STOP_WORD_FILE = "swedish_grammatical_stopwords.txt"
NUMBER_OF_TOPICS = 30
NR_OF_TOP_DOCUMENTS = 100
NUMBER_OF_RUNS = 20
OVERLAP_CUT_OFF = 0.6
MIN_DOCUMENT_FREQUENCY = 10
MAX_DOCUMENT_FREQUENCY = 0.95
# Make the original fork defaults explicit for portable parameter editing.
MAX_NR_OF_FEATURES = None
SUBLINEAR_TF = False
NR_OF_ITERATIONS = 200
PERCENTATE_NONE_OUTLIERS = 0.75
PROPORTION_OF_LESS_TOPIC_TO_ALLOW = 1
PRE_PROCESS = False
REMOVE_DUPLICATES = False
BINARY_TF = False
USE_IDF = True
STOP_WORD_SET = set()
DEBUG = False
# The selected-document model exceeds MongoDB's 16 MiB document limit.
# Use the fork's supported disk-model / MongoDB-metadata storage path.
STORE_IN_DATABASE = False
