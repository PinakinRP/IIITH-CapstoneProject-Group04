from io import BytesIO
import constants as const
from PIL import Image
from ultralytics import YOLO
from data_structures.image_classifications import ImageClassifications
from data_structures.planogram_report import PlanogramReport
import os

def classify_image(image_bytes: BytesIO) -> ImageClassifications:
    result = ImageClassifications()

    image = Image.open(image_bytes)
    
    os.makedirs(const.WORK_DIR, exist_ok=True)

    image.save(const.ORIGINAL_IMAGE, format=const.DEFAULT_IMAGE_FORMAT)

    result.original_imagefullname = const.ORIGINAL_IMAGE

    yolo_model = YOLO("yolo26s.pt")
    yolo_results = yolo_model(image)

    # Generate image with bounding boxes (NumPy array)
    annotated_img = yolo_results[0].plot()

    # Convert NumPy array to PIL Image
    annotated_img = Image.fromarray(annotated_img)

    # Convert PIL Image to BytesIO
    annotated_img.save(const.ANNOTATED_IMAGE, format=const.DEFAULT_IMAGE_FORMAT)

    result.annotated_imagefullname = const.ANNOTATED_IMAGE

    result.item_details = []

    for yolo_result in yolo_results:
        names = yolo_result.names
        for box in yolo_result.boxes:
            class_name = names[int(box.cls[0])]
            # Increment index for this class
            item_detail = next(
                (itd for itd in result.item_details if itd[const.IMAGE_CLASSIFICATION_COLUMNS[0]] == class_name),
                None
            )
            if item_detail is None:
                item_detail = {
                    const.IMAGE_CLASSIFICATION_COLUMNS[0]: class_name,
                    const.IMAGE_CLASSIFICATION_COLUMNS[1]: class_name,
                    const.IMAGE_CLASSIFICATION_COLUMNS[2]: 1
                }
                result.item_details.append(item_detail)
            else:
                item_detail[const.IMAGE_CLASSIFICATION_COLUMNS[2]] += 1
            
            # Bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Crop image
            cropped = image.crop((x1, y1, x2, y2))

            # Save image
            filename = const.WORK_DIR / const.CLASS_IMAGE.format(class_name, item_detail[const.IMAGE_CLASSIFICATION_COLUMNS[2]])
            cropped.save(filename)

            if class_name not in result.class_imagefullnames:
                result.class_imagefullnames[class_name] = []
            result.class_imagefullnames[class_name].append(filename)

    return result

def generate_planogram_report() -> PlanogramReport:
    result = PlanogramReport()
    ## TODO: Run planogram.
    result.annotated_imagefullname = const.ANNOTATED_IMAGE
    result.matched_items = 3
    result.missing_items = 2
    result.extra_items = 1
    return result
