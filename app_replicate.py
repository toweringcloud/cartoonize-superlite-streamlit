from dotenv import dotenv_values
from PIL import Image
import base64
import io
import openai
import replicate
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

    # LLM API Credential
    REPLICATE_API_TOKEN = (
        st.text_input("Input your Replicate API Key", type="password")
        if IS_TEST == True
        else config["REPLICATE_API_TOKEN"]
    )

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


if not REPLICATE_API_TOKEN:
    st.error("Please input your API Key on the sidebar")
else:
    # Define Replicate API Client
    replicate.client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    # Define OpenAI API Client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

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

            # Show Original Image
            st.image(image, caption="Original Image", use_container_width=True)

            # Action to Cartoonize
            if st.button("Cartoonize your photo!"):
                # Encode Image as Base64
                img_b64 = None
                with st.spinner("Encoding..."):
                    img_io = io.BytesIO()
                    image.save(img_io, format="PNG")
                    img_bytes = img_io.getvalue()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                if img_b64:
                    st.success("✅ Encoded!")

                    # Transform Uploaded Image using Replicate API (Stable Diffusion img2img)
                    st.write("Transforming...")
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
                        description_prompt = f"Describe this cartoon-style image (URL: {cartoon_url}) briefly in {OPENAI_LANGUAGE}.)"
                        description = client.chat.completions.create(
                            model=OPENAI_GPT_MODEL,
                            messages=[
                                {"role": "system", "content": description_prompt}
                            ],
                        )

                        st.success("✅ Described on Cartoonized Image!")
                        st.write(description["choices"][0]["message"]["content"])
