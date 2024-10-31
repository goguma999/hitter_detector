import streamlit as st
from moviepy.editor import VideoFileClip
import tempfile

# 전체 레이아웃을 넓게 설정
st.set_page_config(layout="wide")

# # 제목 설정
# st.title("Who is the hitter")

# 커스텀 CSS를 사용해 폰트 스타일 설정
st.markdown(
    """
    <style>
    .custom-title {
        font-size: 3em;
        font-weight: 900;
        color: #506EFD; /* 원하는 색상 코드 */
        font-family: 'Courier New', monospace;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 커스텀 타이틀 표시
st.markdown('<p class="custom-title">Who is the hitter</p>', unsafe_allow_html=True)

# 파일 업로드
uploaded_file = st.file_uploader("비디오 파일을 업로드하세요", type=["mp4", "mov", "avi"])

# 속도 조절 슬라이더 추가 (0.5배에서 2배 속도 조절 가능)
speed = st.slider("재생 속도 조절", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

# 사물 검출 버튼 추가
if st.button("타자 분석하기"):
    if uploaded_file is not None:
        # 업로드된 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_video_path = temp_file.name
        
        # MoviePy를 사용하여 비디오 속도 조절
        with VideoFileClip(temp_video_path) as video:
            modified_video = video.fx(vfx.speedx, speed)  # 속도 조절 적용
            
            # 임시 파일에 저장된 비디오를 다시 불러와 세션 상태에 저장
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            modified_video.write_videofile(temp_output.name, codec="libx264")
            st.session_state["processed_video"] = temp_output.name
        
        st.success("타자 분석이 완료되어 오른쪽에 표시됩니다.")
    else:
        st.warning("타자 분석을 실행하려면 비디오 파일을 업로드하세요.")

# 전체 레이아웃을 컨테이너로 감싸기
with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.header("원본 영상")
        if uploaded_file is not None:
            st.video(uploaded_file)
        else:
            st.write("원본 영상을 표시하려면 비디오 파일을 업로드하세요.")

    with col2:
        st.header("타자 분석 결과 영상")
        result_placeholder = st.empty()
        if "processed_video" in st.session_state:
            st.video(st.session_state["processed_video"])
        else:
            result_placeholder.markdown(
                """
                <div style='width:100%; height:620px; background-color:#d3d3d3; display:flex; align-items:center; justify-content:center; border-radius:5px;'>
                    <p style='color:#888;'>여기에 타자 분석 결과가 표시됩니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
