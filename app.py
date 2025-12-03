import streamlit as st
import requests
import pandas as pd
import os
import sys
from datetime import datetime

# Suppress SSL warnings (only when verify=False is used for testing)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_api_key_from_config():
    # Priority: st.secrets -> environment variable -> None
    key = None
    try:
        key = st.secrets.get("CWB_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.environ.get("CWB_API_KEY")
    return key
DATASET_ID = "F-C0032-001"
BASE_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"


def find_locations(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'location' and isinstance(v, list) and v and isinstance(v[0], dict) and 'locationName' in v[0]:
                return v
            res = find_locations(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_locations(item)
            if res:
                return res
    return None


def extract_location_row_values(location):
    elements = {}
    times_index = []
    weather_elements = location.get('weatherElement') or location.get('weatherElement', [])
    for elem in weather_elements:
        name = elem.get('elementName') or elem.get('elementName') or elem.get('elementName')
        times = elem.get('time') or elem.get('times') or []
        elements[name] = times
        if not times_index and isinstance(times, list):
            times_index = times

    rows = []
    for i, t in enumerate(times_index):
        row = {}
        row['startTime'] = t.get('startTime') or t.get('dataTime') or ''
        row['endTime'] = t.get('endTime') or ''
        for elem_name, times in elements.items():
            val = ''
            if i < len(times):
                entry = times[i]
                if 'parameter' in entry and isinstance(entry['parameter'], dict):
                    val = entry['parameter'].get('parameterName') or entry['parameter'].get('parameterValue') or str(entry['parameter'])
                elif 'elementValue' in entry and isinstance(entry['elementValue'], list) and entry['elementValue']:
                    v = entry['elementValue'][0]
                    val = v.get('value') or v.get('measures') or str(v)
                elif 'parameterName' in entry:
                    val = entry.get('parameterName')
                elif 'value' in entry:
                    val = entry.get('value')
                else:
                    val = str(entry)
            row[elem_name] = val
        rows.append(row)
    return rows


def fetch_data(api_key):
    params = {"Authorization": api_key}
    # Return the full Response so the caller can inspect URL/status for debugging
    # Note: verify=False disables SSL certificate verification (use with caution, only for testing)
    r = requests.get(BASE_URL, params=params, timeout=15, verify=False)
    return r


def main():
    st.set_page_config(page_title="今明36小時天氣預報", layout="wide")
    st.title("今明36小時天氣預報")

    with st.sidebar:
        st.header("設定")
        configured_key = get_api_key_from_config()
        if configured_key:
            st.success("已從 `st.secrets` 或環境變數讀取 API Key（隱藏）。")
        else:
            st.warning("未設定 API Key。請在 `.streamlit/secrets.toml` 設定 `CWB_API_KEY` 或設定環境變數 `CWB_API_KEY`。\n\n若沒有金鑰，請使用下方的 JSON 上傳備援。")
        # No manual input anymore — only secrets/env is used
        api_key = configured_key

    # If there is no api_key configured, allow user to upload a previously
    # downloaded JSON as a fallback and skip the network fetch.
    if not api_key:
        st.info("未找到 API Key；請上傳先前從氣象資料開放平台下載的 JSON 作為備援，或設定 `CWB_API_KEY`。")
        uploaded_local = st.file_uploader("上傳 CWB JSON 檔案 (備援)", type=["json"])
        if uploaded_local is not None:
            try:
                import json
                data = json.load(uploaded_local)
                st.success("已載入上傳的 JSON（備援）。")
            except Exception as ex:
                st.error(f"解析上傳的 JSON 失敗: {ex}")
                return
        else:
            return

    data = None
    try:
        data_load_state = st.info("從氣象資料開放平台抓取資料中...")
        resp = fetch_data(api_key)
        data_load_state.empty()

        # Print to stderr (PowerShell terminal) for debugging
        sys.stderr.write(f"\n[DEBUG] Request URL: {resp.url}\n")
        sys.stderr.write(f"[DEBUG] HTTP status: {resp.status_code}\n\n")
        sys.stderr.flush()

        # Show debug info: actual request URL and HTTP status
        with st.expander("Request Debug (點此查看請求 URL 與狀態)"):
            st.code(resp.url)
            st.write(f"HTTP status: {resp.status_code}")

        # Handle response
        try:
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as http_err:
            st.error(f"伺服器回應錯誤: {http_err} (status {resp.status_code})")
            # try to show body if available
            try:
                st.write(resp.text[:1000])
            except Exception:
                pass
            st.info("你可以上傳先前從 API 取得的 JSON 檔作為備援，或檢查本機網路/Proxy 設定。")
            uploaded = st.file_uploader("上傳 CWB JSON 檔案 (備援)", type=["json"])
            if uploaded is not None:
                try:
                    import json
                    data = json.load(uploaded)
                    st.success("已載入上傳的 JSON。")
                except Exception as ex:
                    st.error(f"解析上傳的 JSON 失敗: {ex}")
                    return
            else:
                return
    except Exception as e:
        st.warning(f"抓取資料失敗: {e}")
        st.info("你可以上傳先前從 API 取得的 JSON 檔作為備援，或檢查本機網路/Proxy 設定。")
        uploaded = st.file_uploader("上傳 CWB JSON 檔案 (備援)", type=["json"])
        if uploaded is not None:
            try:
                import json
                data = json.load(uploaded)
                st.success("已載入上傳的 JSON。")
            except Exception as ex:
                st.error(f"解析上傳的 JSON 失敗: {ex}")
                return
        else:
            return

    locations = find_locations(data) or []
    if not locations:
        st.error("找不到任何 location 資訊，請確認 dataset id 與回傳結構。")
        st.write(data)
        return

    loc_names = [loc.get('locationName', 'Unknown') for loc in locations]
    selected = st.selectbox("選擇縣市 / 區域 (Location)", loc_names)
    loc = next((l for l in locations if l.get('locationName') == selected), None)
    if not loc:
        st.error("選擇的地點找不到資料。")
        return

    lat = loc.get('lat') or loc.get('latitude')
    lon = loc.get('lon') or loc.get('longitude')
    if lat and lon:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            st.map(pd.DataFrame([[lat_f, lon_f]], columns=['lat', 'lon']))
        except Exception:
            pass

    rows = extract_location_row_values(loc)
    if not rows:
        st.warning("此地點沒有可解析的時間資料，顯示原始資料: ")
        st.json(loc)
        return

    df = pd.DataFrame(rows)
    for c in ['startTime', 'endTime']:
        if c in df.columns:
            try:
                df[c] = pd.to_datetime(df[c])
            except Exception:
                pass

    st.subheader(f"{selected} — 今明36小時預報 (共 {len(df)} 條時段)")
    st.dataframe(df)

    numeric_cols = []
    for col in df.columns:
        if col in ('startTime', 'endTime'):
            continue
        try:
            pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9\.-]', '', regex=True))
            numeric_cols.append(col)
        except Exception:
            continue

    if numeric_cols:
        st.subheader("數值圖表")
        chart_df = df.set_index('startTime')[numeric_cols].apply(lambda s: pd.to_numeric(s.astype(str).str.replace(r'[^0-9\.-]', '', regex=True), errors='coerce'))
        st.line_chart(chart_df)

    st.markdown("---")
    st.markdown("如果需要，可在側邊欄輸入不同的 API Key，或改成使用 `st.secrets` 以保護金鑰。")


if __name__ == '__main__':
    main()
