import streamlit as st
import pandas as pd
import constants as const
from components.sidebar import render_sidebar
import services.invertory_management_service as ims
import services.image_processing_service as ips
from PIL import Image
from st_aggrid import AgGrid, GridOptionsBuilder

def initialize_session_state():
    # --- Initialize Persistent Variables ---
    if "show_image_dialog" not in st.session_state:
        st.session_state.show_image_dialog = False

    if "dialog_image" not in st.session_state:
        st.session_state.dialog_image = None

    if "dialog_title" not in st.session_state:
        st.session_state.dialog_title = ""

    if "image_classifications" not in st.session_state:
        st.session_state.image_classifications = None

    if "had_file" not in st.session_state:
        st.session_state.had_file = False

    if "update_status" not in st.session_state:
        st.session_state.update_status = 0

    if "file_upload_version" not in st.session_state:
        st.session_state.file_upload_version = 0

def reset_session_state():
    st.session_state.file_selected = None
    st.session_state.show_image_dialog = False
    st.session_state.dialog_image = None
    st.session_state.dialog_title = ""
    st.session_state.image_classifications = None
    st.session_state.had_file = False
    st.session_state.file_upload_version += 1

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

def reset_screen():
    reset_session_state()
    st.rerun() 

def render_images():
    col1,col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(
                "<div class='image-title'>Shelf Image</div>",
                unsafe_allow_html=True
            )
            uploaded_file = st.file_uploader(
                "",
                type=["png","jpg","jpeg"],
                key=f"file_selected{st.session_state.file_upload_version}"
            )
            if uploaded_file is None and st.session_state.had_file:
                st.session_state.had_file = False
                reset_screen()
            if uploaded_file is not None:
                if not st.session_state.had_file:
                    st.session_state.had_file = True
                st.image(
                    uploaded_file,
                    use_container_width=True
                )
    with col2:
        if st.session_state.had_file:
            with st.container(border=True):
                st.markdown(
                    "<div class='image-title'>Scanned Image</div>",
                    unsafe_allow_html=True
                )
                st.markdown("")
                st.markdown("")
                if uploaded_file:
                    st.button(
                        "🔍 Scan Shelf Image",
                        use_container_width=True,
                        type="primary",
                        key="process_image"
                    )
                    st.markdown("")
                    if st.session_state.process_image:
                        file_selected = st.session_state[f"file_selected{st.session_state.file_upload_version}"]
                        # Trigger image calculation only if results are not stored yet
                        if file_selected is not None and st.session_state.image_classifications is None:
                            with st.spinner("Scanning shelf image..."):
                                st.session_state.image_classifications = ips.classify_image(file_selected)
                                st.rerun() # Refresh to populate layout grids smoothly
                    if st.session_state.image_classifications is not None:
                        try:
                            annotated_img = Image.open(st.session_state.image_classifications.annotated_imagefullname)
                        except:
                            annotated_img = None
                        if annotated_img is not None:
                            st.image(
                                annotated_img,
                                use_container_width=True
                            )

def render_save_button():
    if "image_classifications" in st.session_state and st.session_state.image_classifications is not None and st.session_state.image_classifications.item_details is not None:
        if st.button("💾 Update Inventory", use_container_width=True):
            with st.spinner("Updating the inventory..."):
                try:
                    ims.update_inventory(pd.DataFrame(st.session_state.image_classifications.item_details))
                    st.session_state.update_status = 1
                    reset_screen()
                except Exception:
                    st.session_state.update_status = 2
    if "update_status" in st.session_state and st.session_state.update_status != 0:
        if st.session_state.update_status == 1:
            st.toast("Inventory updated successfully.", icon="✅")
        elif st.session_state.update_status == 2:
            st.toast("Inventory update failed.", icon="❌")
        st.session_state.update_status = 0

