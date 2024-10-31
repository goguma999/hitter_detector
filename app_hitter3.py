import os
import tempfile
import streamlit as st
import cv2
from moviepy.editor import VideoFileClip
from ultralytics import YOLO

# 전체 레이아웃을 넓게 설정
st.set_page_config(layout="wide")

# 제목
st.title("Who is the hitter")

# 모델 파일 업로드
model_file = st.file_uploader("모델 파일을 업로드하세요", type=["pt"])
if model_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as temp_model_file:
        temp_model_file.write(model_file.read())
        model_path = temp_model_file.name
    model = YOLO(model_path)
    st.success("모델이 성공적으로 로드되었습니다.")

# 비디오 파일 업로드
uploaded_file = st.file_uploader("비디오 파일을 업로드하세요", type=["mp4", "mov", "avi"])

# 속도 선택 슬라이더 추가
speed = st.slider("재생 속도 선택", 0.5, 2.0, 1.0, step=0.1)

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
        if "processed_video" in st.session_state and st.session_state["processed_video"] is not None:
            result_placeholder.video(st.session_state["processed_video"])
        else:
            result_placeholder.markdown(
                """
                <div style='width:100%; height:620px; background-color:#d3d3d3; display:flex; align-items:center; justify-content:center; border-radius:5px;'>
                    <p style='color:#888;'>여기에 타자 분석 결과가 표시됩니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# 사물 검출 실행 버튼
if st.button("타자 분석 실행") and uploaded_file and model_file:
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

    # 프레임별로 사물 검출 수행
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO 모델로 예측 수행
        results = model(frame)
        detections = results[0].boxes if len(results) > 0 else []

        # 검출된 객체에 대해 바운딩 박스 그리기
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0]
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            label = f"{class_name} {confidence:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        out.write(frame)

    cap.release()
    out.release()

    # moviepy를 사용해 재인코딩 및 속도 조정
    reencoded_path = output_path.replace(".mp4", f"_speed_{speed}x.mp4")
    clip = VideoFileClip(output_path).fx(vfx.speedx, speed)
    clip.write_videofile(reencoded_path, codec="libx264", audio_codec="aac")

    # 재인코딩된 비디오 경로를 세션에 저장하고 col2에 표시
    st.session_state["processed_video"] = reencoded_path
    result_placeholder.video(st.session_state["processed_video"])

    # 재인코딩된 비디오 다운로드 버튼 제공
    with open(reencoded_path, "rb") as file:
        st.download_button(
            label="재인코딩된 결과 영상 다운로드",
            data=file,
            file_name=f"reencoded_video_{speed}x.mp4",
            mime="video/mp4"
        )
