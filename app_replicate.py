from dotenv import dotenv_values
from PIL import Image
import base64
import io
import replicate
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
    # Generative AI API Credential
    REPLICATE_API_TOKEN = (
        st.text_input("Input your Replicate API Key", type="password")
        if IS_TEST == True
        else config["REPLICATE_API_TOKEN"]
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
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_replicate.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not REPLICATE_API_TOKEN:
    st.error("Please input your Replicate API Token on the sidebar")
else:
    # Define Replicate API Client
    replicate.client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    uploaded_file = st.file_uploader("Upload your photo.", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Check File Size (Max 3MB)
        if uploaded_file.size > 3 * 1024 * 1024:
            st.warning("File size exceeds 3MB. Try again.")
        else:
            # Load Original Image
            image = Image.open(uploaded_file)

            # Select Image Rataion
            rotation = st.radio(
                "Rotate your photo, if necessary.", ("None", "Left 90°", "Right 90°")
            )
            if rotation == "Left 90°":
                image = image.rotate(90, expand=True)
            elif rotation == "Right 90°":
                image = image.rotate(-90, expand=True)

            # Show Original Image
            st.image(image, caption="Original Image", use_container_width=True)

            # Action to Cartoonize
            if st.button("Cartoonize your photo."):
                # Encode Image as Base64
                img_b64 = None
                with st.spinner("Encoding..."):
                    img_io = io.BytesIO()
                    image.save(img_io, format="PNG")
                    img_bytes = img_io.getvalue()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                if img_b64:
                    # Transform Uploaded Image using Replicate API (Stable Diffusion img2img)
                    cartoon_url = None
                    with st.spinner("Transforming..."):
                        art_style = selected_style.split(" | ")[1]
                        output = replicate.run(
                            "stability-ai/stable-diffusion-img2img",
                            input={
                                "image": f"data:image/png;base64,{img_b64}",
                                "prompt": f"A cartoon version of this image, high quality, digital art, {art_style} style",
                                "strength": 0.75,
                                "guidance_scale": 7.5,
                            },
                        )
                        cartoon_url = output[0]

                    if cartoon_url:
                        st.success("✅ Transformed!")

                        # Show Transformed Image
                        st.image(
                            cartoon_url,
                            caption=f"{art_style} style of cartoon",
                            use_container_width=True,
                        )
