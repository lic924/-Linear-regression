# HW1-1: Interactive Linear Regression Visualizer

這是一個使用 **Streamlit** + **scikit-learn** + **matplotlib** 製作的互動式線性迴歸應用程式。  
使用者可以調整資料點數量、線性模型參數與雜訊大小，並即時查看模型擬合結果與離群點。

---

## 📊 功能特色

- 🎛️ **互動式設定**：透過 sidebar 調整  
  - 資料點數 (n)  
  - 斜率 (a_true)  
  - 雜訊變異數 (var)  

- 📈 **視覺化功能**：  
  - 顯示資料點與擬合的線性回歸線  
  - 標記前 5 個離群點（依殘差大小排序）  

- 📑 **數值輸出**：  
  - 顯示模型係數 (Coefficient a) 與截距 (Intercept b)  
  - 提供離群點表格（包含 index、x、y、residuals）  

---

## 🖼️ Prompt截圖

### 1. 先將問題打給LLM，請他輸出合適的prompt
![Prompt 截圖](images/1.jpg)



---

### 2. 線性回歸擬合
![回歸結果](images/regression.jpg)

> 上圖：顯示擬合出的紅色回歸線，並以紫色標記離群點。

---

### 3. 模型係數與離群點表格
![係數與離群點](images/outliers.jpg)

> 上圖：模型係數顯示與前 5 大離群點表格。

---

## ⚙️ 安裝與執行

1. 下載此專案  
   ```bash
   git clone https://github.com/lic924/linear_regression_app.git
   cd linear_regression_app
