import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="고장 위험 순서 예측하기")

st.title("고장 위험 순서 예측하기")
st.caption("공정 조건 다섯 가지로 고장 여부를 판별합니다")

탭_데이터훑기, 탭_전처리, 탭_학습, 탭_결과, 탭_리포트 = st.tabs(
    ["데이터 훑기", "전처리", "학습", "결과", "리포트"]
)

with 탭_데이터훑기:
    업로드파일 = st.file_uploader("CSV 파일을 올려주세요", type="csv")

    if 업로드파일 is None:
        st.write("파일을 올려주세요")
    else:
        df = pd.read_csv(업로드파일)
        st.session_state["df"] = df  # 다른 탭에서도 같은 데이터를 쓰도록 저장

        # 1) 행 수와 열 수를 한 줄로
        st.write(f"행 수: {df.shape[0]} / 열 수: {df.shape[1]}")

        # 2) 앞의 다섯 줄을 표로
        st.dataframe(df.head())

        # 3) 빈칸이 모두 몇 개인지 한 줄로
        빈칸수 = df.isna().sum()
        전체빈칸수 = int(빈칸수.sum())
        st.write(f"빈칸 개수: {전체빈칸수}")

        if 전체빈칸수 > 0:
            빈칸있는열 = 빈칸수[빈칸수 > 0]
            빈칸표 = pd.DataFrame({
                "열 이름": 빈칸있는열.index,
                "빈칸 개수": 빈칸있는열.values,
                "빈칸 비율(%)": (빈칸있는열.values / len(df) * 100).round(2),
            })
            st.dataframe(빈칸표)
        else:
            st.write("빈칸 없음")

        # 4) 결과 열을 고르는 선택 상자 - 처음 값은 맨 마지막 열
        st.write("맞는 열인지 확인하세요")
        결과열 = st.selectbox("결과 열을 고르세요", df.columns, index=len(df.columns) - 1)
        st.session_state["결과열"] = 결과열  # 전처리 탭에서 그대로 이어 쓰도록 저장

        값별표 = df[결과열].value_counts().reset_index()
        값별표.columns = [결과열, "건수"]
        값별표["비율(%)"] = (값별표["건수"] / len(df) * 100).round(2)
        st.dataframe(값별표)

