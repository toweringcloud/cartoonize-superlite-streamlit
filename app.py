from dotenv import dotenv_values
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder
import openai
import streamlit as st
import replicate
import requests


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize :::",
    page_icon="🎨",
)
st.title("Cartoonize")


# Load Configuration
if "CUSTOM_LOGIN_ID" in st.secrets:
    LOGIN_ID = st.secrets["CUSTOM_LOGIN_ID"]
    LOGIN_PW = st.secrets["CUSTOM_LOGIN_PW"]
    IMAGE_ACCOUNT_ID = st.secrets["CLOUDFLARE_ACCOUNT_ID"]
    IMAGE_API_URL = st.secrets["CLOUDFLARE_API_URL"]
    IMAGE_API_KEY = st.secrets["CLOUDFLARE_API_TOKEN_IMAGES"]
    GPT_API_KEY = st.secrets["REPLICATE_API_TOKEN"]
    GPT_MODEL = st.secrets["REPLICATE_MODEL_DRAW"]
    GPT_API_KEY2 = st.secrets["OPENAI_API_KEY"]
    GPT_MODEL2 = st.secrets["OPENAI_MODEL_DRAW"]
else:
    config = dotenv_values(".env")
    LOGIN_ID = config["CUSTOM_LOGIN_ID"]
    LOGIN_PW = config["CUSTOM_LOGIN_PW"]
    IMAGE_ACCOUNT_ID = config["CLOUDFLARE_ACCOUNT_ID"]
    IMAGE_API_URL = config["CLOUDFLARE_API_URL"]
    IMAGE_API_KEY = config["CLOUDFLARE_API_TOKEN_IMAGES"]
    GPT_API_KEY = config["REPLICATE_API_TOKEN"]
    GPT_MODEL = config["REPLICATE_MODEL_DRAW"]
    GPT_API_KEY2 = config["OPENAI_API_KEY"]
    GPT_MODEL2 = config["OPENAI_MODEL_DRAW"]


def login():
    username = st.session_state.get("username")
    password = st.session_state.get("password")

    if username == LOGIN_ID and password == LOGIN_PW:
        st.session_state.logged_in = True
        st.success("✅ Welcome to Cartoonize GPT!")
    else:
        st.warning("Check your Account!")


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


# Show Login Form
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.container():
        username = st.text_input("ID", key="username")
        password = st.text_input("PW", type="password", key="password")

        if st.button("LOGIN"):
            login()
    st.stop()


with st.sidebar:
    # Input Condition
    selected_input = st.selectbox(
        "Choose a Input Condition",
        (
            "이미지 | photo",
            "텍스트 | prompt",
        ),
    )

    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "디즈니 | Pixar disney",
            "마블   | Marvel hero",
            "지브리 | Ghibli studio",
            "짱구   | Crayon shinchan",
            "김홍도 | Korean folk painting",
            "선비 | Confucian scholar",
            "탤런트 | World wide celebrity",
        ),
    )

    # Aspect Ratio
    selected_ratio = (
        st.selectbox(
            "Choose a Aspect Ratio",
            (
                "기본(1:1) | 1:1",
                "가로(4:3) | 4:3",
                "가로(16:9) | 16:9",
                "세로(3:4) | 3:4",
                "세로(9:16) | 9:16",
            ),
        )
        if selected_input.split(" | ")[1] == "photo"
        else st.selectbox(
            "Choose a Aspect Ratio",
            (
                "기본(1:1) | 1024x1024",
                "가로(16:9) | 1792x1024",
                "세로(9:16) | 1024x1792",
            ),
        )
    )

    # Link to Github Repo
    st.markdown("---")
    github_link = "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app.py"
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not IMAGE_API_KEY:
    st.error("Please input your Cloudflare API Token on runtime configuration")
elif not GPT_API_KEY:
    st.error("Please input your Replicate API Token on runtime configuration")
elif not GPT_API_KEY2:
    st.error("Please input your OpenAI API Key on runtime configuration")
