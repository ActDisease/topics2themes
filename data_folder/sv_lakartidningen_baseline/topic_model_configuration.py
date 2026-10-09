"""Svenska Läkartidningen baseline: original Diabetes modeling defaults."""

from topic_model_constants import DATA_LABEL, DIRECTORY_NAME, NMF_NAME
from swemper_journal_collection import page_year, nonblank_pages_without_comments

DATA_LABEL_LIST = [{DATA_LABEL: "Svenska Läkartidningen", DIRECTORY_NAME: "pages"}]
TOPIC_MODEL_ALGORITHM = NMF_NAME
STOP_WORD_FILE = "stop_words.txt"
NUMBER_OF_TOPICS = 10
NUMBER_OF_RUNS = 20
OVERLAP_CUT_OFF = 0.6
NR_OF_TOP_DOCUMENTS = 50
MIN_DOCUMENT_FREQUENCY = 10
MAX_DOCUMENT_FREQUENCY = 0.95
STORE_IN_DATABASE = False
READ_FUNCTION = nonblank_pages_without_comments
ADDITIONAL_LABELS_METHOD = page_year
