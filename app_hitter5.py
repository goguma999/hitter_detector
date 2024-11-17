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
st.write("\n" * 3)  # 간격 추가
st.header("🤖선수 정보 검색🤖")

# 선수 이름을 입력받고 정보를 제공
player_name = st.text_input("궁금한 선수의 이름을 입력하세요:")
search_button = st.button("검색")

# 선수 정보를 저장한 딕셔너리
player_info = {
    "yongkyu": ["이용규", "용규", "yongkyu", "Yongkyu"],
    "geonchang": ["서건창", "건창", "geonchang", "Geonchang"],
    "heedong": ["권희동", "희동", "heedong", "Heedong"],
    "daehyung": ["이대형", "대형", "daehyung", "Daehyung"],
    "byungho": ["박병호", "병호", "byungho", "Byungho"],
    "sihwan": ["노시환", "시환", "sihwan", "Sihwan"]
}

# 선수별 상세 정보를 저장한 딕셔너리
player_info_details = {
    "yongkyu": "[이용규] 한줄평 \n키움 히어로즈 소속 좌투좌타 외야수 \n생년월일: 1985년 08월 26일 \n경력: 성동초-잠신중-덕수정보고-LG-KIA-한화 \n입단연도: 2004(2차 2라운드 전체 15번, LG) \n수상: 골든글러브(2006, 2011, 2012)",
    "geonchang": "[서건창] 한줄평 \n기아 타이거즈 소속 우투좌타 내야수 \n생년월일: 1989년 08월 22일 \n경력: 송정동초-충장중-광주제일고-LG-히어로즈-키움-LG \n입단연도: 2008 LG 육성선수 \n수상: 신인왕(2012), 골든글러브(2012, 2014, 2016), 정규시즌 MVP(2014)",
    "heedong": "[권희동] 한줄평 \nNC다이노스 소속 우투우타 외야수 \n생년월일: 1990년 12월 30일\n경력: 동천초-경주중-경주고-경남대-NC-상무 \n입단연도: 2013(9라운드 전체 84번, NC)",
    "daehyung": "[이대형] 한줄평\n 2003년~2019년 활약한 前야구선수 現SPOTV 야구 해설 위원\n생년월일: 1983년 07월 19일 \n경력: 광주서림초-무등중-광주제일고-LG-KIA-KT \n입단연도: 2003(2차 2라운드 전체 11번, LG) \n수상: 골든글러브(2007)",
    "byungho": "[박병호] 한줄평 \n삼성 라이온즈 소속 우투우타 내야수 \n생년월일: 1986년 07월 10일 \n경력: 영일초-영남중-성남고-상무-LG-히어로즈-미네소타-넥센(키움)-KT \n입단연도: 2005(1차 지명, LG) \n수상: 골든글러브(2012, 2013, 2014, 2018, 2019, 2022), 정규시즌 MVP(2012, 2013), 올스타전 MVP(2014), 준플레이오프 MVP(2019)",
    "sihwan": "[노시환] 한줄평 \n한화 이글스 소속 우투우타 내야수 \n생년월일: 2000년 12월 03일 \n경력: 부산수영초-경남중-경남고 \n입단연도: 2019(2차 1라운드 전체 3번, 한화 \n수상: 골든글러브(2023)"
        }

# 검색 버튼이 눌렸을 때 선수 정보 표시
if search_button:
    # 입력한 이름을 모든 선수의 별명 리스트에서 찾기
    found_player = None
    for key, aliases in player_info.items():
        if player_name in aliases:
            found_player = key
            break

    # 결과 출력
    if found_player:
        st.markdown(
            f"<div style='background-color:#e6f7ff; padding:10px; border-radius:5px; font-weight:bold;'>"
            f"{player_info_details[found_player]}"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='color:red; font-weight:bold;'>해당 선수의 정보가 없습니다.</div>",
            unsafe_allow_html=True
        )