with 탭_전처리:
    if "df" not in st.session_state:
        st.write("먼저 '데이터 훑기' 탭에서 파일을 올려주세요")
    else:
        # 첫 번째 탭에서 올린 파일을 그대로 쓴다 (다시 올리지 않는다)
        원본df = st.session_state["df"]
        결과열_전처리 = st.session_state.get("결과열", 원본df.columns[-1])

        # 빈칸이 몇 개인지 먼저 센다
        빈칸수_전 = int(원본df.isna().sum().sum())

        if 빈칸수_전 == 0:
            st.write("빈칸이 없습니다. 채울 것이 없어요")
            채우기방법 = None
        else:
            st.write(f"빈칸 개수: {빈칸수_전}")
            채우기방법 = st.selectbox("빈칸을 무엇으로 채울까요", ["중앙값", "평균", "0"])

        # 글자로 된 열 목록 (결과 열은 따로 처리하므로 제외)
        글자열목록 = [c for c in 원본df.select_dtypes(include="object").columns if c != 결과열_전처리]

        if 글자열목록:
            st.write("글자로 된 열:", ", ".join(글자열목록))
            글자열처리 = st.selectbox("글자로 된 열을 어떻게 할까요", ["학습에서 뺀다", "숫자로 바꾼다"])
        else:
            st.write("글자로 된 열 없음")
            글자열처리 = None

        # 결과 열에서 어느 값을 1로 볼지 고른다
        결과값목록 = 원본df[결과열_전처리].dropna().unique().tolist()
        양성값 = st.selectbox(f"'{결과열_전처리}' 열에서 어느 값을 1로 볼까요", 결과값목록)

        # 학습용·시험용 나누는 비율 (기본 8대 2 = 시험용 20%)
        시험비율 = st.slider("시험용 비율(%)", min_value=10, max_value=50, value=20, step=5)

        if st.button("적용"):
            처리후df = 원본df.copy()

            # 1) 빈칸 채우기 (숫자 열만)
            숫자열_전처리 = 처리후df.select_dtypes(include="number").columns
            if 채우기방법 == "중앙값":
                처리후df[숫자열_전처리] = 처리후df[숫자열_전처리].fillna(처리후df[숫자열_전처리].median())
            elif 채우기방법 == "평균":
                처리후df[숫자열_전처리] = 처리후df[숫자열_전처리].fillna(처리후df[숫자열_전처리].mean())
            elif 채우기방법 == "0":
                처리후df[숫자열_전처리] = 처리후df[숫자열_전처리].fillna(0)

            빈칸수_후 = int(처리후df.isna().sum().sum())

            # 2) 글자 열 처리
            if 글자열처리 == "학습에서 뺀다":
                처리후df = 처리후df.drop(columns=글자열목록)
                글자열_설명 = f"글자 열 {len(글자열목록)}개를 학습에서 뺐습니다"
            elif 글자열처리 == "숫자로 바꾼다":
                for 열이름 in 글자열목록:
                    처리후df[열이름] = 처리후df[열이름].astype("category").cat.codes
                글자열_설명 = f"글자 열 {len(글자열목록)}개를 숫자로 바꿨습니다"
            else:
                글자열_설명 = "글자로 된 열이 없어 처리하지 않았습니다"

            # 결과 열을 label(1/0)로 바꾼다
            처리후df["label"] = (원본df[결과열_전처리] == 양성값).astype(int)
            전체_1건수 = int(처리후df["label"].sum())

            # 3) 학습용·시험용으로 나눈다
            from sklearn.model_selection import train_test_split
            학습df, 시험df = train_test_split(
                처리후df,
                test_size=시험비율 / 100,
                random_state=42,
                stratify=처리후df["label"],
            )

            st.write(f"빈칸 {빈칸수_전}개 → {빈칸수_후}개")
            st.write(글자열_설명)
            st.write(f"결과 열을 0/1로 바꿨습니다 - 1(양성)이 {전체_1건수}건입니다")
            st.write(f"학습용 {len(학습df)}행 / 시험용 {len(시험df)}행")

            나뉜행수합 = len(학습df) + len(시험df)
            행수일치 = 나뉜행수합 == len(원본df)
            st.write(
                f"행 수가 원본과 같은가: {행수일치} "
                f"(학습 {len(학습df)} + 시험 {len(시험df)} = {나뉜행수합} / 원본 {len(원본df)})"
            )

            나눔비교표 = pd.DataFrame({
                "구분": ["학습용", "시험용"],
                "1 개수": [int(학습df["label"].sum()), int(시험df["label"].sum())],
                "1 비율(%)": [
                    round(학습df["label"].mean() * 100, 2),
                    round(시험df["label"].mean() * 100, 2),
                ],
            })
            st.dataframe(나눔비교표)

            # 학습 탭에서 이어 쓰도록 나뉜 결과를 들고 있는다
            st.session_state["학습df"] = 학습df
            st.session_state["시험df"] = 시험df

