from dotenv import dotenv_values
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize C :::",
    page_icon="🎨",
)
st.title("Cartoonize")


# Load Configuration
if "CLOUDFLARE_ACCOUNT_ID" in st.secrets:
    IMAGE_ACCOUNT_ID = st.secrets["CLOUDFLARE_ACCOUNT_ID"]
    IMAGE_API_URL = st.secrets["CLOUDFLARE_API_URL"]
    IMAGE_API_KEY = st.secrets["CLOUDFLARE_API_TOKEN_IMAGES"]
else:
    config = dotenv_values(".env")
    IMAGE_ACCOUNT_ID = config["CLOUDFLARE_ACCOUNT_ID"]
    IMAGE_API_URL = config["CLOUDFLARE_API_URL"]
    IMAGE_API_KEY = config["CLOUDFLARE_API_TOKEN_IMAGES"]


# Handle OAuth Login
st.login()
user = st.experimental_user

if user.is_logged_in:
    st.success(f"✅ Welcome to Cartoonize GPT, {user.name}님!")
    st.write("- User Info:")
    st.json(user.to_dict())
else:
    st.warning("Check your Account!")
    st.stop()

with st.sidebar:
    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "디즈니 | Disney",
            "픽사 | Pixar",
            "지브리 | Studio Ghibli",
            "마블 | Marvel Hero",
            "아이돌 | K-Pop Star",
        ),
    )

    # Link to Github Repo
    st.markdown("---")
    github_link = (
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_cloudflare.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


def upload_image_to_storage(image_file):
    encoder = MultipartEncoder(
        fields={"file": (image_file.name, image_file, "image/jpeg")}
    )
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": encoder.content_type,
    }

    IMAGE_UPLOAD_URL = f"{IMAGE_API_URL}/{IMAGE_ACCOUNT_ID}/images/v1"
    response = requests.post(IMAGE_UPLOAD_URL, headers=headers, data=encoder)

    if response.status_code == 200:
        return response.json()["result"]["variants"][0]
    else:
        st.error(f"Failed to upload: {response.text}")
        return None


if not IMAGE_API_KEY:
    st.error("Please input your Cloudflare API Token on runtime configuration")
else:
    uploaded_file = st.file_uploader("Upload your photo!", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Check File Size (Max 3MB)
        if uploaded_file.size > 3 * 1024 * 1024:
            st.warning("File size exceeds 3MB. Try again.")
        else:
            # Load Original Image
            image = Image.open(uploaded_file)

            # Select Image Rataion
            rotation = st.radio("Image Rotation", ("None", "Left 90", "Right 90"))
            if rotation == "Left 90":
                image = image.rotate(90, expand=True)
            elif rotation == "Right 90":
                image = image.rotate(-90, expand=True)

            #  Show Original Image
            st.image(image, caption="Original Image", use_container_width=True)

            # Action to Cartoonize
            if st.button("Cartoonize"):
                # Upload Image on Cloudflare Storage
                image_url = None
                with st.spinner("Uploading..."):
                    image_url = upload_image_to_storage(uploaded_file)

                if image_url:
                    st.success("✅ Uploaded!")

                    # Transform Uploaded Image using Cloudflare Workers
                    art_style = selected_style.split(" | ")[1]
                    files = {"file": uploaded_file.getvalue(), "style": art_style}

                    with st.spinner("Transforming..."):
                        response = requests.post(
                            "https://cartoonize.toweringcloud.workers.dev", files=files
                        )

                    if response.status_code == 200:
                        result = response.json()
                        cartoon_url = result.get("result", {}).get("variants", [])[0]

                        if cartoon_url:
                            st.success("✅ Transformed!")

                            # Show Transformed Image
                            st.image(
                                cartoon_url,
                                caption=f"{art_style} style of cartoon",
                                use_container_width=True,
                            )
                        else:
                            st.error("Failed to transform...😢")
