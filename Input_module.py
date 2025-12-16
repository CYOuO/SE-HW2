import os
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, font # 導入 font 模組來設定字體

# --- 配置 (Configuration) ---
DATA_FILE = 'expenses.csv'
FIELDNAMES = ['date', 'amount', 'category', 'notes']
DATE_FORMAT = '%Y-%m-%d'

# --- 數據初始化 (Data Initialization) ---
# ... (initialize_data_file 函數不變) ...
def initialize_data_file():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=FIELDNAMES).to_csv(DATA_FILE, index=False, encoding='utf_8_sig')
        print(f"已創建新的數據文件: {DATA_FILE}")

# --- GUI 應用程序邏輯 (GUI Application Logic) ---

class ExpenseApp:
    def __init__(self, master):
        self.master = master
        master.title("💰 費用輸入工具 (Member A)")

        # --- 定義自定義字體和間距 ---
        # 放大字體大小 (例如 14)
        self.entry_font = font.Font(family="Helvetica", size=14) 
        # 增加間距值
        self.padding_x = 10 
        self.padding_y = 10
        self.new_width = 25 # 調整寬度以配合更大的字體 (25 個字元)

        # 確保數據文件存在
        initialize_data_file()

        # --- 標籤 (Labels): 應用更大的字體和間距 ---
        
        # 日期
        tk.Label(master, text="日期 (YYYY-MM-DD):", font=self.entry_font).grid(
            row=0, column=0, padx=self.padding_x, pady=self.padding_y, sticky='w'
        )
        # 金額
        tk.Label(master, text="金額:", font=self.entry_font).grid(
            row=1, column=0, padx=self.padding_x, pady=self.padding_y, sticky='w'
        )
        # 類別
        tk.Label(master, text="類別:", font=self.entry_font).grid(
            row=2, column=0, padx=self.padding_x, pady=self.padding_y, sticky='w'
        )
        # 備註
        tk.Label(master, text="備註 (可選):", font=self.entry_font).grid(
            row=3, column=0, padx=self.padding_x, pady=self.padding_y, sticky='w'
        )

        # --- 輸入框 (Entry Fields): 應用更大的字體和寬度、間距 ---
        
        self.date_entry = tk.Entry(master, font=self.entry_font, width=self.new_width)
        self.date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.date_entry.grid(row=0, column=1, padx=self.padding_x, pady=self.padding_y)

        self.amount_entry = tk.Entry(master, font=self.entry_font, width=self.new_width)
        self.amount_entry.grid(row=1, column=1, padx=self.padding_x, pady=self.padding_y)

        self.category_entry = tk.Entry(master, font=self.entry_font, width=self.new_width)
        self.category_entry.grid(row=2, column=1, padx=self.padding_x, pady=self.padding_y)

        self.notes_entry = tk.Entry(master, font=self.entry_font, width=self.new_width)
        self.notes_entry.grid(row=3, column=1, padx=self.padding_x, pady=self.padding_y)

        # 儲存按鈕 (Save Button): 應用更大的字體
        self.save_button = tk.Button(master, text="儲存費用", command=self.save_expense, font=self.entry_font)
        # 按鈕通常在底下一行，將其 pady 設得更大一些
        self.save_button.grid(row=4, column=0, columnspan=2, pady=self.padding_y * 2)


    # ... (中略：validate_input 函數不變) ...
    def validate_input(self, date_str, amount_str, category):
        """驗證用戶輸入的數據"""
        errors = []
        
        # 1. 日期驗證
        try:
            datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            errors.append(f"日期格式無效。請使用 {DATE_FORMAT} 格式。")

        # 2. 金額驗證
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("金額必須是正數。")
        except ValueError:
            errors.append("金額必須是有效的數字。")
        except UnboundLocalError: # 如果 amount_str 是空字串，這裡會捕獲
            errors.append("金額不能為空。")

        # 3. 類別驗證
        if not category.strip():
            errors.append("類別不能為空。")
            
        return errors
        
        
    def show_custom_success(self, message):
        """
        自定義的成功彈窗，用於替代標準 messagebox，並可以控制大小。
        """
        # 創建一個新的頂層視窗
        success_window = tk.Toplevel(self.master)
        success_window.title("操作成功")
        
        # 設置視窗大小 (控制視窗大小)
        success_window.geometry("300x150")
        
        # 阻止主視窗操作 (模態視窗)
        success_window.grab_set() 
        
        # 設定更大的字體
        custom_font = font.Font(size=14, weight='bold')

        # 顯示成功訊息
        tk.Label(success_window, text="✅ 成功!", font=custom_font, 
                 fg="green", pady=10).pack()
                 
        tk.Label(success_window, text=message, font=font.Font(size=12)).pack(pady=5)
        
        # 確定按鈕，點擊後關閉彈窗
        tk.Button(success_window, text="確定", command=success_window.destroy, 
                  width=10).pack(pady=10)

        # 將焦點設置到這個視窗上
        success_window.focus_set()

    def show_custom_error(self, title, message):
        """
        自定義的錯誤彈窗，使用與成功彈窗相同的 Toplevel 結構和大小。
        """
        # 創建一個新的頂層視窗
        error_window = tk.Toplevel(self.master)
        error_window.title(title)
        
        # 設置視窗大小 (保持與 success 視窗一致)
        error_window.geometry("300x150")
        
        # 阻止主視窗操作 (模態視窗)
        error_window.grab_set() 
        
        # 設定更大的字體
        custom_font = font.Font(size=14, weight='bold')

        # 顯示錯誤訊息 (使用紅色)
        tk.Label(error_window, text="❌ 錯誤!", font=custom_font, 
                 fg="red", pady=10).pack()
                 
        # 顯示詳細錯誤內容
        tk.Label(error_window, text=message, font=font.Font(size=10)).pack(pady=5)
        
        # 確定按鈕，點擊後關閉彈窗
        tk.Button(error_window, text="確定", command=error_window.destroy, 
                  width=10).pack(pady=10)

        # 將焦點設置到這個視窗上
        error_window.focus_set()


    def save_expense(self):
        """從輸入框獲取數據，驗證，並保存到 CSV 文件。"""
        # --- 變數聲明與賦值 ---
        date_str = self.date_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        category = self.category_entry.get().strip()
        notes = self.notes_entry.get().strip()
        
        # 進行驗證
        errors = self.validate_input(date_str, amount_str, category)

        if errors:
            self.show_custom_error("輸入錯誤", "\n".join(errors))
            return
        
        try:
            amount = round(float(amount_str), 2)
            
            new_expense = {
                'date': date_str,
                'amount': amount,
                'category': category,
                'notes': notes
            }

            # 1. 嘗試讀取現有的數據
            try:
                # 讀取現有數據時，指定 UTF-8 編碼 (如果你使用 CSV)
                df = pd.read_csv(DATA_FILE, encoding='utf_8_sig') 
            except (pd.errors.EmptyDataError, FileNotFoundError):
                # 處理空文件或不存在的情況 (避免 FutureWarning)
                dtype_dict = {name: object for name in FIELDNAMES}
                df = pd.DataFrame(columns=FIELDNAMES).astype(dtype_dict)

            # 2. 創建包含新數據的 DataFrame
            new_df = pd.DataFrame([new_expense])
            
            # 3. 使用 pd.concat 進行數據追加
            df = pd.concat([df, new_df], ignore_index=True)
            
            # 4. 將合併後的完整 DataFrame 寫回文件
            df.to_csv(DATA_FILE, index=False, encoding='utf_8_sig')

            # 成功訊息：使用自定義的 Toplevel 視窗
            self.show_custom_success("費用已成功添加！")
            
            # 清空輸入欄位
            self.amount_entry.delete(0, tk.END)
            self.category_entry.delete(0, tk.END)
            self.notes_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.now().strftime(DATE_FORMAT)) 

        except Exception as e:
            self.show_custom_error("保存錯誤", f"保存數據時出錯: {e}")


# --- 運行應用 (Run the App) ---

if __name__ == '__main__':
    root = tk.Tk()
    app = ExpenseApp(root)
    root.mainloop()