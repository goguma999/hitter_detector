
import streamlit as st

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

# 전체 레이아웃을 컨테이너로 감싸기
with st.container():     # with절로 하나의 기능을 하는 코드를 묶어줌.(가독성 높이기) 
    col1, col2 = st.columns(2)  # 열을 균등하게 분배하여 넓게 표시.   # (3)하면 컬럼 3개 생성되는 거

    # 파일 업로드
    uploaded_file = st.file_uploader("비디오 파일을 업로드하세요", type=["mp4", "mov", "avi"])

    with col1:
        st.header("원본 영상")    # col1 영역의 제목
        if uploaded_file is not None:   # 영상이 업로드가 되었다면 
            st.video(uploaded_file)     # 영상 플레이 해라~ 
        else:
            st.write("원본 영상을 표시하려면 비디오 파일을 업로드하세요.")

    with col2:   
        st.header("타자 감지 결과 영상")  # col2에 해당하는 영역의 제목 
        if "processed_video" in st.session_state:     # 사물 검출 완료된 비디오가 있으면 
            st.video(st.session_state["processed_video"])  # 그 비디오를 플레이 해라 
        else:
            st.write("여기에 사물 검출 결과가 표시됩니다.")

# 사물 검출 버튼 추가
if st.button("사물 검출 실행"):     # 사물검출 실행이라는 버튼을 추가합니다. 버튼을 누르면 
    if uploaded_file is not None:  # 업로드된 영상이 있다면 
        st.session_state["processed_video"] = uploaded_file   # 검출된 영상을 사용
        st.success("사물 검출이 완료되어 오른쪽에 표시됩니다.")  # 이 메세지 출력
    else:
        st.warning("사물 검출을 실행하려면 비디오 파일을 업로드하세요.")







