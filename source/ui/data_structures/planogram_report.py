class PlanogramReport():
    annotated_imagefullname: str
    matched_items:int
    missing_items:int
    extra_items:int

    def __init__(self):
        self.annotated_imagefullname = None
        self.matched_items = 0
        self.missing_items = 0
        self.extra_items = 0

