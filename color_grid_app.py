import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import io

st.set_page_config(page_title="격자 색상 분석", layout="wide")

# 리디바탕체 웹폰트 적용
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/webfontworld/ridibatang/RidiBatang.css');

    html, body, [class*="css"], .stApp {
        font-family: 'RidiBatang', serif !important;
    }

    div.stMarkdown p, div.stMarkdown h1, h2, h3, h4, h5, h6 {
        font-family: 'RidiBatang', serif !important;
    }
    </style>
""", unsafe_allow_html=True)

# 상태 저장
if "grid_size" not in st.session_state:
    st.session_state.grid_size = (4, 4)
if "image" not in st.session_state:
    st.session_state.image = None
if "avg_colors" not in st.session_state:
    st.session_state.avg_colors = []
if "pending_grid_size" not in st.session_state:
    st.session_state.pending_grid_size = (4, 4)

# 탭 구성
tabs = st.tabs(["1. 시작", "2. 전체 보기", "3. 조각 보기", "4. 조색정보"])

# === 1. 이미지 업로드 탭 ===
with tabs[0]:
    st.header("1. 이미지 업로드 및 격자 설정")
    uploaded_file = st.file_uploader("이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

    pending_cols = st.slider("가로 칸 수 (cols)", 1, 50, st.session_state.pending_grid_size[0])
    pending_rows = st.slider("세로 칸 수 (rows)", 1, 50, st.session_state.pending_grid_size[1])

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state.image = image
        st.image(image, caption="업로드된 이미지", use_container_width=True)

        if st.button("?? 분석 시작"):
            st.session_state.grid_size = (pending_cols, pending_rows)
            cols, rows = st.session_state.grid_size

            # 평균 색상 계산
            w, h = image.size
            cell_w = w // cols
            cell_h = h // rows

            avg_colors = []
            for r in range(rows):
                row_colors = []
                for c in range(cols):
                    cell = image.crop((c*cell_w, r*cell_h, (c+1)*cell_w, (r+1)*cell_h))
                    mean_color = tuple(np.array(cell).mean(axis=(0,1)).astype(int))
                    hex_color = '#%02x%02x%02x' % mean_color
                    row_colors.append(hex_color)
                avg_colors.append(row_colors)

            st.session_state.avg_colors = avg_colors
            st.session_state.pending_grid_size = (pending_cols, pending_rows)
            st.success("색상 추출 완료!")

# === 2. 전체 색상 격자 탭 ===
with tabs[1]:
    st.header("2. 전체 색상 격자 (버전 1)")
    if not st.session_state.avg_colors:
        st.warning("이미지를 업로드하고 분석을 먼저 해주세요.")
    else:
        cols, rows = st.session_state.grid_size
        grid = st.session_state.avg_colors

        left_col, right_col = st.columns(2)

        with left_col:
            st.image(st.session_state.image, caption="원본 이미지", use_container_width=True)

        with right_col:
            html = f"<div style='display:grid;grid-template-columns:repeat({cols}, 1fr);gap:1px;width:100%;'>"
            for row in grid:
                for color in row:
                    html += f"<div style='aspect-ratio:1/1;background:{color}' title='{color}'></div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

# === 3. 셀 번호 검색 탭 ===
with tabs[2]:
    st.header("3. 셀 번호로 보기 (버전 2)")
    if not st.session_state.avg_colors:
        st.warning("이미지를 업로드하고 분석을 먼저 해주세요.")
    else:
        cols, rows = st.session_state.grid_size
        grid = st.session_state.avg_colors

        cell_id = st.text_input("셀 번호 입력 (예: 0101 = 1열 1행)", max_chars=4)

        if len(cell_id) == 4 and cell_id.isdigit():
            col = int(cell_id[:2]) - 1
            row = int(cell_id[2:]) - 1

            if 0 <= row < rows and 0 <= col < cols:
                hex_color = grid[row][col]

                left_col, right_col = st.columns(2)

                with left_col:
                    image = st.session_state.image
                    w, h = image.size
                    cell_w = w // cols
                    cell_h = h // rows
                    cell_img = image.crop((col*cell_w, row*cell_h, (col+1)*cell_w, (row+1)*cell_h))
                    st.image(cell_img, caption=f"셀 {cell_id} 이미지", use_container_width=True)

                with right_col:
                    st.markdown(f"<div style='width:100%;aspect-ratio:1/1;background:{hex_color}'></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;'><strong>셀 {cell_id} 평균 색상: `{hex_color}`</strong></p>", unsafe_allow_html=True)
            else:
                st.error("입력한 셀 번호가 격자 범위를 벗어났어요.")

# === 4. 조색정보 탭 ===
with tabs[3]:
    st.header("4. 조색정보")
    if not st.session_state.avg_colors:
        st.warning("이미지를 업로드하고 분석을 먼저 해주세요.")
    else:
        cols, rows = st.session_state.grid_size
        grid = st.session_state.avg_colors
        data = []

        for r in range(rows):
            for c in range(cols):
                hex_color = grid[r][c]
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
                r_f, g_f, b_f = [x / 255.0 for x in rgb]
                k = 1 - max(r_f, g_f, b_f)
                if k < 1:
                    c_c = (1 - r_f - k) / (1 - k)
                    m_c = (1 - g_f - k) / (1 - k)
                    y_c = (1 - b_f - k) / (1 - k)
                else:
                    c_c = m_c = y_c = 0

                data.append({
                    "연번": f"{r*cols + c + 1:04}",
                    "격자위치": f"{c+1:02}{r+1:02}",
                    "색상코드": hex_color,
                    "Cyan(%)": round(c_c * 100, 2),
                    "Magenta(%)": round(m_c * 100, 2),
                    "Yellow(%)": round(y_c * 100, 2),
                    "White(%)": round(k * 100, 2)
                })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="?? CSV 다운로드",
            data=csv,
            file_name="color_mix_info.csv",
            mime="text/csv"
        )