with 탭_학습:
    if "학습df" not in st.session_state or "시험df" not in st.session_state:
        st.write("전처리를 먼저 해주세요")
    else:
        학습df_전달 = st.session_state["학습df"]
        시험df_전달 = st.session_state["시험df"]

        모델선택 = st.selectbox("모델을 고르세요", ["로지스틱 회귀", "의사결정나무", "랜덤 포레스트"])
        가중치켜기 = st.toggle("적은 쪽(1)에 가중치를 준다")

        if st.button("학습"):
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import make_pipeline
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

            # 숫자로 된 열만 입력으로 쓴다 (label과 원래 글자였던 결과 열은 자연히 빠진다)
            입력열_학습 = [c for c in 학습df_전달.select_dtypes(include="number").columns if c != "label"]
            X_train_학습 = 학습df_전달[입력열_학습]
            y_train_학습 = 학습df_전달["label"]
            X_test_학습 = 시험df_전달[입력열_학습]
            y_test_학습 = 시험df_전달["label"]

            가중치설정 = "balanced" if 가중치켜기 else None

            # 고른 모델을 만든다 (로지스틱 회귀만 표준화와 함께 묶는다)
            if 모델선택 == "로지스틱 회귀":
                모델객체 = make_pipeline(
                    StandardScaler(),
                    LogisticRegression(max_iter=1000, class_weight=가중치설정),
                )
            elif 모델선택 == "의사결정나무":
                모델객체 = DecisionTreeClassifier(random_state=42, class_weight=가중치설정)
            else:
                모델객체 = RandomForestClassifier(random_state=42, class_weight=가중치설정)

            # 학습용으로만 학습시키고 시험용으로 채점한다
            모델객체.fit(X_train_학습, y_train_학습)
            예측_학습 = 모델객체.predict(X_test_학습)
            확률_학습 = 모델객체.predict_proba(X_test_학습)[:, 1]  # 문턱 슬라이더에서 다시 쓸 예측 가능성

            # 기준 모델 - 전부 정상(0)이라고만 답한다
            기준예측_학습 = np.zeros(len(y_test_학습), dtype=int)

            def 네가지점수(정답, 예측값):
                return [
                    round(accuracy_score(정답, 예측값), 3),
                    round(precision_score(정답, 예측값, zero_division=0), 3),
                    round(recall_score(정답, 예측값, zero_division=0), 3),
                    round(f1_score(정답, 예측값, zero_division=0), 3),
                ]

            점수표 = pd.DataFrame(
                {
                    "기준 모델(전부 정상)": 네가지점수(y_test_학습, 기준예측_학습),
                    모델선택: 네가지점수(y_test_학습, 예측_학습),
                },
                index=["정확도", "정밀도", "재현율", "F1"],
            )
            st.dataframe(점수표)

            # 결과 탭에서 이어 쓰도록 학습 결과를 들고 있는다
            st.session_state["학습된모델"] = 모델객체
            st.session_state["학습입력열"] = 입력열_학습
            st.session_state["시험예측"] = 예측_학습
            st.session_state["시험확률"] = 확률_학습
            st.session_state["시험정답"] = y_test_학습
            st.session_state["기준예측"] = 기준예측_학습
            st.session_state["선택모델이름"] = 모델선택

