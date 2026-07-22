from io import BytesIO
import constants as const
from PIL import Image
from ultralytics import YOLO
from data_structures.image_classifications import ImageClassifications
from data_structures.planogram_report import PlanogramReport
import os

import pandas as pd
import numpy as np
import os
from pathlib import Path
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
import chromadb
import cv2
import streamlit as st
from services.logging_service import Logger

@st.cache_data(show_spinner=False)
def load_class_names():
    if os.path.exists(const.CLASS_NAMES_PATH):
        df = pd.read_csv(const.CLASS_NAMES_PATH)
        return df
    else:
        raise Exception(f"Class names file not found at {const.CLASS_NAMES_PATH}")

def write_trace(trace_message:str, is_warning:bool = False):
    message = trace_message if not is_warning else f"WARNING: {trace_message}"
    print(message)

@st.cache_data(show_spinner=False)
def load_annotations():
    if os.path.exists(const.CSV_ANNOTS_PATH):
        df = pd.read_csv(const.CSV_ANNOTS_PATH)
        return df
    else:
        raise Exception(f"Annotations file not found at {const.CSV_ANNOTS_PATH}")

@st.cache_resource(show_spinner=False)
def get_chroma_collection():
    client = chromadb.PersistentClient(path=const.CHROMA_PATH)
    try:
        collection = client.get_collection("simclr_crop_embeds")
        return collection
    except Exception as e:
        raise Exception(f"Error loading ChromaDB collection: {e}. Please ensure the ChromaDB is properly initialized.")

@st.cache_resource(show_spinner=False)
def get_annotation_model() -> YOLO:
    Logger.debug("Loading annotation model...")
    return YOLO(const.YOLO_MODEL_PATH)

def process_crops_for_streamlit(uploaded_image_pil):
    crop_data = []
    yolo_model = get_annotation_model()
    Logger.debug("Loaded annotation model.")
    Logger.debug("Processing image through annotation model...")
    yolo_results = yolo_model(uploaded_image_pil, imgsz=1024)
    Logger.debug("Annotation model processed the image.")
    yolo_result = yolo_results[0]
    boxes = yolo_result.boxes.xyxy.cpu().numpy()
    Logger.debug(f"Found {len(boxes)} boxes.")
    for idx, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)

        try:
            crop = uploaded_image_pil.crop((x1, y1, x2, y2))
            crop_id = f"{Path(const.ORIGINAL_IMAGE).stem}_bbox_{idx}"

            crop_data.append(
                {
                    "id": crop_id,
                    "source_image": const.ORIGINAL_IMAGE,
                    "crop_pil": crop, # Store PIL image directly
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                }
            )
        except Exception as e:
            raise Exception(f"Error processing crop {idx} from {const.ORIGINAL_IMAGE}: {e}")
    Logger.debug("Completed image cropping.")
    return pd.DataFrame(crop_data)


@st.cache_resource(show_spinner=False)
def load_model_and_transforms():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load the trained simclr backbone
    base_resnet = resnet50() # Initialize ResNet with default weights first
    encoder_model = torch.nn.Sequential(*list(base_resnet.children())[:-1])
    if os.path.exists(const.WEIGHTS_PATH):
        try:
            encoder_model.load_state_dict(torch.load(const.WEIGHTS_PATH, map_location=device))
            Logger.info(f"Loaded custom weights") #from {WEIGHTS_PATH}")
        except Exception as e:
            raise Exception(f"Error loading model weights: {e}. Using baseline weights.")
    else:
        #st.warning(f"No custom checkpoint found at {const.WEIGHTS_PATH}. Executing using baseline weights.")
        raise Exception(f"No custom checkpoint found at {const.WEIGHTS_PATH}. Executing using baseline weights.")

    encoder_model.to(device).eval() # Set to evaluation mode

    inference_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return encoder_model, inference_transform, device


def get_embedding_resnet(input_img, encoder, inference_transform, device):
    if encoder is None or inference_transform is None or device is None:
        raise Exception("Model or transforms not loaded. Cannot generate embeddings.")

    if isinstance(input_img, np.ndarray):
        rgb_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
    elif isinstance(input_img, Image.Image):
        pil_img = input_img.convert("RGB")
    else:
        raise TypeError("Input image must be a numpy array (from cv2) or a PIL Image.")

    tensor_input = inference_transform(pil_img).unsqueeze(0).to(device)

    with torch.no_grad():
        features = encoder(tensor_input).flatten(1)
        normalized_vector = torch.nn.functional.normalize(features, p=2, dim=1)
        vector_np = normalized_vector.cpu().numpy().flatten()
    return vector_np

def draw_boxes_on_image(image_pil, df_crops_with_predictions, df_classnames_map):
    # Convert PIL Image to OpenCV format for drawing
    img_np = np.array(image_pil.convert("RGB"))
    img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    print(f"image_pil.width = {image_pil.width}")
    for idx, row in df_crops_with_predictions.iterrows():
        x1, y1, x2, y2 = int(row['x1']), int(row['y1']), int(row['x2']), int(row['y2'])
        predicted_class_id = row['predicted_class_id']

        color = (0, 255, 0) # Green BGR
        text_color = (0, 0, 255) # Red BGR

        cv2.rectangle(img_cv2, (x1, y1), (x2, y2), color, 4)
        if predicted_class_id is not None:
            text = f"C{predicted_class_id}"
            # Adjust font scale and thickness based on image size if necessary
            font_scale = 0.8 * (image_pil.width / 1000) # dynamic scaling, reduced from 1.0
            font_thickness = max(1, int(3 * (image_pil.width / 1000)))
            cv2.putText(img_cv2, text, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness)

    # Convert back to PIL Image for Streamlit display
    return Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))

