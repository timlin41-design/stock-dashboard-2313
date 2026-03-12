import os
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime

# --- 1. 取得雲端環境變數 ---
# 這裡取代了原本 Colab 的 userdata，改從 GitHub Secrets 讀取
FUGLE_TOKEN = os.environ.get('FUGLE_TOKEN')

# --- 2. 參數設定 ---
STOCK_ID = '2313'
start_date = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')

dl = DataLoader()
df_inst = dl.taiwan_stock_institutional_investors(stock_id=STOCK_ID, start_date=start_date)

# --- 3. 數據整理 (包含假日移除邏輯) ---
df_inst['diff'] = df_inst['buy'] - df_inst['sell']
df_pivot = df_inst.pivot_table(index='date', columns='name', values='diff', aggfunc='sum').fillna(0)
df_pivot.index = pd.to_datetime(df_pivot.index)

dealer_self = df_pivot.get('Dealer_self', pd.Series(0, index=df_pivot.index))
dealer_hedging = df_pivot.get('Dealer_Hedging', pd.Series(0, index=df_pivot.index))
df_pivot['Dealer'] = dealer_self + dealer_hedging
df_pivot['Total'] = df_pivot.sum(axis=1)

# --- 4. 繪製 Fugle 風格圖表 ---
fig = go.Figure()
colors = {'Foreign_Investor': '#f5b128', 'Investment_Trust': '#f27c7c', 'Dealer': '#5ca1e6'}
labels = {'Foreign_Investor': '外資', 'Investment_Trust': '投信', 'Dealer': '自營商'}

for col in ['Foreign_Investor', 'Investment_Trust', 'Dealer']:
    fig.add_trace(go.Bar(
        x=df_pivot.index,
        y=df_pivot[col],
        name=labels[col],
        marker_color=colors[col],
        hovertemplate='%{y:,.0f} 張<extra></extra>',
    ))

fig.update_layout(
    title=f"<b>{STOCK_ID} 法人買賣超 (自動化更新版)</b>",
    barmode='relative',
    template='plotly_white',
    height=500,
    hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    xaxis=dict(
        type='date',
        showgrid=True,
        gridcolor='#eeeeee',
        tickformat='%m/%d',
        rangebreaks=[dict(bounds=["sat", "mon"])], # 移除週末
        rangeslider=dict(visible=False),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(step="all", label="1Y")
            ])
        )
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#eeeeee',
        zeroline=True,
        zerolinecolor='#999999',
        tickformat='.2s'
    )
)

# --- 5. 輸出為 HTML (GitHub Pages 部署關鍵) ---
# 檔名必須是 index.html，且產生在根目錄
fig.write_html("index.html", include_plotlyjs="cdn", full_html=True)
print("✅ 網頁檔 index.html 產生成功！")
