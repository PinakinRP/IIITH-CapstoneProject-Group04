import streamlit as st
import pandas as pd
import constants as const
from components.sidebar import render_sidebar
import services.invertory_management_service as ims
import services.image_processing_service as ips
from PIL import Image
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def initialize_session_state():
    # --- Initialize Persistent Variables ---
    if "show_image_dialog" not in st.session_state:
        st.session_state.show_image_dialog = False

    if "dialog_image" not in st.session_state:
        st.session_state.dialog_image = None

    if "dialog_title" not in st.session_state:
        st.session_state.dialog_title = ""

    if "planogram_report" not in st.session_state:
        st.session_state.planogram_report = None

    if "had_shelf_image" not in st.session_state:
        st.session_state.had_shelf_image = False

    if "shelf_image_saved" not in st.session_state:
        st.session_state.shelf_image_saved = False

    if "had_template_image" not in st.session_state:
        st.session_state.had_template_image = False

    if "template_image_saved" not in st.session_state:
        st.session_state.template_image_saved = False

def reset_session_state():
    st.session_state.show_image_dialog = False
    st.session_state.dialog_image = None
    st.session_state.dialog_title = ""
    st.session_state.image_classifications = None
    st.session_state.had_shelf_image = False
    st.session_state.shelf_image_saved = False
    st.session_state.had_template_image = False
    st.session_state.template_image_saved = False

def update_inventory():
    # Update existing inventory
    # product_update_count = ims.update_inventory_for_products(st.session_state.processed_counts)

    # missing_product_codes = [
    #     product_code
    #     for product_code in st.session_state.processed_counts["Product Code"]
    #     if product_update_count.get(product_code, 0) == 0
    # ]

    # if len(missing_product_codes) == 0:
    #     st.session_state.success_message = "Inventory has been updated successfully"
    # else:
    #     st.session_state.upload_shelf_image_warning_message = f"Product code(s) {",".join(missing_product_codes)} not found." 

    # # FORCE FULL CLEANUP: Reset variables & bump key version to destroy widget cache
    # st.session_state.processed_counts = None
    # st.session_state.uploader_key_version += 1
    # st.session_state.trigger_clean_rerun = True
    # st.session_state.boxed_image = None
    pass

@st.dialog("Image Preview", width="large")
def show_image_dialog():
    st.subheader(st.session_state.dialog_title)
    image = st.session_state.dialog_image
    st.image(image, width="stretch")

def render_styles():
    st.markdown("""
    <style>

    .block-container{
        padding-top:1.2rem;
        padding-bottom:2rem;
        max-width:1400px;
    }

    /* Card */
    .card{
        background:white;
        border:1px solid #E5E7EB;
        border-radius:12px;
        padding:18px;
        margin-bottom:18px;
        box-shadow:0 1px 3px rgba(0,0,0,.08);
    }

    /* Section title */
    .section-title{
        font-size:20px;
        font-weight:700;
        margin-bottom:15px;
    }

    /* Image title */
    .image-title{
        font-size:18px;
        font-weight:600;
        margin-bottom:10px;
    }

    /* Expand icon */
    .expand-icon{
        float:right;
        color:#6b7280;
        font-size:22px;
    }

    /* Upload card spacing */
    .upload-row{
        padding-top:5px;
    }

    .product-chip{
        border:1px solid #E5E7EB;
        border-radius:12px;
        padding:16px 10px;
        text-align:center;
        background:white;
        transition:.2s;
    }

    .product-chip:hover{
        border-color:#16a34a;
        box-shadow:0 2px 8px rgba(0,0,0,.08);
    }

    .product-name{
        font-size:15px;
        font-weight:600;
    }

    .product-count{
        color:#16a34a;
        font-size:28px;
        font-weight:700;
        margin-top:6px;
    }

    div.stButton > button {
        background-color: #A4E9FF;
        border-color: #A4E9FF;
    }            

    div.stButton > button:hover {
        background-color: #A4E9FF;
        border-color: #A4E9FF;
    } 
                
    div.stButton > button p {
        color: #1A1A1A;
    }
    </style>
    """, unsafe_allow_html=True)

