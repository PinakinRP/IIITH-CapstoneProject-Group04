class ImageClassifications():
    original_imagefullname: str
    annotated_imagefullname: str
    item_details: list[dict]
    class_imagefullnames: dict
    
    def __init__(self):
        self.original_imagefullname = None
        self.annotated_imagefullname = None
        self.item_details = []
        self.class_imagefullnames = {}

