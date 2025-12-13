import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import csv
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from collections import defaultdict

# --- 檔案設定 ---
DATA_FILE = 'expenses.csv'

# 全域變數
current_wedges = []
current_texts = []
current_autotexts = []
current_labels = []
current_details = {}
last_modified_time = 0
hovered_index = -1

# --- 客製化顏色順序 (粉 紫 靛 藍 綠 黃 橙 紅 棕) ---
CUSTOM_COLORS = [
    '#F48FB1', # 粉
    '#CE93D8', # 紫
    '#9FA8DA', # 靛
    '#90CAF9', # 藍
    '#A5D6A7', # 綠
    '#FFF59D', # 黃
    '#FFCC80', # 橙
    '#EF9A9A', # 紅
    '#BCAAA4', # 棕
]

def darken_color(hex_color, factor=0.6):
    """將顏色變深，用於文字"""
    try:
        rgb = mcolors.hex2color(hex_color)
        darker_rgb = [x * factor for x in rgb]
        return darker_rgb
    except:
        return 'black'

def get_expenses_data():
    """讀取資料邏輯"""
    global last_modified_time
    if not os.path.exists(DATA_FILE): return None, None

    try:
        file_mtime = os.path.getmtime(DATA_FILE)
        if file_mtime == last_modified_time: return "NO_CHANGE", "NO_CHANGE"
        last_modified_time = file_mtime
    except OSError: return None, None

    category_data = defaultdict(list)
    category_totals = defaultdict(float)

    try:
        with open(DATA_FILE, mode='r', encoding='utf_8_sig') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames: return None, None
            
            fieldnames = [f.lower() for f in reader.fieldnames]
            if 'category' not in fieldnames: return None, None

            for row in reader:
                try:
                    row_lower = {k.lower(): v for k, v in row.items()}
                    amt = float(row_lower['amount'])
                    cat = row_lower['category']
                    date = row_lower['date']
                    note = row_lower.get('notes', '')
                    if cat:
                        category_totals[cat] += amt
                        category_data[cat].append((date, amt, note))
                except: continue
    except: return None, None

    return category_totals, category_data

def show_custom_table(category):
    """顯示詳細表格視窗"""
    items = current_details.get(category, [])
    
    root = tk.Tk()
    root.title(f"{category} 明細")
    
    # 【修正 2】調整視窗大小接近 Input 視窗 (改為直式 400x550)
    w, h = 400, 550
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
    root.configure(bg="#FDFEFE") 

    # 標題
    header_frame = tk.Frame(root, bg="#FDFEFE")
    header_frame.pack(fill=tk.X, pady=15, padx=15)
    
    try:
        cat_index = current_labels.index(category)
        color_idx = cat_index % len(CUSTOM_COLORS)
        title_color = darken_color(CUSTOM_COLORS[color_idx], factor=0.7) 
        hex_title_color = mcolors.to_hex(title_color)
    except:
        hex_title_color = "#34495E"

    tk.Label(header_frame, text=f"📂 {category}", 
             font=("Microsoft JhengHei", 18, "bold"), 
             bg="#FDFEFE", fg=hex_title_color).pack(side=tk.LEFT)

    # 表格樣式
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure("Custom.Treeview.Heading", 
                    font=("Microsoft JhengHei", 12, "bold"),
                    background=hex_title_color, foreground="white", relief="flat")
    
    # 【修正 3】增加 rowheight 到 50，防止字被切掉
    style.configure("Custom.Treeview", 
                    font=("Microsoft JhengHei", 12), 
                    rowheight=50, 
                    background="white", fieldbackground="white", borderwidth=0)
    
    style.map("Custom.Treeview", background=[('selected', '#D6EAF8')])

    columns = ('date', 'amount', 'note')
    tree = ttk.Treeview(root, columns=columns, show='headings', style="Custom.Treeview")

    tree.heading('date', text='📅 日期')
    tree.column('date', width=100, anchor='center')
    
    # 【修正 1】金額欄位改為置中 (anchor='center')
    tree.heading('amount', text='💰 金額')
    tree.column('amount', width=80, anchor='center') 
    
    tree.heading('note', text='📝 備註')
    tree.column('note', width=180, anchor='w')

    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 15))

    # 填入資料
    total = 0
    sorted_items = sorted(items, key=lambda x: x[0], reverse=True)
    
    tree.tag_configure('odd', background='#F4F6F7')
    tree.tag_configure('even', background='white')

    for i, (date, amt, note) in enumerate(sorted_items):
        total += amt
        tag = 'odd' if i % 2 == 0 else 'even'
        # 金額格式化
        tree.insert('', tk.END, values=(date, f"{int(amt):,}", note), tags=(tag,))

    # 底部總計
    footer = tk.Frame(root, bg="#ECF0F1", height=50)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    tk.Label(footer, text=f"總計: ${int(total):,}", 
             font=("Microsoft JhengHei", 15, "bold"), 
             bg="#ECF0F1", fg="#E74C3C").pack(side=tk.RIGHT, padx=20, pady=10)

    root.mainloop()

