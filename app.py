from PIL import Image
import base64
import io
import replicate
import streamlit as st


# Streamlit 앱 UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")


with st.sidebar:
    # Input LLM API Key
    API_KEY = st.text_input("Input your Replicate API Key", type="password")

    # Select Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        ("ghibli", "van gogh", "cyber"),
    )


if not API_KEY:
    st.error("Please input your API Key on the sidebar")
else:
    # Replicate API 클라이언트 설정
    replicate.client = replicate.Client(api_token=API_KEY)

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
                st.write("변환 중...")

                # 이미지를 Base64로 인코딩하여 API에 전달
                img_io = io.BytesIO()
                image.save(img_io, format="PNG")
                img_bytes = img_io.getvalue()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Replicate API 호출 (Stable Diffusion img2img 모델 활용)
                output = replicate.run(
                    "stability-ai/stable-diffusion-img2img",
                    input={
                        "image": f"data:image/png;base64,{img_b64}",
                        "prompt": f"A cartoon version of this image, high quality, digital art, {selected_style} style",
                        "strength": 0.75,  # 변환 강도 (0~1, 높을수록 변형 많아짐)
                        "guidance_scale": 7.5,
                    },
                )
                cartoon_url = output[0]  # 변환된 이미지 URL

                # 변환된 이미지 표시
                st.image(
                    cartoon_url, caption="만화 스타일 이미지", use_container_width=True
                )
