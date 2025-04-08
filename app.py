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
if "OPENAI_API_KEY" in st.secrets:
    LOGIN_ID = st.secrets["CUSTOM_LOGIN_ID"]
    LOGIN_PW = st.secrets["CUSTOM_LOGIN_PW"]
    API_KEY = st.secrets["OPENAI_API_KEY"]
    GPT_MODEL = st.secrets["OPENAI_MODEL_DRAW"]
else:
    config = dotenv_values(".env")
    LOGIN_ID = config["CUSTOM_LOGIN_ID"]
    LOGIN_PW = config["CUSTOM_LOGIN_PW"]
    API_KEY = config["OPENAI_API_KEY"]
    GPT_MODEL = config["OPENAI_MODEL_DRAW"]


def login():
    username = st.session_state.get("username")
    password = st.session_state.get("password")

    if username == LOGIN_ID and password == LOGIN_PW:
        st.session_state.logged_in = True
        st.success("✅ Welcome to Cartoonize GPT!")
    else:
        st.warning("Check your Account!")


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
    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "케이팝 | k-pop",
            "뽀로로 | ppororo",
            "지브리 | ghibli",
            "짱구   | crayon shinchan",
            "디즈니 | disney",
            "고흐   | van gogh",
            "피카소 | picaso",
        ),
    )

    # Link to Github Repo
    st.markdown("---")
    github_link = "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app.py"
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


if not API_KEY:
    st.error("Please setup your OpenAI API Key on the runtime configuration")
else:
    # Define OpenAI API Client
    client = openai.OpenAI(api_key=API_KEY)

    # Accept User's Prompt
    user_prompt = st.text_input("Enter your prompt (at least 10 characters):")

    if user_prompt:
        if len(user_prompt) >= 10:
            # Action to Cartoonize
            if st.button("🐱‍🐉 Cartoonize"):
                # Transform Uploaded Image using OpenAI DALL·E API
                cartoon_url = None
                with st.spinner("Transforming..."):
                    art_style = selected_style.split(" | ")
                    response = client.images.generate(
                        model=GPT_MODEL,
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
