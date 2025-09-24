# streamlit_app.py
# ===============================================================
# HW1-1: Interactive Linear Regression Visualizer
#
# How to install (最低可用指令)
#   pip install streamlit scikit-learn matplotlib numpy pandas
#
# How to run
#   streamlit run streamlit_app.py
#
# 本 App 目的：
#   以可互動的方式示範「簡單線性回歸 y = a·x + b + noise」，
#   並以 CRISP-DM 六步驟組織程式結構與註解，包含資料生成、模型訓練、
#   以及前 5 大離群點標註與表格輸出。
#   ※ b 在本範例固定為 5（程式內清楚標示）。
# ===============================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import streamlit as st


# ------------------------------
# CRISP-DM Step 1: Business Understanding
# ------------------------------
# 教學目的：讓使用者調整資料量 (n)、真實斜率 a、雜訊變異 var，
# 視覺化線性關係、回歸線與離群點對模型的影響，並查看估計係數與離群點。


# ========== UI 基本設定 ==========
st.set_page_config(page_title="HW1-1: Interactive Linear Regression Visualizer", layout="wide")
st.title("HW1-1: Interactive Linear Regression Visualizer")

with st.sidebar:
    st.header("Configuration")
    n = st.slider("Number of data points (n)", min_value=50, max_value=3000, value=500, step=10)
    a_true = st.slider("Coefficient 'a' (y = ax + b + noise)", min_value=-5.0, max_value=5.0, value=2.0, step=0.1)
    var = st.slider("Noise Variance (var)", min_value=0, max_value=300, value=100, step=5)


# ------------------------------
# Utility Functions
# ------------------------------
def generate_data(n: int, a: float, var: float, seed: int = 42, b: float = 5.0) -> tuple[np.ndarray, np.ndarray, float]:
    """
    CRISP-DM Step 2: Data Understanding
    - x ~ Uniform(0, 10), length n
    - noise ~ Normal(0, sqrt(var))
    - y = a*x + b + noise
    - 固定亂數種子以利重現；本範例 b 固定為 5.0
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 10.0, size=n)
    noise = rng.normal(loc=0.0, scale=np.sqrt(var), size=n)
    y = a * x + b + noise
    return x, y, b


def fit_linear_regression(x: np.ndarray, y: np.ndarray) -> tuple[LinearRegression, np.ndarray, float, float]:
    """
    CRISP-DM Step 4: Modeling
    使用 scikit-learn 的 LinearRegression 擬合 (x, y)。
    回傳 model、y_pred、估計的 a_hat、b_hat。
    """
    # CRISP-DM Step 3: Data Preparation（把 x 轉成 (n, 1)）
    X = x.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    a_hat = float(model.coef_[0])
    b_hat = float(model.intercept_)
    return model, y_pred, a_hat, b_hat


def get_top_outliers(x: np.ndarray, y: np.ndarray, y_pred: np.ndarray, k: int = 5) -> pd.DataFrame:
    """
    以絕對殘差 |y - y_pred| 最大的前 k 筆為離群點，回傳表格資料。
    """
    residuals = y - y_pred
    order = np.argsort(-np.abs(residuals))[:k]
    df = pd.DataFrame({
        "index": order,
        "x": x[order],
        "y": y[order],
        "residuals": residuals[order]
    }).reset_index(drop=True)

    # 四捨五入到 4 位小數供顯示
    df_display = df.copy()
    df_display["x"] = df_display["x"].round(4)
    df_display["y"] = df_display["y"].round(4)
    df_display["residuals"] = df_display["residuals"].round(4)

    # 依 |residual| 由大到小排序（顯示用）
    df_display = df_display.reindex(df_display["residuals"].abs().sort_values(ascending=False).index)
    df_display = df_display[["index", "x", "y", "residuals"]]
    return df_display


def plot_regression_with_outliers(x: np.ndarray, y: np.ndarray, a_hat: float, b_hat: float,
                                  outlier_indices: list[int] | np.ndarray) -> plt.Figure:
    """
    產生 matplotlib 圖：
      - 散點（Generated Data）
      - 紅色回歸線（Linear Regression）
      - 以紫色標出前 5 大離群點，並註記 Outlier <index>
    """
    fig, ax = plt.subplots(figsize=(11, 6))

    # 散點
    ax.scatter(x, y, alpha=0.7, label="Generated Data")

    # 回歸線（用排序後的 x 產生平滑直線）
    xs = np.linspace(0.0, 10.0, 200)
    ys = a_hat * xs + b_hat
    ax.plot(xs, ys, "r-", linewidth=2, label="Linear Regression")  # 回歸線用紅色

    # 標註離群點
    if len(outlier_indices) > 0:
        xo = x[outlier_indices]
        yo = y[outlier_indices]
        ax.scatter(xo, yo, s=80, edgecolor="black", facecolor="purple", zorder=5)
        for idx, xi, yi in zip(outlier_indices, xo, yo):
            ax.annotate(f"Outlier {idx}", (xi, yi),
                        textcoords="offset points", xytext=(5, 8), fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", alpha=0.8, lw=0))

    ax.set_title("Linear Regression with Outliers")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


# ------------------------------
# 主流程（整合 CRISP-DM 步驟）
# ------------------------------

# Step 2: Data Understanding（& 產生資料）
x, y, b_true = generate_data(n=n, a=a_true, var=var, seed=42, b=5.0)

# Step 4（含 Step 3）: 建模
model, y_pred, a_hat, b_hat = fit_linear_regression(x, y)

# 取前 5 大離群點（依 |residual|）
residuals_full = y - y_pred
top_k = min(5, len(x))
top_idx = np.argsort(-np.abs(residuals_full))[:top_k]

# 視覺化（Deployment）
st.subheader("Generated Data and Linear Regression")
fig = plot_regression_with_outliers(x, y, a_hat, b_hat, top_idx)
st.pyplot(fig, use_container_width=True)

# 數值區塊：模型係數
st.markdown("---")
st.subheader("Model Coefficients")
col1, col2 = st.columns(2)
with col1:
    st.metric("Coefficient (a)", f"{a_hat:.2f}")
with col2:
    st.metric("Intercept (b)", f"{b_hat:.2f}")

# 離群點表格
st.subheader("Top 5 Outliers")
outliers_df = get_top_outliers(x, y, y_pred, k=5)
st.dataframe(outliers_df, use_container_width=True)

# 結語（註解說明）
# ------------------------------
# CRISP-DM Step 6: Deployment
# 本檔即為可直接部署的單檔 Streamlit App。深色/淺色主題可用 Streamlit 偏好切換；
# 圖表色彩簡潔，回歸線使用紅色，離群點以紫色標出並加上 Outlier <index> 註記。