def classify_image(image_bytes: BytesIO, file_name:str) -> ImageClassifications:
    result = ImageClassifications()

    image = Image.open(image_bytes)
    
    os.makedirs(const.WORK_DIR, exist_ok=True)

    image.save(const.ORIGINAL_IMAGE, format=const.DEFAULT_IMAGE_FORMAT)

    result.original_imagefullname = const.ORIGINAL_IMAGE
    
    #**************************************
    original_image_pil = Image.open(image_bytes).convert("RGB")
    #df_annots_global = load_annotations()
    df_classnames = load_class_names()
    #df_annotations_for_this_image = df_annots_global[df_annots_global['image'] == file_name]
    
    # if df_annotations_for_this_image.empty:
    #     #display st msg
    #     raise Exception(f"No annotations found for '{file_name}' in the dataset. Please upload an image only from the given subset.")
    # else:
    # Step 1: Extract crops
    df_test_crops_streamlit = process_crops_for_streamlit(original_image_pil)

    collection = get_chroma_collection()
    
    annotated_image = None
    df_display_table = None
    
    if not df_test_crops_streamlit.empty:
        #display st msg
        Logger.info(f"Extracted {len(df_test_crops_streamlit)} product crops.")
        # Step 2: recognizing the extracted crops
        Logger.info("Analysing the products...")
        encoder, inference_transform, device = load_model_and_transforms()
        embeddings_test_list = []
        for _, row in df_test_crops_streamlit.iterrows():
            if row['crop_pil'] is not None: # Ensure crop_pil is not None
                embedding = get_embedding_resnet(row['crop_pil'], encoder, inference_transform, device)
                if embedding is not None:
                    embeddings_test_list.append(embedding.tolist())
                else:
                    embeddings_test_list.append(None) # Handle cases where embedding generation failed
            else:
                embeddings_test_list.append(None)

        df_test_crops_streamlit['embeddings'] = embeddings_test_list

        # Filter out crops where embedding generation might have failed
        df_test_crops_streamlit = df_test_crops_streamlit.dropna(subset=['embeddings'])
        
        if not df_test_crops_streamlit.empty and collection is not None:
            Logger.info("Classifying the products...")
            # Ensure embeddings are in correct format for query
            query_embeddings_for_db = [emb for emb in df_test_crops_streamlit['embeddings'] if emb is not None]

            if query_embeddings_for_db:
                query_results = collection.query(
                    query_embeddings=query_embeddings_for_db,
                    n_results=1,
                    include=['metadatas']
                )

                predicted_class_ids = []
                for metadata_list in query_results['metadatas']:
                    if metadata_list: # Ensure there is a match
                        predicted_class_id = metadata_list[0].get('class_id')
                        predicted_class_ids.append(predicted_class_id)
                    else:
                        predicted_class_ids.append(None) # No match found

                df_test_crops_streamlit['predicted_class_id'] = predicted_class_ids
                df_test_crops_streamlit = df_test_crops_streamlit.dropna(subset=['predicted_class_id']) # Remove crops without a prediction
                df_test_crops_streamlit['predicted_class_id'] = df_test_crops_streamlit['predicted_class_id'].astype(int)
                
                if not df_test_crops_streamlit.empty:
                    annotated_image = draw_boxes_on_image(original_image_pil, df_test_crops_streamlit, df_classnames)
                
                    df_display_table = pd.merge(
                            df_test_crops_streamlit.groupby('predicted_class_id').size().reset_index(name='Product Count'),
                            df_classnames,
                            left_on='predicted_class_id',
                            right_on='cluster_id',
                            how='left'
                        )
                    df_display_table = df_display_table[['cluster_id', 'cluster_name', 'Product Count']]
                    df_display_table.columns = ['Class ID', 'Class Name', 'Product Count']
                else:
                    Logger.warning("No product classifications were obtained. This might indicate that no matching products were found or the products are unknown.", True)
            else:
                Logger.warning("Products are not recognized.")
            
        else:
            if collection is None:
                raise Exception("Database is not available. Please check the DB setup.")
            else:
                Logger.warning("No products are recognized from the image.")
    else:
        Logger.warning("Image is unidentified / Not known to model.")
            
    result.annotated_image = annotated_image
    result.item_details = []

    if df_display_table is not None and not df_display_table.empty:
        for _, row in df_display_table.iterrows():
            dict_data = {
                const.IMAGE_CLASSIFICATION_COLUMNS[0]: str(row['Class ID']),
                const.IMAGE_CLASSIFICATION_COLUMNS[1]: row['Class Name'],
                const.IMAGE_CLASSIFICATION_COLUMNS[2]: row['Product Count']
            }
            result.item_details.append(dict_data)

    if df_test_crops_streamlit is not None and not df_test_crops_streamlit.empty:
        class_images = (
            df_test_crops_streamlit.groupby('predicted_class_id')['crop_pil']
            .apply(list)
            .to_dict()
        )
        result.class_images = {str(k): v for k, v in class_images.items()}

    '''yolo_model = YOLO("yolo26s.pt")
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

            if class_name not in result.class_images:
                result.class_images[class_name] = []
            result.class_images[class_name].append(filename)'''
    return result

def generate_planogram_report() -> PlanogramReport:
    result = PlanogramReport()
    ## TODO: Run planogram.
    result.annotated_imagefullname = const.ANNOTATED_IMAGE
    result.matched_items = 3
    result.missing_items = 2
    result.extra_items = 1
    return result
