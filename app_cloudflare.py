from dotenv import dotenv_values
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")

# Load Configuration
IS_TEST = True
config = dotenv_values(".env")

with st.sidebar:
    # Storage API Credential
    CLOUDFLARE_ACCOUNT_ID = (
        st.text_input("Input your Cloudflare Account ID", type="password")
        if IS_TEST == True
        else config["CLOUDFLARE_ACCOUNT_ID"]
    )
    CLOUDFLARE_API_TOKEN = (
        st.text_input("Input your Cloudflare API Token", type="password")
        if IS_TEST == True
        else config["CLOUDFLARE_API_TOKEN"]
    )

    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "케이팝 | k-pop",
            "뽀로로 | ppororo",
            "지브리 | ghibli",
            "디즈니 | disney",
            "피카소 | picaso",
            "판타지 | fantastic",
            "사이버 | cybertic",
        ),
    )

    # Link to Github Repo
    st.markdown("---")
    github_link = (
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_cloudflare.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


def upload_image_to_cloudflare(image_file):
    """Upload Image on Storage Server using Cloudflare Images API"""
    CLOUDFLARE_UPLOAD_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"

    encoder = MultipartEncoder(
        fields={"file": (image_file.name, image_file, "image/jpeg")}
    )

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": encoder.content_type,
    }

    response = requests.post(CLOUDFLARE_UPLOAD_URL, headers=headers, data=encoder)

    if response.status_code == 200:
        return response.json()["result"]["variants"][0]
    else:
        st.error(f"Failed to upload: {response.text}")
        return None


if not CLOUDFLARE_ACCOUNT_ID:
    st.error("Please input your Cloudflare Account ID on the sidebar")
elif not CLOUDFLARE_API_TOKEN:
    st.error("Please input your Cloudflare API Token on the sidebar")
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
            if st.button("Cartoonize your photo!"):
                # Upload Image on Cloudflare Storage
                image_url = None
                with st.spinner("Uploading..."):
                    image_url = upload_image_to_cloudflare(uploaded_file)

                if image_url:
                    st.success("✅ Uploaded!")

                    # Transform Uploaded Image using OpenAI DALL·E API
                    st.write("Transforming...")
                    art_style = selected_style.split(" | ")[1]
                    response = client.images.generate(
                        model="dall-e-3",
                        image=image_url,
                        prompt=f"A cartoon version of this image, high quality, digital art, {art_style} style",
                        n=1,
                        size="1024x1024",
                    )
                    cartoon_url = response["data"][0]["url"]

                    if cartoon_url:
                        st.success("✅ Transformed!")

                        # Show Transformed Image
                        st.image(
                            cartoon_url,
                            caption="Cartoonized Image",
                            use_container_width=True,
                        )
