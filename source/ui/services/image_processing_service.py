from io import BytesIO
from collections import Counter
from PIL import Image
from ultralytics import YOLO


def get_product_counts_boxed_image(image_bytes: BytesIO) -> tuple[BytesIO, dict]:
    image = Image.open(image_bytes)

    model = YOLO("yolo26s.pt")
    results = model(image)

    result = results[0]
    class_ids = result.boxes.cls.cpu().numpy().astype(int)

    # Generate image with bounding boxes (NumPy array)
    annotated_img = result.plot()

    # Convert NumPy array to PIL Image
    annotated_img = Image.fromarray(annotated_img)

    # Convert PIL Image to BytesIO
    annotated_img_bytes = BytesIO()
    annotated_img.save(annotated_img_bytes, format="PNG")
    annotated_img_bytes.seek(0)

    counts = Counter(class_ids)

    return annotated_img_bytes, {
        model.names[class_id]: count
        for class_id, count in counts.items()
    }
