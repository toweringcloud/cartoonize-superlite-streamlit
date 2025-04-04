from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from dotenv import dotenv_values
from PIL import Image
import openai
import streamlit as st
import torch


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
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_diffusers.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not OPENAI_API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
else:
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

            #  Show Original Image
            st.image(image, caption="Original Image", use_container_width=True)

            # Action to Cartoonize
            if st.button("Cartoonize your photo."):
                # Transform Uploaded Image using OpenAI DALL·E API
                cartoon_url = None
                with st.spinner("Transforming..."):
                    # Load ControlNet Model
                    controlnet = ControlNetModel.from_pretrained(
                        "lllyasviel/control_v11f1e_sd15_tile"
                    )

                    # Setup Stable Diffusion Pipeline
                    pipe = StableDiffusionControlNetPipeline.from_pretrained(
                        "runwayml/stable-diffusion-v1-5",
                        controlnet=controlnet,
                        torch_dtype=torch.float16,
                    ).to("cuda")

                    # Run Transformation with Prompt
                    art_style = selected_style.split(" | ")[1]
                    prompt = (f"high quality, {art_style} cartoon style",)
                    cartoon_url = pipe(prompt=prompt, image=image).images[0]

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
                        messages=[{"role": "system", "content": description_prompt}],
                    )

                    st.success("✅ Described!")
                    st.write(description.choices[0].message.content)
