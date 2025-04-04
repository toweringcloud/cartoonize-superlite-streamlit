from dotenv import dotenv_values
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder
import base64
import io
import openai
import replicate
import requests
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")


with st.sidebar:
    IS_TEST = True
    config = dotenv_values(".env")

    # Generative AI API Credential
    REPLICATE_API_TOKEN = (
        st.text_input("Input your Replicate API Key", type="password")
        if IS_TEST == True
        else config["REPLICATE_API_TOKEN"]
    )

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

    # LLM API Credential
    OPENAI_API_KEY = (
        st.text_input("Input your OpenAI API Key", type="password")
        if IS_TEST == True
        else config["OPENAI_API_KEY"]
    )
    OPENAI_GPT_MODEL = "gpt-4o-mini" if IS_TEST == True else config["OPENAI_GPT_MODEL"]
    OPENAI_LANGUAGE = "Korean" if IS_TEST == True else config["OPENAI_LANGUAGE"]

    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "지브리 | ghibli",
            "디즈니 | disney",
            "뽀로로 | ppororo",
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


def upload_image_to_cloudflare(image_file):
    CLOUDFLARE_VERIFY_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/tokens/verify"
    response = requests.get(
        CLOUDFLARE_VERIFY_URL,
        headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
    )
    print(f"[verify] {response} | {response.text}")

    if response.status_code != 200:
        st.error(f"Failed to verify: {response.text}")
        return None

    CLOUDFLARE_UPLOAD_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
    encoder = MultipartEncoder(
        fields={"file": (image_file.name, image_file, "image/jpeg")}
    )
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": encoder.content_type,
    }
    response = requests.post(CLOUDFLARE_UPLOAD_URL, headers=headers, data=encoder)
    print(f"[upload] {response} | {response.text}")

    if response.status_code == 200:
        return response.json()["result"]["variants"][0]
    else:
        st.error(f"Failed to upload: {response.text}")
        return None


if not REPLICATE_API_TOKEN:
    st.error("Please input your Replicate API Token on the sidebar")
elif not CLOUDFLARE_ACCOUNT_ID:
    st.error("Please input your Cloudflare Account ID on the sidebar")
elif not CLOUDFLARE_API_TOKEN:
    st.error("Please input your Cloudflare API Token on the sidebar")
elif not OPENAI_API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
else:
    # Define Replicate API Client
    replicate.client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    # Define OpenAI API Client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
                            caption="Cartoonized Image",
                            use_container_width=True,
                        )

                        # Generate Summary on Image using LangChain
                        description_prompt = f"Describe this cartoon-style image ({cartoon_url}) briefly in {OPENAI_LANGUAGE}.)"
                        description = client.chat.completions.create(
                            model=OPENAI_GPT_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": description_prompt,
                                }
                            ],
                        )

                        st.success("✅ Described!")
                        st.write(description.choices[0].message.content)

                        # Upload Image on Cloudflare Storage
                        response = requests.get(cartoon_url)
                        if response.status_code == 200:
                            image_data = response.content
                            image_url = None
                            with st.spinner("Uploading..."):
                                image_url = upload_image_to_cloudflare(uploaded_file)
                                print(image_url)

                            if image_url:
                                st.success("✅ Uploaded!")