def update_chart(frame):
    global current_wedges, current_texts, current_autotexts, current_labels, current_details
    
    totals, details = get_expenses_data()
    if totals == "NO_CHANGE" or totals is None: return

    ax.clear()
    
    current_details = details
    labels = list(totals.keys())
    sizes = list(totals.values())
    current_labels = labels

    if not sizes:
        ax.text(0.5, 0.5, "等待資料輸入...", ha='center', va='center', fontsize=14, color='gray')
        return

    # 繪製圓餅圖
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140,
        colors=CUSTOM_COLORS, 
        pctdistance=0.8,
        labeldistance=1.1
    )

    # 【修正 4】判斷資料筆數，決定是否有白線
    is_single = len(sizes) <= 1
    edge_width = 0 if is_single else 2

    for i, w in enumerate(wedges):
        # 只有多於一塊時才畫白線，不然一整塊圓會有奇怪的切線
        w.set_edgecolor('white')
        w.set_linewidth(edge_width)
        
        face_color = w.get_facecolor()
        text_color = darken_color(face_color, factor=0.45) 
        
        texts[i].set_fontsize(14)        
        texts[i].set_fontweight('bold')
        texts[i].set_color(text_color)
        
        autotexts[i].set_color('white')
        autotexts[i].set_fontweight('bold')
        autotexts[i].set_fontsize(11)
        autotexts[i].set_path_effects([
            import_patheffects().withStroke(linewidth=2, foreground=text_color)
        ])

    current_wedges = wedges
    current_texts = texts
    current_autotexts = autotexts

    ax.set_title('支出即時監控', fontsize=18, fontweight='bold', pad=20, color='#555')
    ax.axis('equal') 

def import_patheffects():
    import matplotlib.patheffects as path_effects
    return path_effects

def on_hover(event):
    """滑鼠懸停特效"""
    global hovered_index
    if event.inaxes != ax: 
        if hovered_index != -1: 
            hovered_index = -1
            for idx, wedge in enumerate(current_wedges):
                wedge.set_alpha(1.0)
                current_texts[idx].set_fontsize(14)
            fig.canvas.draw_idle()
        return

    found = False
    for i, w in enumerate(current_wedges):
        if w.contains(event)[0]:
            found = True
            if hovered_index != i:
                hovered_index = i
                for idx, wedge in enumerate(current_wedges):
                    if idx == i:
                        wedge.set_alpha(1.0) 
                        current_texts[idx].set_fontsize(16) 
                    else:
                        wedge.set_alpha(0.3) 
                        current_texts[idx].set_fontsize(14)
                fig.canvas.draw_idle()
            break
            
    if not found and hovered_index != -1:
        hovered_index = -1
        for idx, wedge in enumerate(current_wedges):
            wedge.set_alpha(1.0)
            current_texts[idx].set_fontsize(14)
        fig.canvas.draw_idle()

def on_click(event):
    """滑鼠點擊偵測"""
    if event.button != 1 or event.inaxes != ax: return
    
    for i, wedge in enumerate(current_wedges):
        if wedge.contains(event)[0]:
            category = current_labels[i]
            show_custom_table(category)
            break

if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei'] 
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(8, 6))
    
    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    
    ani = animation.FuncAnimation(fig, update_chart, interval=1000, cache_frame_data=False)

    print("程式已啟動！設定更新：")
    print("- 表格視窗改為 400x550 (仿收據大小)")
    print("- 表格文字高度加高至 50 (防切字)")
    print("- 金額欄位已置中")
    print("- 單一類別時隱藏白線邊框")
    plt.show()