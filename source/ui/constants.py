from pathlib import Path

DEFAULT_IMAGE_FORMAT = "png"
ROOT_DIR = Path(_file_).resolve().parent
IMAGE_DIR = ROOT_DIR / "images"
TEMP_DIR = ROOT_DIR / "temp"
WORK_DIR = TEMP_DIR / "work"
ANNOTATED_IMAGE = WORK_DIR / f"annotated.{DEFAULT_IMAGE_FORMAT}"
ORIGINAL_IMAGE = WORK_DIR / f"original.{DEFAULT_IMAGE_FORMAT}"
CLASS_IMAGE = f"{{}}_{{}}.{DEFAULT_IMAGE_FORMAT}"
IMAGE_CLASSIFICATION_COLUMNS = ["Product Code", "Description", "Quantity"]
INVENTORY_COLUMNS = ["Product Code", "Description", "Quantity"]
TEMPLATE_IMAGE = WORK_DIR / f"template.{DEFAULT_IMAGE_FORMAT}"
DB_FILE_PATH = ROOT_DIR / "data" / "inventory.db"

# --- Configuration ---
CHROMA_PATH = "/content/chroma_db"
CSV_ANNOTS_PATH = "/content/annotations_train.csv" 
CLASS_NAMES_PATH = "/content/class_names.csv"
WEIGHTS_PATH = "/content/simclr_backbone.pth" 

