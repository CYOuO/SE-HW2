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
opened_windows = {} 

# --- 客製化顏色順序 ---
CUSTOM_COLORS = [
    '#F48FB1', '#CE93D8', '#9FA8DA', '#90CAF9', '#A5D6A7', 
    '#FFF59D', '#FFCC80', '#EF9A9A', '#BCAAA4'
]

def darken_color(hex_color, factor=0.6):
    try:
        rgb = mcolors.hex2color(hex_color)
        darker_rgb = [x * factor for x in rgb]
        return darker_rgb
    except:
        return 'black'

def get_expenses_data():
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

def on_window_close(category):
    if category in opened_windows:
        del opened_windows[category]

def show_custom_table(category):
    """顯示詳細視窗 (智慧換行版)"""
    if category in opened_windows:
        win_info = opened_windows[category]
        root = win_info['root']
        if root.winfo_exists():
            root.lift()
            root.focus_force()
            return
        else:
            del opened_windows[category]

    items = current_details.get(category, [])
    
    root = tk.Tk()
    root.title(f"{category} 明細")
    
    # 設定視窗大小
    w, h = 900, 600
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
    root.configure(bg="white") 
    
    root.protocol("WM_DELETE_WINDOW", lambda: [root.destroy(), on_window_close(category)])

    try:
        cat_index = current_labels.index(category)
        color_idx = cat_index % len(CUSTOM_COLORS)
        title_color = darken_color(CUSTOM_COLORS[color_idx], factor=0.7) 
        hex_title_color = mcolors.to_hex(title_color)
    except:
        hex_title_color = "#34495E"

    # --- 標題區 ---
    header_frame = tk.Frame(root, bg="white")
    header_frame.pack(fill=tk.X, pady=20, padx=30)
    
    header_label = tk.Label(header_frame, text=f"📂 {category}", 
             font=("Microsoft JhengHei", 24, "bold"), 
             bg="white", fg=hex_title_color)
    header_label.pack(side=tk.LEFT)

    # --- 可捲動內容區 ---
    container = tk.Frame(root, bg="white")
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    canvas = tk.Canvas(container, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    
    # 這裡不設定固定寬度，讓它自動適應
    scrollable_frame = tk.Frame(canvas, bg="white")

    # 🔧 關鍵修正 1：讓 scrollable_frame 的寬度永遠等於 canvas 的寬度
    # 這樣內容就不會超出視窗邊緣
    frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _configure_canvas(event):
        # 更新捲動範圍
        canvas.configure(scrollregion=canvas.bbox("all"))
        # 強制內層 Frame 寬度等於 Canvas 寬度
        canvas.itemconfig(frame_id, width=event.width)

    canvas.bind("<Configure>", _configure_canvas)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    opened_windows[category] = {
        'root': root,
        'frame': scrollable_frame,
        'header_label': header_label
    }

    refresh_table_content(category, items)

def refresh_table_content(category, items):
    if category not in opened_windows: return
    
    win_info = opened_windows[category]
    frame = win_info['frame']
    header_label = win_info['header_label']
    
    for widget in frame.winfo_children():
        widget.destroy()
        
    total = 0
    sorted_items = sorted(items, key=lambda x: x[0], reverse=True)
    
    # --- 表頭 ---
    # 使用 Grid 排版，確保對齊
    header_row = tk.Frame(frame, bg="#EEEEEE", pady=10) 
    header_row.pack(fill=tk.X, expand=True)
    
    # 設定 Grid 權重，讓備註欄位(Column 2)自動伸縮
    header_row.grid_columnconfigure(0, minsize=150) # 日期
    header_row.grid_columnconfigure(1, minsize=120) # 金額
    header_row.grid_columnconfigure(2, weight=1)    # 備註 (伸縮)

    tk.Label(header_row, text="日期", font=("Microsoft JhengHei", 14, "bold"), 
             bg="#EEEEEE", anchor="center").grid(row=0, column=0, sticky="ew")
    tk.Label(header_row, text="金額", font=("Microsoft JhengHei", 14, "bold"), 
             bg="#EEEEEE", anchor="center").grid(row=0, column=1, sticky="ew")
    tk.Label(header_row, text="備註", font=("Microsoft JhengHei", 14, "bold"), 
             bg="#EEEEEE", anchor="w").grid(row=0, column=2, sticky="ew", padx=20)

    # --- 資料行 ---
    for i, (date, amt, note) in enumerate(sorted_items):
        total += amt
        bg_color = "#F9F9F9" if i % 2 == 0 else "white"
        
        row_frame = tk.Frame(frame, bg=bg_color, pady=15)
        row_frame.pack(fill=tk.X, expand=True)
        
        row_frame.grid_columnconfigure(0, minsize=150)
        row_frame.grid_columnconfigure(1, minsize=120)
        row_frame.grid_columnconfigure(2, weight=1) # 關鍵：備註欄位佔滿剩餘空間

        # 1. 日期
        tk.Label(row_frame, text=date, font=("Microsoft JhengHei", 14), 
                 bg=bg_color, anchor="center").grid(row=0, column=0, sticky="ew")
        
        # 2. 金額
        tk.Label(row_frame, text=f"${int(amt):,}", font=("Microsoft JhengHei", 14, "bold"), fg="#E74C3C",
                 bg=bg_color, anchor="center").grid(row=0, column=1, sticky="ew")
        
        # 3. 備註 (🔧 關鍵修正 2：動態 Wraplength)
        note_label = tk.Label(row_frame, text=note, font=("Microsoft JhengHei", 14), 
                 bg=bg_color, anchor="w", justify="left")
        note_label.grid(row=0, column=2, sticky="ew", padx=20)
        
        # 這個神奇的指令會監聽視窗變化，自動計算該在哪裡換行
        # e.width - 10 表示：只要寬度一變，換行點就設為「當前寬度 - 10px」
        note_label.bind('<Configure>', lambda e: e.widget.configure(wraplength=e.width-10))

        ttk.Separator(frame, orient='horizontal').pack(fill='x')

    header_label.config(text=f"📂 {category} (總計: ${int(total):,})")

def update_open_tables(all_details):
    for category in list(opened_windows.keys()):
        if category in all_details:
            new_items = all_details[category]
            refresh_table_content(category, new_items)

def update_chart(frame):
    global current_wedges, current_texts, current_autotexts, current_labels, current_details
    totals, details = get_expenses_data()
    if totals == "NO_CHANGE" or totals is None: return

    ax.clear()
    current_details = details
    labels = list(totals.keys())
    sizes = list(totals.values())
    current_labels = labels

    update_open_tables(details)

    if not sizes:
        ax.text(0.5, 0.5, "等待資料輸入...", ha='center', va='center', fontsize=14, color='gray')
        return

    is_single = len(sizes) <= 1
    edge_width = 0 if is_single else 2

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140,
        colors=CUSTOM_COLORS, pctdistance=0.8, labeldistance=1.1
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
        autotexts[i].set_path_effects([path_effects.withStroke(linewidth=2, foreground=text_color)])

    current_wedges = wedges
    current_texts = texts
    current_autotexts = autotexts
    ax.set_title('支出圓餅圖', fontsize=18, fontweight='bold', pad=20, color='#555')
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
    plt.show()