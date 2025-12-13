import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
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

# 【新功能】用來追蹤已開啟的視窗，防止重複開啟 & 用於自動更新
# 格式: { '類別名稱': {'root': window_obj, 'tree': tree_obj, 'label': total_label_obj} }
opened_windows = {}

# --- 客製化顏色順序 ---
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
        # 這裡我們稍微修改邏輯，如果是為了自動更新表格，我們需要知道資料是不是變了
        # 但為了效能，若沒變回傳 NO_CHANGE 給圖表用，但我們需要把這邏輯跟表格更新分開
        if file_mtime == last_modified_time: 
            return "NO_CHANGE", "NO_CHANGE"
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

def on_window_close(category):
    """當表格視窗關閉時，從追蹤清單中移除"""
    if category in opened_windows:
        del opened_windows[category]

def show_custom_table(category):
    """顯示詳細表格視窗 (單例模式 + 尺寸加大)"""
    
    # 1. 防止重複開啟
    if category in opened_windows:
        win_info = opened_windows[category]
        root = win_info['root']
        # 如果視窗還在，就把它拉到最前面，然後結束函式
        if root.winfo_exists():
            root.lift()
            root.focus_force()
            return
        else:
            # 如果視窗物件在但其實已經關了(意外狀況)，就從清單移除重開
            del opened_windows[category]

    items = current_details.get(category, [])
    
    root = tk.Tk()
    root.title(f"{category} 明細")
    
    # 2. 強制設定大尺寸 (500x600)，比輸入視窗稍大
    w, h = 500, 600
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
    root.configure(bg="#FDFEFE") 
    
    # 設定關閉視窗時的 callback
    root.protocol("WM_DELETE_WINDOW", lambda: [root.destroy(), on_window_close(category)])

    # 標題區
    header_frame = tk.Frame(root, bg="#FDFEFE")
    header_frame.pack(fill=tk.X, pady=20, padx=20)
    
    try:
        cat_index = current_labels.index(category)
        color_idx = cat_index % len(CUSTOM_COLORS)
        title_color = darken_color(CUSTOM_COLORS[color_idx], factor=0.7) 
        hex_title_color = mcolors.to_hex(title_color)
    except:
        hex_title_color = "#34495E"

    tk.Label(header_frame, text=f"📂 {category}", 
             font=("Microsoft JhengHei", 22, "bold"), 
             bg="#FDFEFE", fg=hex_title_color).pack(side=tk.LEFT)

    # 表格樣式
    style = ttk.Style()
    style.theme_use("clam")
    
    # 表頭字體加大
    style.configure("Custom.Treeview.Heading", 
                    font=("Microsoft JhengHei", 14, "bold"),
                    background=hex_title_color, foreground="white", relief="flat")
    
    # 3. 表格內容字體加大 (Size 14) + 行高加高 (RowHeight 50)
    style.configure("Custom.Treeview", 
                    font=("Microsoft JhengHei", 14), 
                    rowheight=50, 
                    background="white", fieldbackground="white", borderwidth=0)
    
    style.map("Custom.Treeview", background=[('selected', '#D6EAF8')])

    columns = ('date', 'amount', 'note')
    tree = ttk.Treeview(root, columns=columns, show='headings', style="Custom.Treeview")

    tree.heading('date', text='📅 日期')
    tree.column('date', width=140, anchor='center')
    
    tree.heading('amount', text='💰 金額')
    tree.column('amount', width=100, anchor='center') 
    
    tree.heading('note', text='📝 備註')
    tree.column('note', width=220, anchor='w')

    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 20))

    # 底部總計 Label
    footer = tk.Frame(root, bg="#ECF0F1", height=60)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    total_label = tk.Label(footer, text="", 
             font=("Microsoft JhengHei", 18, "bold"), 
             bg="#ECF0F1", fg="#E74C3C")
    total_label.pack(side=tk.RIGHT, padx=30, pady=15)

    # 儲存視窗資訊到全域變數，供後續更新使用
    opened_windows[category] = {
        'root': root,
        'tree': tree,
        'label': total_label
    }

    # 首次填入資料
    refresh_table_content(category, items)

def refresh_table_content(category, items):
    """更新特定類別表格的內容"""
    if category not in opened_windows: return
    
    win_info = opened_windows[category]
    tree = win_info['tree']
    total_label = win_info['label']
    
    # 清空舊資料
    for item in tree.get_children():
        tree.delete(item)
        
    total = 0
    sorted_items = sorted(items, key=lambda x: x[0], reverse=True)
    
    tree.tag_configure('odd', background='#F4F6F7')
    tree.tag_configure('even', background='white')

    for i, (date, amt, note) in enumerate(sorted_items):
        total += amt
        tag = 'odd' if i % 2 == 0 else 'even'
        tree.insert('', tk.END, values=(date, f"{int(amt):,}", note), tags=(tag,))
        
    total_label.config(text=f"總計: ${int(total):,}")

def update_open_tables(all_details):
    """【新功能】檢查所有已開啟的視窗，並自動更新它們的資料"""
    # 複製 key 列表以防迭代時修改字典
    for category in list(opened_windows.keys()):
        if category in all_details:
            # 如果這個類別有新資料，就刷新表格
            new_items = all_details[category]
            refresh_table_content(category, new_items)
        else:
            # 如果資料庫裡這類別不見了(極少見)，也可以選擇不做事或清空
            pass

def update_chart(frame):
    global current_wedges, current_texts, current_autotexts, current_labels, current_details
    
    totals, details = get_expenses_data()
    
    # 這裡的邏輯是：如果有新資料 (totals不是字串)，我們就要更新圖表 AND 更新表格
    if totals == "NO_CHANGE" or totals is None: 
        return

    # 1. 更新圖表
    ax.clear()
    
    current_details = details
    labels = list(totals.keys())
    sizes = list(totals.values())
    current_labels = labels

    # 2. 【關鍵】如果有任何表格視窗開著，順便更新它們的內容！
    update_open_tables(details)

    if not sizes:
        ax.text(0.5, 0.5, "等待資料輸入...", ha='center', va='center', fontsize=14, color='gray')
        return

    # 繪製圓餅圖
    is_single = len(sizes) <= 1
    edge_width = 0 if is_single else 2

    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140,
        colors=CUSTOM_COLORS, 
        pctdistance=0.8,
        labeldistance=1.1
    )

    for i, w in enumerate(wedges):
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
            path_effects.withStroke(linewidth=2, foreground=text_color)
        ])

    current_wedges = wedges
    current_texts = texts
    current_autotexts = autotexts

    ax.set_title('支出即時監控', fontsize=18, fontweight='bold', pad=20, color='#555')
    ax.axis('equal') 

def on_hover(event):
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
            # 這裡改成呼叫 show_custom_table，裡面有防止重複的邏輯
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
    print("1. 表格視窗大小已調整為 500x600 (比輸入視窗大)")
    print("2. 字體已加大加粗，確保清晰")
    print("3. 已防止重複開啟相同視窗")
    print("4. 表格開啟狀態下，新增資料會自動更新")
    plt.show()