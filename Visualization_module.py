import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
import os  # 這行原本少了，補回來了
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict

# --- 設定對接 Member A 的檔案 ---
# 這是你 Member A 產生的檔案名稱
DATA_FILE = 'expenses.csv' 

# 全域變數
current_wedges = []
current_labels = []
current_details = {}
last_modified_time = 0

def get_expenses_data():
    """讀取資料，只有檔案真的變更時才讀取"""
    global last_modified_time
    
    if not os.path.exists(DATA_FILE):
        return None, None

    try:
        # 檢查檔案最後修改時間，沒變就不讀
        file_mtime = os.path.getmtime(DATA_FILE)
        if file_mtime == last_modified_time:
            return "NO_CHANGE", "NO_CHANGE"
        last_modified_time = file_mtime
    except OSError:
        return None, None

    category_data = defaultdict(list)
    category_totals = defaultdict(float)

    try:
        with open(DATA_FILE, mode='r', encoding='utf_8_sig') as file:
            reader = csv.DictReader(file)
            
            if not reader.fieldnames:
                return None, None
            
            # 欄位轉小寫處理 (防呆)
            fieldnames = [f.lower() for f in reader.fieldnames]

            if 'category' not in fieldnames:
                return None, None

            for row in reader:
                try:
                    # 處理大小寫並讀取
                    row_lower = {k.lower(): v for k, v in row.items()}
                    
                    amount = float(row_lower['amount'])
                    category = row_lower['category']
                    date = row_lower['date']
                    note = row_lower.get('notes', '')
                    
                    if category:
                        category_totals[category] += amount
                        category_data[category].append((date, amount, note))
                except (ValueError, KeyError):
                    continue
    except Exception:
        return None, None

    return category_totals, category_data

def show_details_popup(category):
    """點擊圓餅圖後跳出的視窗"""
    items = current_details.get(category, [])
    
    root = tk.Tk()
    root.title(f"{category} 明細")
    
    w, h = 350, 250
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

    text_area = tk.Text(root, font=("Microsoft JhengHei", 11), padx=10, pady=10)
    scrollbar = tk.Scrollbar(root, command=text_area.yview)
    text_area.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    text_area.insert(tk.END, f"【{category}】\n", "header")
    text_area.insert(tk.END, "-"*25 + "\n")
    
    total = 0
    for date, amt, note in items:
        total += amt
        note_str = f" ({note})" if note else ""
        text_area.insert(tk.END, f"{date} | ${int(amt)}{note_str}\n")
    
    text_area.insert(tk.END, "-"*25 + "\n")
    text_area.insert(tk.END, f"總計: ${int(total)}", "total")

    text_area.tag_config("header", foreground="blue", font=("Microsoft JhengHei", 12, "bold"))
    text_area.tag_config("total", foreground="red", font=("Microsoft JhengHei", 11, "bold"))
    text_area.config(state=tk.DISABLED)
    root.mainloop()

def update_chart(frame):
    """動畫核心：自動檢查資料"""
    global current_wedges, current_labels, current_details
    
    totals, details = get_expenses_data()
    
    if totals == "NO_CHANGE" or totals is None:
        return

    ax.clear()
    
    current_details = details
    labels = list(totals.keys())
    sizes = list(totals.values())
    current_labels = labels

    if not sizes:
        ax.text(0.5, 0.5, "等待資料輸入...", ha='center', va='center', fontsize=12)
        return

    # --- 這裡修正了原本報錯的地方 ---
    # 1. 移除了 picker=True
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    
    # 2. 改用手動設定 picker (這在所有版本都不會報錯)
    for wedge in wedges:
        wedge.set_picker(True)
    
    current_wedges = wedges
    # -----------------------------

    ax.set_title('支出即時監控', fontsize=16, fontweight='bold')
    ax.axis('equal') 

def on_click(event):
    if event.mouseevent.button != 1: return
    for i, wedge in enumerate(current_wedges):
        # 檢查是否點擊到了區塊
        if wedge.contains(event.mouseevent)[0]:
            category = current_labels[i]
            show_details_popup(category)
            break

if __name__ == "__main__":
    # 設定中文字型
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei'] 
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(8, 6))
    
    fig.canvas.mpl_connect('pick_event', on_click)
    
    ani = animation.FuncAnimation(fig, update_chart, interval=1000, cache_frame_data=False)

    print("圖表程式已啟動...請確保 expenses.csv 在同一個資料夾")
    plt.show()