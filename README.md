# 今明36小時天氣預報 (Streamlit 範例)

說明：這是一個簡單的 Streamlit 應用程式，用來串接「氣象資料開放平台」的「今明36小時天氣預報」資料集 (dataset id: `F-C0032-001`)。

快速開始：

1. 建議使用虛擬環境。
2. 安裝相依套件：

```powershell
pip install -r requirements.txt
```


3. 直接啟動：請先設定 `st.secrets['CWB_API_KEY']` 或環境變數 `CWB_API_KEY`（本範例不再提供側邊欄輸入）：

```powershell
streamlit run app.py
```

使用說明：
- 在側邊欄輸入或貼上你的 CWB API Key，或使用 `st.secrets` / 環境變數 `CWB_API_KEY`。
- 選擇 Location 後，頁面會顯示該地點的時段資料表，並嘗試繪製數值欄位的折線圖與地圖（若包含經緯度）。

注意：如果需要部署到 Streamlit Cloud / 其他平台，請將 API Key 放到平台的 Secret 管理中，並改用 `st.secrets` 讀取。

**部署到 Streamlit Community Cloud**
- **Secrets (UI)**: 在你的 Streamlit 應用頁面，點選 `Manage App` → `Secrets`（或在部署頁面尋找 Secrets/Environment），新增一個 key 名稱為 `CWB_API_KEY` 並貼上你的 API key。
- **本地測試範例**: 可在專案根目錄建立 `.streamlit/secrets.toml`，內容示例如下（不要提交到公開 repo）：

```toml
CWB_API_KEY = "你的_api_key_放在這裡"
```

- **注意**: 請勿將含實際金鑰的 `secrets.toml` 提交到公開版本控制（例如 GitHub）。建議只提交 `secrets.toml.example` 並將真實檔案加入 `.gitignore`。
