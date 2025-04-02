import openai
import requests
import streamlit as st
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Streamlit 앱 UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")


with st.sidebar:
    # OpenAI Account
    OPENAI_API_KEY = st.text_input("Input your OpenAI API Key", type="password")

    # Cloudflare Account
    CLOUDFLARE_ACCOUNT_ID = "your_account_id"
    CLOUDFLARE_API_TOKEN = st.text_input(
        "Input your Cloudflare API Token", type="password"
    )
    CLOUDFLARE_UPLOAD_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"

    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        ("지브리", "고흐", "사이버틱"),
    )

    # Link to Github Repo
    # st.markdown("---")
    # github_link = "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_openai.py"
    # badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    # st.write(f"[![Repo]({badge_link})]({github_link})")


def upload_image_to_cloudflare(image_file):
    """Cloudflare Images API를 사용하여 이미지 업로드"""
    encoder = MultipartEncoder(
        fields={"file": (image_file.name, image_file, "image/jpeg")}
    )

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": encoder.content_type,
    }

    response = requests.post(CLOUDFLARE_UPLOAD_URL, headers=headers, data=encoder)

    if response.status_code == 200:
        return response.json()["result"]["variants"][0]  # 이미지 URL 반환
    else:
        st.error(f"업로드 실패: {response.text}")
        return None


if not OPENAI_API_KEY:
    st.error("Please input your OpenAI API Key on the sidebar")
elif not CLOUDFLARE_API_TOKEN:
    st.error("Please input your Cloudflare API Token on the sidebar")
else:
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
            st.image(image, caption="Original Image", use_container_width=True)

            # 변환 버튼
            if st.button("만화 스타일로 변환하기"):
                # Cloudflare에 이미지 업로드 후 URL 리턴
                image_url = None
                with st.spinner("업로드 중..."):
                    image_url = upload_image_to_cloudflare(uploaded_file)

                if image_url:
                    st.success("✅ 업로드 완료!")
                    st.image(
                        image_url,
                        caption="Uploaded Image",
                        use_container_width=True,
                    )
                    st.write("변환 중...")

                    # OpenAI DALL·E API를 활용해 만화 스타일로 변환
                    response = client.images.generate(
                        model="dall-e-3",
                        image=image_url,
                        prompt=f"이 이미지를 {selected_style} 스타일의 만화 캐릭터로 바꿔줘.",
                        n=1,
                        size="1024x1024",
                    )
                    cartoon_url = response["data"][0]["url"]

                    if cartoon_url:
                        st.success("✅ 변환 완료!")

                        # 변환된 이미지 표시
                        st.image(
                            cartoon_url,
                            caption="Cartoonized Image",
                            use_container_width=True,
                        )

                        # LangChain을 활용한 이미지 설명 생성
                        description_prompt = f"Describe this cartoon-style image briefly in Korean.\n (Image URL: {cartoon_url})"
                        description = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": description_prompt}
                            ],
                        )

                        # st.write("### 이미지 설명 📝")
                        st.write(description["choices"][0]["message"]["content"])
