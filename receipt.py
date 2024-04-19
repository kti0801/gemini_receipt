import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
generation_config = {
    "temperature": 0.3,
    "max_output_tokens": 2048,
    "top_k": 10,
    "top_p": 0.5,
}
model_vision = genai.GenerativeModel(
    model_name='gemini-pro-vision',
    generation_config=generation_config,
)

model_text = genai.GenerativeModel(
    model_name='gemini-pro',
    generation_config=generation_config,
)


if not 'picture' in st.session_state:
    st.session_state.picture = None

if st.session_state.picture is None:
    # picture_cam = st.camera_input("Take a picture")
    # if picture_cam:
    #     st.session_state.picture = Image.open(picture_cam)
    #     st.rerun()
    picture_upload = st.file_uploader("Upload a picture", ['png', 'jpg', 'jpeg'], accept_multiple_files=False)
    if picture_upload:
        st.session_state.picture = Image.open(picture_upload)
        st.rerun()
else:
    st.image(st.session_state.picture)
    prompt = [
"""Extract information from the receipt in the image.
Write in JSON format with the following keys.
Do not infer or calculate, just extract.

**Information (Keys)**:
- Store Info (string)
- DateTime (YYYY-MM-DD HH:MM:SS)
- Items
    - Name
    - Quantity (integer)
    - Amount (float)
- Total Amount (float)

**Image**:""",
        st.session_state.picture,
        "\n\n**JSON**:\n",
    ]

    response = model_vision.generate_content(prompt)
    info = json.loads(response.text.replace("```json", "").replace("```", ""))
    st.write(
f"""- **Store**: {info.get("Store Info", "No Info.")}
- **Date**: {info.get("DateTime", "No Info.")}
- **Total Amount**: {info.get("Total Amount", "No Info.")}""")
    items_df = pd.DataFrame(info.get("Items"))
    st.dataframe(items_df)

    st.divider()
    condition = ''
    if (items_df['Amount'].astype(float) <= 10000).all():
        condition += '가격이 10,000을 초과하는 항목이 없음.'
        st.write(":white_check_mark: 각 항목의 가격이 10,000원을 초과하지 않음.")
    else:
        condition += '가격이 10,000을 초과하는 항목이 있음.'
        st.write(":x: 가격이 10,000을 초과하는 항목이 있음.")
    if float(info.get('Total Amount', 0)) <= 100000:
        condition += '가격의 총 합이 100,000을 초과하지 않음.'
        st.write(":white_check_mark: 가격의 총 합이 10,000원을 초과하지 않음.")
    else:
        condition += '가격의 총 합이 100,000을 초과.'
        st.write(":x: 가격의 총 합이 100,000을 초과.")

    st.divider()
    prompt = f"""다음의 정보를 바탕으로 사용자가 규정을 위반 했는지 안내하라. 규정위반이 있다면 모든 규정위반에 대해 자세히 설명하라.
**JSON**: {response.text}

**규정 위반 여부**: {condition}

**안내**:
"""
    response = model_text.generate_content(prompt)
    st.write(response.text)