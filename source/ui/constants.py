from pathlib import Path

DEFAULT_IMAGE_FORMAT = "png"
ROOT_DIR = Path(__file__).resolve().parent
IMAGE_DIR = ROOT_DIR / "images"
TEMP_DIR = ROOT_DIR / "temp"
WORK_DIR = TEMP_DIR / "work"
ORIGINAL_IMAGE = WORK_DIR / f"original.{DEFAULT_IMAGE_FORMAT}"
CLASS_IMAGE = f"{{}}_{{}}.{DEFAULT_IMAGE_FORMAT}"
IMAGE_CLASSIFICATION_COLUMNS = ["Product Code", "Description", "Quantity"]
INVENTORY_COLUMNS = ["Product Code", "Description", "Quantity"]
INVOICE_COLUMNS = IMAGE_CLASSIFICATION_COLUMNS + ["Unit Price", "Total Price"]
TEMPLATE_IMAGE = WORK_DIR / f"template.{DEFAULT_IMAGE_FORMAT}"
DB_FILE_PATH = ROOT_DIR / "data" / "inventory.db"
LOGGING_FILE = WORK_DIR / "app.log"
#YOLO_MODEL_PATH = ROOT_DIR / "models" / "yolo26n.pt"
YOLO_MODEL_PATH = ROOT_DIR / "models" / "yolo26.pt"

# --- Configuration ---
CHROMA_PATH = ROOT_DIR / "data" / "chroma_db"
CSV_ANNOTS_PATH = ROOT_DIR / "models" / "annotations_train.csv" 
CLASS_NAMES_PATH = ROOT_DIR / "models" / "class_names.csv"
WEIGHTS_PATH = ROOT_DIR / "models" / "simclr_backbone.pth" 