with 탭_결과:
    필요값_결과 = ["학습된모델", "시험예측", "시험정답", "기준예측", "선택모델이름"]
    if not all(k in st.session_state for k in 필요값_결과):
        st.write("학습을 먼저 해주세요")
    else:
        # 세 번째 탭에서 만든 결과를 그대로 가져다 쓴다 (다시 학습하지 않는다)
        시험정답_결과 = st.session_state["시험정답"]
        시험예측_결과 = st.session_state["시험예측"]
        기준예측_결과 = st.session_state["기준예측"]
        모델이름_결과 = st.session_state["선택모델이름"]

        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

        def 네가지점수_결과(정답, 예측값):
            return [
                round(accuracy_score(정답, 예측값), 3),
                round(precision_score(정답, 예측값, zero_division=0), 3),
                round(recall_score(정답, 예측값, zero_division=0), 3),
                round(f1_score(정답, 예측값, zero_division=0), 3),
            ]

        # 맨 위 - 기준 모델과 내 모델을 나란히
        점수표_결과 = pd.DataFrame(
            {
                "기준 모델(전부 정상)": 네가지점수_결과(시험정답_결과, 기준예측_결과),
                모델이름_결과: 네가지점수_결과(시험정답_결과, 시험예측_결과),
            },
            index=["정확도", "정밀도", "재현율", "F1"],
        )
        st.dataframe(점수표_결과)

        # 그 아래 - 혼동행렬 네 칸
        맞힌정상, 헛경보, 놓친것, 잡은것 = confusion_matrix(시험정답_결과, 시험예측_결과).ravel()

        혼동표 = pd.DataFrame({
            "칸": ["잡은 것", "놓친 것", "헛경보", "정상을 정상이라 한 것"],
            "건수": [int(잡은것), int(놓친것), int(헛경보), int(맞힌정상)],
            "무슨 뜻인가": [
                "실제 1인데 1이라고 맞힌 건수",
                "실제 1인데 0이라고 놓친 건수",
                "실제 0인데 1이라고 잘못 지목한 건수",
                "실제 0인데 0이라고 맞힌 건수",
            ],
        })
        st.dataframe(혼동표)

        # 문턱 슬라이더 - 다시 학습하지 않고, 이미 나온 예측 가능성만 다시 잘라서 계산한다
        if "시험확률" not in st.session_state:
            st.write("문턱 슬라이더는 학습을 다시 한 번 하면 쓸 수 있습니다")
        else:
            시험확률_결과 = st.session_state["시험확률"]

            문턱값 = st.slider("문턱", min_value=0.05, max_value=0.95, value=0.50, step=0.05)
            st.write("지금 문턱:", 문턱값)

            문턱예측 = (시험확률_결과 >= 문턱값).astype(int)

            지목건수_문턱 = int((문턱예측 == 1).sum())
            진짜건수_문턱 = int(((문턱예측 == 1) & (시험정답_결과 == 1)).sum())
            놓친건수_문턱 = int(((문턱예측 == 0) & (시험정답_결과 == 1)).sum())

            정밀도_문턱 = round(precision_score(시험정답_결과, 문턱예측, zero_division=0), 3)
            재현율_문턱 = round(recall_score(시험정답_결과, 문턱예측, zero_division=0), 3)
            F1_문턱 = round(f1_score(시험정답_결과, 문턱예측, zero_division=0), 3)

            st.write(f"1) 지목한 건수: {지목건수_문턱}")
            st.write(f"2) 그중 진짜 건수: {진짜건수_문턱}")
            st.write(f"3) 놓친 건수: {놓친건수_문턱}")
            st.write(f"4) 정밀도: {정밀도_문턱} / 재현율: {재현율_문턱} / F1: {F1_문턱}")

            맞힌정상_문턱, 헛경보_문턱, 놓친것_문턱, 잡은것_문턱 = confusion_matrix(시험정답_결과, 문턱예측).ravel()
            혼동표_문턱 = pd.DataFrame({
                "칸": ["잡은 것", "놓친 것", "헛경보", "정상을 정상이라 한 것"],
                "건수": [int(잡은것_문턱), int(놓친것_문턱), int(헛경보_문턱), int(맞힌정상_문턱)],
            })
            st.dataframe(혼동표_문턱)

            # 문턱별 비교 표 - 0.1부터 0.9까지 아홉 줄
            문턱목록_비교 = [round(0.1 * i, 1) for i in range(1, 10)]
            문턱결과목록 = []
            for 문턱_비교 in 문턱목록_비교:
                예측_비교 = (시험확률_결과 >= 문턱_비교).astype(int)
                문턱결과목록.append({
                    "문턱": 문턱_비교,
                    "지목 건수": int((예측_비교 == 1).sum()),
                    "그중 진짜": int(((예측_비교 == 1) & (시험정답_결과 == 1)).sum()),
                    "놓친 건수": int(((예측_비교 == 0) & (시험정답_결과 == 1)).sum()),
                    "정밀도": round(precision_score(시험정답_결과, 예측_비교, zero_division=0), 3),
                    "재현율": round(recall_score(시험정답_결과, 예측_비교, zero_division=0), 3),
                    "F1": round(f1_score(시험정답_결과, 예측_비교, zero_division=0), 3),
                })

            문턱비교표 = pd.DataFrame(문턱결과목록)
            최고F1_인덱스 = 문턱비교표["F1"].idxmax()
            최고F1_문턱값 = 문턱비교표.loc[최고F1_인덱스, "문턱"]

            def F1최고_강조(행):
                if 행.name == 최고F1_인덱스:
                    return ["background-color: #ffe08a"] * len(행)
                return [""] * len(행)

            st.dataframe(문턱비교표.style.apply(F1최고_강조, axis=1))
            st.write(f"F1이 가장 높은 문턱: {최고F1_문턱값}")

        # 그림 세 장 - 중요 변수 / 혼동행렬 / 기준-내 모델 막대그림
        import os
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        # 한글이 네모로 깨지지 않도록 폰트를 먼저 잡는다 (그래프 안 글자도 같이 적용됨)
        mpl.rcParams["font.family"] = "Malgun Gothic"
        mpl.rcParams["axes.unicode_minus"] = False

        os.makedirs("figures", exist_ok=True)

        입력열_결과 = st.session_state["학습입력열"]
        모델객체_결과 = st.session_state["학습된모델"]

        # 1) 중요 변수 - 파이프라인이면 마지막 단계(실제 모델)를 꺼낸다
        마지막단계_결과 = 모델객체_결과[-1] if hasattr(모델객체_결과, "named_steps") else 모델객체_결과
        if hasattr(마지막단계_결과, "coef_"):
            중요도값 = np.abs(마지막단계_결과.coef_[0])
        else:
            중요도값 = 마지막단계_결과.feature_importances_
        중요도_결과 = pd.Series(중요도값, index=입력열_결과).sort_values()

        fig1, ax1 = plt.subplots(figsize=(8, 5))
        중요도_결과.plot(kind="barh", ax=ax1, color="steelblue")
        ax1.set_title("어느 항목이 판단에 많이 쓰였나")
        ax1.set_xlabel("중요도")
        fig1.tight_layout()
        경로1 = os.path.join("figures", "feature_importance.png")
        fig1.savefig(경로1, dpi=150, bbox_inches="tight")
        st.pyplot(fig1)
        st.caption("입력으로 쓴 열마다, 모델이 판단할 때 얼마나 크게 반영했는지를 보여줍니다")

        # 2) 혼동행렬 그림
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        행렬값 = np.array([[맞힌정상, 헛경보], [놓친것, 잡은것]])
        ax2.imshow(행렬값, cmap="Blues")
        ax2.set_xticks([0, 1])
        ax2.set_yticks([0, 1])
        ax2.set_xticklabels(["정상", "1(양성)"])
        ax2.set_yticklabels(["정상", "1(양성)"])
        ax2.set_xlabel("예측")
        ax2.set_ylabel("실제")
        ax2.set_title(f"혼동행렬 - {모델이름_결과}")
        for i in range(2):
            for j in range(2):
                ax2.text(
                    j, i, str(행렬값[i, j]), ha="center", va="center",
                    color="white" if 행렬값[i, j] > 행렬값.max() / 2 else "black",
                )
        fig2.tight_layout()
        경로2 = os.path.join("figures", "confusion_matrix.png")
        fig2.savefig(경로2, dpi=150, bbox_inches="tight")
        st.pyplot(fig2)
        st.caption("실제 값과 예측 값이 네 칸 중 어디에 들어갔는지 보여줍니다")

        # 3) 기준 모델과 내 모델 점수 막대그림
        fig3, ax3 = plt.subplots(figsize=(7, 5))
        지표이름_결과 = ["정확도", "정밀도", "재현율", "F1"]
        x위치 = np.arange(len(지표이름_결과))
        막대폭 = 0.35
        ax3.bar(x위치 - 막대폭 / 2, 점수표_결과["기준 모델(전부 정상)"], 막대폭,
                label="기준 모델(전부 정상)", color="lightgray")
        ax3.bar(x위치 + 막대폭 / 2, 점수표_결과[모델이름_결과], 막대폭,
                label=모델이름_결과, color="steelblue")
        ax3.set_xticks(x위치)
        ax3.set_xticklabels(지표이름_결과)
        ax3.set_ylim(0, 1)
        ax3.set_title("기준 모델과 내 모델 점수 비교")
        ax3.legend()
        fig3.tight_layout()
        경로3 = os.path.join("figures", "score_comparison.png")
        fig3.savefig(경로3, dpi=150, bbox_inches="tight")
        st.pyplot(fig3)
        st.caption("기준 모델과 내 모델의 정확도·정밀도·재현율·F1을 나란히 비교합니다")

with 탭_리포트:
    st.write("여기는 아직 비어 있습니다")

st.write("지금 시각:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
