from io import BytesIO

class ImageClassifications():
    annotated_image: BytesIO
    item_details: list[dict]
    class_images: dict
    
    def __init__(self):
        self.annotated_image = None
        self.item_details = []
        self.class_images = {}