def save_file(file_contents, save_file_name):
    upload_dir = Path(save_file_name).parent
    upload_dir.mkdir(exist_ok=True)
    with open(save_file_name, "wb") as f:
        f.write(file_contents.getbuffer())

def reset_screen():
    reset_session_state()
    st.rerun()

def run_compliance_report():
    if "planogram_report" not in st.session_state or st.session_state.planogram_report is None:
        st.session_state.planogram_report = ips.generate_planogram_report()

def render_compliance_report():
    if "planogram_report" in st.session_state and st.session_state.planogram_report is not None:
        st.subheader("Planogram Report")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="✅ Matched Items",
                value=st.session_state.planogram_report.matched_items
            )
        with col2:
            st.metric(
                label="❌ Missing Items",
                value=st.session_state.planogram_report.missing_items
            )
        with col3:
            st.metric(
                label="➕ Extra Items",
                value=st.session_state.planogram_report.extra_items
            )

        annotated_image = Image.open(st.session_state.planogram_report.annotated_imagefullname) if st.session_state.planogram_report.annotated_imagefullname is not None else None
        if annotated_image is not None:
            st.image(
                annotated_image,
                use_container_width=True
            )
        else:
            st.info("Empty image")
        

def render_uploadfile_section():
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown(
                "<div class='image-title'>Shelf Image</div>",
                unsafe_allow_html=True
            )
            shelf_image = st.file_uploader(
                "",
                type=["png","jpg","jpeg"],
                key="shelf_image"
            )
            if shelf_image is None and st.session_state.had_shelf_image:
                st.session_state.had_shelf_image = False
                reset_screen()
            elif shelf_image is not None:
                try:
                    st.image(
                        shelf_image,
                        use_container_width=True
                    )
                    if not st.session_state.shelf_image_saved:
                        save_file(shelf_image, const.ORIGINAL_IMAGE)
                        #shelf_image.save(const.ANNOTATED_IMAGE)
                        st.session_state.shelf_image_saved = True
                except Exception:
                    raise
                    st.error("Failed to load image.")
                if not st.session_state.had_shelf_image:
                    st.session_state.had_shelf_image = True
    with right:
        with st.container(border=True):
            st.markdown(
                "<div class='image-title'>Template Image</div>",
                unsafe_allow_html=True
            )
            template_image = st.file_uploader(
                "",
                type=["png","jpg","jpeg"],
                key="template_image"
            )
            if template_image is None and st.session_state.had_template_image:
                st.session_state.had_template_image = False
                reset_screen()
            elif template_image is not None:
                try:
                    st.image(
                        template_image,
                        use_container_width=True
                    )
                    if not st.session_state.template_image_saved:
                        save_file(template_image, const.TEMPLATE_IMAGE)
                        st.session_state.template_image_saved = True
                except Exception:
                    st.error("Failed to load image.")
                if not st.session_state.had_template_image:
                    st.session_state.had_template_image = True

def render_button():
    if st.session_state.shelf_image is not None and st.session_state.template_image is not None:
        if st.button("🧩 Check Compliance", use_container_width=True, key="check-compliance"):
            run_compliance_report()
            render_compliance_report()

def render_page():
    # pass
    initialize_session_state()
    
    st.set_page_config(
        page_title="Check Planogram Compliance",
        page_icon="🧩",
        layout="wide"
    )

    render_sidebar()

    render_styles() 

    #st.title("🛒 Product Detection & Classification")
    col1, col2 = st.columns([1, 11])
    with col1:
        st.image(
            str(const.IMAGE_DIR / "planogram-compliance.png"), 
            use_container_width=True
        )
    with col2:
        st.header("Check Planogram Compliance")

    render_uploadfile_section() 
    render_button()

if __name__ == "__main__":
    render_page()
