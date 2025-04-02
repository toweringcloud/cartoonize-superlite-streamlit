import io
import openai
import streamlit as st
from PIL import Image


# Streamlit 앱 UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")


with st.sidebar:
    # Input LLM API Key
    API_KEY = st.text_input("Input your OpenAI API Key", type="password")

    # Select Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        ("지브리", "고흐", "사이버틱"),
    )

    # Link to Github Repo
    # st.markdown("---")
    # github_link = "https://github.com/toweringcloud/cartoonize-gpt/blob/main/index.py"
    # badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    # st.write(f"[![Repo]({badge_link})]({github_link})")


if not API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
else:
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=API_KEY)

    uploaded_file = st.file_uploader("사진을 업로드하세요", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # 파일 크기 확인 (3MB 초과 시 경고)
        if uploaded_file.size > 3 * 1024 * 1024:
            st.warning("파일 용량이 3MB를 초과합니다. 더 작은 파일을 업로드해주세요.")
        else:
            # 원본 이미지 로드
            image = Image.open(uploaded_file)

            # 회전 옵션 추가
            rotation = st.radio(
                "이미지 회전", ("회전 없음", "왼쪽 90도", "오른쪽 90도")
            )
            if rotation == "왼쪽 90도":
                image = image.rotate(90, expand=True)
            elif rotation == "오른쪽 90도":
                image = image.rotate(-90, expand=True)

            # 원본 이미지 표시
            st.image(image, caption="원본 이미지", use_container_width=True)

            # 변환 버튼
            if st.button("만화 스타일로 변환하기"):
                # 2MB 이상이면 크기 조정
                img_io = None
                if uploaded_file.size > 2 * 1024 * 1024:
                    img_io = io.BytesIO()
                    image.save(img_io, format="PNG", quality=85)
                    img_io.seek(0)
                else:
                    img_io = io.BytesIO()
                    image.save(img_io, format="PNG")
                    img_io.seek(0)

                # 마스크 이미지 생성 (전체 편집을 위한 투명 마스크)
                mask = Image.new(
                    "L", image.size, 255
                )  # 흰색 마스크 (모든 부분 편집 허용)
                mask_io = io.BytesIO()
                mask.save(mask_io, format="PNG")
                mask_io.seek(0)

                st.write("변환 중...")

                # OpenAI DALL·E API를 활용해 만화 스타일로 변환
                response = client.images.edit(
                    model="dall-e-2",
                    image=img_io,
                    mask=mask_io,
                    prompt=f"이 이미지를 {selected_style} 스타일의 만화 캐릭터로 바꿔줘.",
                    n=1,
                    size="1024x1024",
                )
                cartoon_url = response.data[0].url

                # 변환된 이미지 표시
                st.image(
                    cartoon_url, caption="Cartoonized Image", use_container_width=True
                )

                # LangChain을 활용한 이미지 설명 생성
                description_prompt = (
                    "Describe this cartoon-style image briefly in Korean."
                )
                description = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": description_prompt}],
                )

                # st.write("### 이미지 설명 📝")
                st.write(description["choices"][0]["message"]["content"])
