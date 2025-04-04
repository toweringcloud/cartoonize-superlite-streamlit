from dotenv import dotenv_values
import openai
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Prompt")


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
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_openapi.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not OPENAI_API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
else:
    # Define OpenAI API Client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Accept User's Prompt
    user_prompt = st.text_input

    if user_prompt is not None and len(user_prompt) >= 10:
        # Action to Cartoonize
        if st.button("Cartoonize your photo."):
            # Transform Uploaded Image using OpenAI DALL·E API
            cartoon_url = None
            with st.spinner("Transforming..."):
                art_style = selected_style.split(" | ")[1]
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=f"{user_prompt}, high quality, {art_style} cartoon style",
                    size="1024x1024",
                    n=1,
                )
                cartoon_url = response.data[0].url

            if cartoon_url:
                st.success("✅ Transformed!")

                # Show Transformed Image
                st.image(
                    cartoon_url, caption="Cartoonized Image", use_container_width=True
                )
