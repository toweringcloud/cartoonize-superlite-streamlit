from dotenv import dotenv_values
import openai
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Prompt")

# Load Configuration
IS_TEST = True
config = dotenv_values(".env")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    username = st.session_state.get("username")
    password = st.session_state.get("password")

    if username == config["CUSTOM_LOGIN_ID"] and password == config["CUSTOM_LOGIN_PW"]:
        st.session_state.logged_in = True
        st.success("✅ Welcome to Cartoonize GPT!")
    else:
        st.warning("Check your Account!")


# Show Login Form
if not st.session_state.logged_in:
    with st.container():
        username = st.text_input("ID", key="username")
        password = st.text_input("PW", type="password", key="password")

        if st.button("LOGIN"):
            login()
    st.stop()


with st.sidebar:
    # API Credential
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
    github_link = "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app.py"
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not OPENAI_API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
else:
    # Define OpenAI API Client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Accept User's Prompt
    user_prompt = st.text_input("Enter your prompt (at least 10 characters):")

    if user_prompt:
        if len(user_prompt) >= 10:
            # Action to Cartoonize
            if st.button("Cartoonize your prompt."):
                # Transform Uploaded Image using OpenAI DALL·E API
                cartoon_url = None
                with st.spinner("Transforming..."):
                    art_style = selected_style.split(" | ")
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=f"{user_prompt}, high quality, {art_style[1]} cartoon style",
                        size="1024x1024",
                        n=1,
                    )
                    cartoon_url = response.data[0].url

                if cartoon_url:
                    st.success("✅ Transformed!")

                    # Show Transformed Image
                    st.image(
                        cartoon_url,
                        caption=f"[{art_style[0]}] {user_prompt}",
                        use_container_width=True,
                    )
        else:
            st.error("⚠️ Please enter at least 10 characters.")