else:
    input_condition = selected_input.split(" | ")[1]

    if input_condition == "photo":
        # Define Replicate API Client
        replicate.client = replicate.Client(api_token=GPT_API_KEY)

        # Accept User's Prompt
        uploaded_file = st.file_uploader(
            "Upload your photo.", type=["jpg", "png", "jpeg"]
        )

        # Accept User's Prompt (Optional)
        user_prompt = st.text_input(
            "Enter your prompt if necessary:",
            placeholder=(
                "[EN] A woman in a white astronaut suit with orange flowers, [KR] 눈 내리는 숲 속 파란 망토 소녀"
            ),
        )

        if uploaded_file is not None:
            # Check File Size (Max 3MB)
            if uploaded_file.size > 3 * 1024 * 1024:
                st.warning("File size exceeds 3MB. Try again.")
            else:
                # Load Original Image
                image = Image.open(uploaded_file)

                # Show Original Image
                st.image(image, caption="Original Image", use_container_width=True)

                # Action to Cartoonize
                if st.button("Cartoonize your Photo"):
                    # Upload Image on Cloudflare Storage
                    image_url = None
                    with st.spinner("Uploading..."):
                        image_url = upload_image_to_storage(uploaded_file)

                    # if img_b64:
                    if image_url:
                        cartoon_url = None
                        art_style = selected_style.split(" | ")

                        prompt_plus = f"""
                            A cartoon version of the input image, maintaining the same pose, background and facial expression. 
                            Clean lines, bright colors, stylized like {art_style[1]} animation, but with the original subject's identity preserved. 
                            {user_prompt if len(user_prompt) > 5 else ""}
                        """
                        prompt_minus = """
                            disfigured, kitsch, ugly, oversaturated, greain, 
                            low-res, deformed, blurry, bad anatomy, poorly drawn face, 
                            mutation, mutated, extra limb, poorly drawn hands, missing limb, 
                            floating limbs, disconnected limbs, malformed hands, blur, out of focus, 
                            long neck, long body, disgusting, poorly drawn, childish, 
                            mutilated, mangled, old, surreal, calligraphy, 
                            sign, writing, watermark, text, body out of frame, 
                            extra legs, extra arms, extra feet, out of frame, poorly drawn feet, 
                            cross-eye
                        """

                        # Transform uploaded image into cartoon using stable-diffusion-3.5-medium
                        with st.spinner("Transforming..."):
                            output = replicate.run(
                                GPT_MODEL,
                                input={
                                    "image": image_url,
                                    "prompt": prompt_plus,
                                    "negative_prompt": prompt_minus,
                                    "prompt_strength": 0.5,
                                    "strength": 0.5,
                                    "guidance_scale": 7.5,
                                    "output_quality": 90,
                                    "num_inference_steps": 30,
                                    "num_outputs": 1,
                                    "aspect_ratio": selected_ratio.split(" | ")[1],
                                },
                            )
                            cartoon_url = (
                                str(output[0])
                                if isinstance(output, list)
                                else str(output)
                            )

                        # Show Transformed Image
                        if cartoon_url:
                            st.image(
                                cartoon_url,
                                caption=f"{art_style[1]} style of cartoon",
                                use_container_width=True,
                            )

    else:
        # Define OpenAI API Client
        client = openai.OpenAI(api_key=GPT_API_KEY2)

        # Accept User's Prompt
        user_prompt = st.text_input("Enter your prompt (at least 10 characters):")

        # Show Example Prompt
        st.markdown(
            """
            **Example Prompt in English**:  
            - *A woman in a white astronaut suit surrounded by orange flowers*  
            - *A cozy winter cabin with a cat sleeping by the fireplace*  
            - *A cyberpunk city with neon lights and flying cars*  

            **Example Prompt in Korean**:  
            - *눈 내리는 마법 숲 속 파란 망토 소녀*  
            - *저녁노을에 비친 한옥과 고요한 호수*  
            - *1980년대 아케이드 게임장에서 웃는 남녀*
            """
        )

        if user_prompt:
            if len(user_prompt) >= 10:
                # Action to Cartoonize
                if st.button("Cartoonize your Prompt"):
                    cartoon_url = None
                    art_style = selected_style.split(" | ")

                    # Transform uploaded image into cartoon using dall-e-3
                    with st.spinner("Transforming..."):
                        response = client.images.generate(
                            model=GPT_MODEL2,
                            size=selected_ratio.split(" | ")[1],
                            prompt=f"A {art_style[1]} style of cartoonized image, {user_prompt}",
                            n=1,
                        )
                        cartoon_url = response.data[0].url

                    if cartoon_url:
                        # Show Transformed Image
                        st.image(
                            cartoon_url,
                            caption=f"[{art_style[0]}] {user_prompt}",
                            use_container_width=True,
                        )
            else:
                st.error("⚠️ Please enter at least 10 characters.")
