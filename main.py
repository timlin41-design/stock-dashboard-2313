import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from google.colab import userdata
import datetime

# --- 1. 參數設定 ---
STOCK_ID = '2313'
# 抓取較長的時間範圍以便進行週/月加總
start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')

dl = DataLoader()
df_inst = dl.taiwan_stock_institutional_investors(stock_id=STOCK_ID, start_date=start_date)

# --- 2. 數據整理與重採樣函數 ---
def process_data(df, freq='D'):
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df_temp['diff'] = df_temp['buy'] - df_temp['sell']
    
    # 轉置為以日期為 Index
    pivot = df_temp.pivot_table(index='date', columns='name', values='diff', aggfunc='sum').fillna(0)
    
    # 合併自營商
    d_self = pivot.get('Dealer_self', pd.Series(0, index=pivot.index))
    d_hedge = pivot.get('Dealer_Hedging', pd.Series(0, index=pivot.index))
    pivot['Dealer'] = d_self + d_hedge
    
    # 根據頻率重採樣 (日 D, 週 W, 月 ME)
    if freq != 'D':
        pivot = pivot.resample(freq).sum()
    
    return pivot

df_daily = process_data(df_inst, 'D')
df_weekly = process_data(df_inst, 'W')
df_monthly = process_data(df_inst, 'ME')

# --- 3. 繪製圖表 ---
fig = go.Figure()

colors = {'Foreign_Investor': '#f5b128', 'Investment_Trust': '#f27c7c', 'Dealer': '#5ca1e6'}
labels = {'Foreign_Investor': '外資', 'Investment_Trust': '投信', 'Dealer': '自營商'}

# 建立 Trace 的函數
def add_traces(df, visible=False):
    traces = []
    for col in ['Foreign_Investor', 'Investment_Trust', 'Dealer']:
        traces.append(go.Bar(
            x=df.index.strftime('%Y/%m/%d'),
            y=df[col],
            name=labels[col],
            marker_color=colors[col],
            visible=visible,
            hovertemplate='%{y:,.0f} 張<extra></extra>'
        ))
    return traces

# 加入三組資料 (預設顯示每日)
fig.add_traces(add_traces(df_daily, visible=True))
fig.add_traces(add_traces(df_weekly, visible=False))
fig.add_traces(add_traces(df_monthly, visible=False))

# --- 4. 週期切換按鈕 ---
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0, y=1.15,
            showactive=True,
            buttons=list([
                dict(label="日統計", method="update", args=[{"visible": [True, True, True, False, False, False, False, False, False]}]),
                dict(label="週統計", method="update", args=[{"visible": [False, False, False, True, True, True, False, False, False]}]),
                dict(label="月統計", method="update", args=[{"visible": [False, False, False, False, False, False, True, True, True]}])
            ]),
        )
    ],
    title=f"<b>{STOCK_ID} 法人買賣超 (張) - 多週期切換</b>",
    barmode='relative',
    template='plotly_white',
    hovermode='x unified',
    xaxis=dict(type='category', showgrid=True, gridcolor='#eeeeee'),
    yaxis=dict(showgrid=True, gridcolor='#eeeeee', tickformat='.2s')
)

# --- 5. 匯出 HTML 檔案 ---
html_filename = "2313_institutional_flow.html"
fig.write_html(html_filename, include_plotlyjs="cdn", full_html=True)
print(f"✅ 圖表已成功匯出為：{html_filename}")

fig.show()
