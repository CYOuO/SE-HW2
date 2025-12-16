import os
import pandas as pd
from datetime import datetime

# --- 配置 (Configuration) ---
DATA_FOLDER = r'C:\資料庫導論' 
DATA_FILE = os.path.join(DATA_FOLDER, 'expenses.csv')
FIELDNAMES = ['date', 'amount', 'category', 'notes']
DATE_FORMAT = '%Y-%m-%d'

# --- 數據初始化 (Data Initialization) ---

def initialize_data_file():
    """確保數據文件和文件夾存在，如果不存在則創建。"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    if not os.path.exists(DATA_FILE):
        # 寫入時使用 utf_8_sig 確保 Excel 開啟時中文不亂碼
        pd.DataFrame(columns=FIELDNAMES).to_csv(DATA_FILE, index=False, encoding='utf_8_sig')
        print(f"已創建新的數據文件: {DATA_FILE}")

# --- 核心輸入與保存邏輯 (Core Input & Save Logic) ---

def input_expense():
    """
    接收用戶在命令行中的費用輸入，進行驗證並保存到 CSV 文件。
    """
    print("\n--- 💰 輸入新的費用 ---")
    
    # 循環直到輸入有效
    while True:
        try:
            # 1. 日期輸入與驗證
            date_str = input(f"請輸入日期 ({DATE_FORMAT}, 例如 {datetime.now().strftime(DATE_FORMAT)}): ").strip()
            if not date_str: continue
            datetime.strptime(date_str, DATE_FORMAT)
            
            # 2. 金額輸入與驗證
            amount_str = input("請輸入金額 (必須是正數): ").strip()
            if not amount_str: continue
            amount = float(amount_str)
            if amount <= 0:
                print("金額必須是正數。")
                continue
            
            # 3. 類別輸入與驗證
            category = input("請輸入類別 (例如 食物, 交通): ").strip()
            if not category: continue
            
            # 4. 備註 (可選)
            notes = input("請輸入備註 (可選): ").strip()

            break # 輸入驗證通過，跳出循環

        except ValueError as e:
            print(f"\n[❌ 錯誤] 輸入無效: {e}. 請重新輸入。\n")
        except Exception as e:
            print(f"\n[❌ 系統錯誤] {e}. 請重新輸入。\n")

    # --- 數據保存邏輯 (已優化) ---
    new_expense = {
        'date': date_str,
        'amount': round(amount, 2),
        'category': category,
        'notes': notes
    }

    try:
        # 1. 嘗試讀取現有的數據 (處理空文件和編碼)
        try:
            # 讀取時使用 utf_8_sig
            df = pd.read_csv(DATA_FILE, encoding='utf_8_sig')
        except (pd.errors.EmptyDataError, FileNotFoundError):
            # 處理空文件或不存在的情況 (設置 dtype 避免 FutureWarning)
            dtype_dict = {name: object for name in FIELDNAMES}
            df = pd.DataFrame(columns=FIELDNAMES).astype(dtype_dict)

        # 2. 創建包含新數據的 DataFrame
        new_df = pd.DataFrame([new_expense])
        
        # 3. 使用 pd.concat 進行數據追加
        df = pd.concat([df, new_df], ignore_index=True)
        
        # 4. 將合併後的完整 DataFrame 寫回文件 (寫入時使用 utf_8_sig)
        df.to_csv(DATA_FILE, index=False, encoding='utf_8_sig')
        
        print("\n--- ✅ 費用已成功添加！---")
        print(f"記錄: {new_expense}")

    except Exception as e:
        print(f"\n[❌ 錯誤] 保存數據時出錯: {e}")


# --- 主程序入口 (Main Execution) ---

if __name__ == '__main__':
    initialize_data_file()
    
    # 循環讓用戶持續輸入費用
    while True:
        input_expense()
        
        # 詢問是否繼續
        choice = input("\n是否要繼續輸入另一筆費用？ (y/n): ").strip().lower()
        if choice != 'y':
            print("費用輸入程序結束。")
            break