def render_product_by_class_section():

    if "image_classifications" in st.session_state and st.session_state.image_classifications is not None:
        data = pd.DataFrame(st.session_state.image_classifications.item_details)

        if data is not None and not data.empty:
            total_quantity = data[const.IMAGE_CLASSIFICATION_COLUMNS[2]].sum()
            total_products = data[const.IMAGE_CLASSIFICATION_COLUMNS[0]].nunique()
        
            st.write("")
        
            if "selected_class" not in st.session_state:
                st.session_state.selected_class = list(data)[0]
            
            st.subheader("Shelf Contents")
            
            section_left_col, section_right_col = st.columns(2)
            with section_left_col:
                m1, m2 = st.columns(2)
                with m1:
                    st.metric(
                        label="🏷️ Total Products",
                        value=total_products
                    )
                    
                with m2:
                    st.metric(
                        label="📦 Total Quantity",
                        value=total_quantity
                    )

                gb = GridOptionsBuilder.from_dataframe(data)
                gb.configure_default_column(
                    sortable=True,
                    filter=True,
                    resizable=True,
                )
                gb.configure_selection(
                    selection_mode="disabled",
                    use_checkbox=False
                )
                gb.configure_grid_options(
                    rowSelection="disabled",
                    suppressRowClickSelection=False
                )
                
                grid_response = AgGrid(
                    data,
                    gridOptions=gb.build(),
                    fit_columns_on_grid_load=True,
                    height=450
                )

                selected_rows = grid_response["selected_rows"]

                if selected_rows is not None and len(selected_rows):
                    st.session_state.selected_class = selected_rows.iloc[0][const.IMAGE_CLASSIFICATION_COLUMNS[0]]
            
            with section_right_col:
                part_1, part_2 = st.columns([3,1])
                with part_1:
                    st.text("Product Code")
                    selected_class = st.selectbox(
                        "Select Product Code",
                        data[const.IMAGE_CLASSIFICATION_COLUMNS[0]].tolist(),
                        label_visibility="collapsed",
                        key="selected_class"
                    )
                with part_2:
                    quantity = data.loc[
                        data[const.IMAGE_CLASSIFICATION_COLUMNS[0]] == selected_class,
                        const.IMAGE_CLASSIFICATION_COLUMNS[2]
                    ].iloc[0]
                    st.metric("Quantity", quantity)

                gallery = st.container(
                    height=445,
                    border=True
                )

                with gallery:
                    images = []
                    if st.session_state.image_classifications.class_imagefullnames is not None and selected_class in st.session_state.image_classifications.class_imagefullnames:
                        images = st.session_state.image_classifications.class_imagefullnames[selected_class]
                    COLS = 3
                    index = 0
                    for i in range(0, len(images), COLS):
                        st.markdown(" ")
                        st.markdown(" ")
                        cols = st.columns(COLS)
                        for col, img in zip(cols, images[i:i+COLS]):
                            with col:
                                try:
                                    inner_col1, inner_col2 = st.columns([6,1])
                                    with inner_col1:
                                        image = Image.open(img)
                                        st.image(
                                            image,
                                            use_container_width=True
                                        )
                                    # with inner_col2:
                                    #     if st.button(
                                    #         "⛶",
                                    #         key=f"expand_{index}",
                                    #         help="View full size"
                                    #     ):
                                    #         st.session_state.dialog_title = f"{st.session_state.selected_class} {index}"
                                    #         st.session_state.dialog_image = image
                                    #         show_image_dialog()
                                except:
                                    st.info("No Image")
                        index += 1

def render_page():
    # pass
    initialize_session_state()
    
    st.set_page_config(
        page_title="Update Inventory",
        page_icon="📷",
        layout="wide"
    )

    render_sidebar()

    render_styles() 

    #st.title("🛒 Product Detection & Classification")
    col1, col2 = st.columns([1, 11])
    with col1:
        st.image(
            str(const.IMAGE_DIR / "upload-shelf-image.png"), 
            use_container_width=True
        )
    with col2:
        st.header("Update Inventory")

    render_images()
    render_product_by_class_section()  
    render_save_button() 

if __name__ == "__main__":
    render_page()
