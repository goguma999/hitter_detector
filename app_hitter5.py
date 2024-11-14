import os
import tempfile
import streamlit as st
import cv2
from moviepy.editor import VideoFileClip, vfx
from ultralytics import YOLO
from collections import defaultdict
import urllib.request

# 전체 레이아웃을 넓게 설정
st.set_page_config(layout="wide")

# 제목
st.title("⚾ Who is the batter ⚾")

# GitHub에 업로드된 모델 경로
MODEL_URL = "https://github.com/yourusername/yourrepository/raw/main/6_trained_model.pt"
model_path = "6_trained_model.pt"

# 모델 파일이 없을 경우 다운로드
if not os.path.exists(model_path):
    st.info("모델 파일을 다운로드 중입니다...")
    urllib.request.urlretrieve(MODEL_URL, model_path)
    st.success("모델 다운로드 완료!")

# YOLO 모델 로드
model = YOLO(model_path)

# 비디오 파일 업로드
uploaded_file = st.file_uploader("비디오 파일을 업로드하세요", type=["mp4", "mov", "avi"])

# 다른 영상이 업로드될 때 결과 리셋
if uploaded_file:
    st.session_state["processed_video"] = None

# 속도 선택 슬라이더와 "타자 분석 실행" 버튼을 나란히 배치하여 버튼을 오른쪽에 정렬
col_speed, col_button = st.columns([3, 1])

with col_speed:
    speed = st.slider("재생 속도 선택", 0.25, 1.0, 1.0, step=0.25)

with col_button:
    st.markdown(
        "<div style='display: flex; align-items: flex-end; justify-content: flex-end; height: 100%;'>",
        unsafe_allow_html=True
    )
    run_analysis = st.button("타자 분석 실행")
    st.markdown("</div>", unsafe_allow_html=True)

# 전체 레이아웃을 컨테이너로 감싸기
with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.header("원본 영상")
        if uploaded_file is not None:
            st.video(uploaded_file)
        else:
            st.markdown(
                """
                <div style='width:100%; height:300px; background-color:#d3d3d3; display:flex; align-items:center; justify-content:center; border-radius:5px;'>
                    <p style='color:#888;'>원본 영상이 여기에 표시됩니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        st.header("타자 분석 결과 영상")
        result_placeholder = st.empty()
        if "processed_video" in st.session_state and st.session_state["processed_video"] is not None:
            result_placeholder.video(st.session_state["processed_video"])
        else:
            result_placeholder.markdown(
                """
                <div style='width:100%; height:300px; background-color:#d3d3d3; display:flex; align-items:center; justify-content:center; border-radius:5px;'>
                    <p style='color:#888;'>여기에 타자 분석 결과가 표시됩니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# 영상과 분석 결과 사이의 간격을 넓히기
st.write("\n" * 2)

# 분석 결과 텍스트와 다운로드 버튼을 나란히 배치
result_col, button_col = st.columns([2, 1])

with result_col:
    result_text_placeholder = st.empty()
    result_text_placeholder.write("### 분석 결과: 영상 속 타자는 **_______** 입니다.")

with button_col:
    download_button_placeholder = st.empty()

# "타자 분석 실행" 버튼이 클릭되었을 때 비디오 분석 시작
if run_analysis and uploaded_file:
    # 임시 파일 경로 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output:
        output_path = temp_output.name

    # 원본 비디오 파일을 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False) as temp_input:
        temp_input.write(uploaded_file.read())
        temp_input_path = temp_input.name

    # 비디오 처리 시작
    cap = cv2.VideoCapture(temp_input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 검출된 인물 횟수를 추적하는 변수들
    detection_counts = defaultdict(int)
    frequent_detection = None
    confidence_threshold = 0.65

    # frequent_detection 이름을 한글 이름으로 매핑
    name_mapping = {
        "yongkyu": "이용규",
        "geonchang": "서건창",
        "daehyung": "이대형",
        "byungho": "박병호",
        "sihwan": "노시환",
        "heedong": "권희동"
    }

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO 모델로 예측 수행
        results = model(frame)
        detections = results[0].boxes if len(results) > 0 else []

        # 검출된 객체에 대해 바운딩 박스 그리기
        for box in detections:
            if box.conf[0] >= confidence_threshold:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                
                # 검출 횟수 증가 및 50프레임 도달 확인
                detection_counts[class_name] += 1
                if detection_counts[class_name] >= 50 and frequent_detection is None:
                    frequent_detection = class_name

                label = f"{class_name} {confidence:.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        out.write(frame)

    cap.release()
    out.release()

    # 가장 많이 검출된 인물을 한글 이름으로 변환
    translated_detection = name_mapping.get(frequent_detection, "없음")

    # moviepy를 사용해 재인코딩 및 속도 조정
    reencoded_path = output_path.replace(".mp4", f"_speed_{speed}x.mp4")
    clip = VideoFileClip(output_path).fx(vfx.speedx, speed)
    clip.write_videofile(reencoded_path, codec="libx264", audio_codec="aac")

    # 재인코딩된 비디오 경로를 세션에 저장하고 col2에 표시
    st.session_state["processed_video"] = reencoded_path
    result_placeholder.video(st.session_state["processed_video"])

    # 분석 결과 업데이트
    result_text = f"### 분석 결과: 영상 속 타자는 **{translated_detection}** 입니다."
    result_text_placeholder.write(result_text)

    # 결과 영상 다운로드 버튼 표시
    with open(reencoded_path, "rb") as file:
        download_button_placeholder.download_button(
            label="결과 영상 다운로드", 
            data=file,
            file_name=f"reencoded_video_{speed}x.mp4",
            mime="video/mp4"
        )


# 선수 정보 챗봇 기능
st.write("\n" * 2)  # 간격 추가
st.header("🤖선수 정보 검색🤖")

# 선수 이름을 입력받고 정보를 제공
player_name = st.text_input("궁금한 선수의 이름을 입력하세요:")
search_button = st.button("검색")

# 선수 정보를 저장한 딕셔너리
player_info = {
    "이용규": "1985년생, 좌타자, KBO 리그 활약",
    "서건창": "1989년생, 좌타자, 타이틀 보유",
    "이대형": "1983년생, 우타자, 뛰어난 주력",
    "박병호": "1986년생, 우타자, 홈런왕 출신 강타자",
    "노시환": "1999년생, 우타자, KBO 리그 신예",
    "권희동": "1990년생, 우타자, 강한 수비력"
}

# 검색 버튼이 눌렸을 때 선수 정보 표시
if search_button:
    if player_name in player_info:
        st.write(f"{player_name}: {player_info[player_name]}")
    else:
        st.write("해당 선수의 정보가 없습니다.")
