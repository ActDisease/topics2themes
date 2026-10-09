"""Exploratory large-corpus configuration, not a claim of optimal settings."""

from data_folder.sv_lakartidningen_baseline.topic_model_configuration import (
    ADDITIONAL_LABELS_METHOD,
    DATA_LABEL_LIST,
    READ_FUNCTION,
    TOPIC_MODEL_ALGORITHM,
)

STOP_WORD_FILE = "swedish_grammatical_stopwords.txt"
NUMBER_OF_TOPICS = 50
NUMBER_OF_RUNS = 20
OVERLAP_CUT_OFF = 0.6
NR_OF_TOP_DOCUMENTS = 150
MIN_DOCUMENT_FREQUENCY = 20
MAX_DOCUMENT_FREQUENCY = 0.95
MAX_NR_OF_FEATURES = 60000
SUBLINEAR_TF = True
# Make the original fork defaults explicit; these do not change the saved run.
NR_OF_ITERATIONS = 200
PERCENTATE_NONE_OUTLIERS = 0.75
PROPORTION_OF_LESS_TOPIC_TO_ALLOW = 1
PRE_PROCESS = False
REMOVE_DUPLICATES = False
BINARY_TF = False
USE_IDF = True
STOP_WORD_SET = set()
DEBUG = False
STORE_IN_DATABASE = False
