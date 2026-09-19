import cv2
import numpy as np
import pytesseract
import win32gui
import mss
import time
import pyautogui
import keyboard
import os
import difflib
import obsws_python as obs
pyautogui.FAILSAFE = False
# ================= 參數設定區 =================
import sys # 在最上方 import 區塊加入這行

# ================= 參數設定區 =================
# 1. 自動定位 Tesseract 執行檔路徑 (支援 PyInstaller 打包與管理員權限)
if getattr(sys, 'frozen', False):
    # 如果是被 PyInstaller 打包成 EXE 執行
    base_path = os.path.dirname(sys.executable)
else:
    # 如果是在開發環境 (Python 腳本) 執行
    base_path = os.path.dirname(os.path.abspath(__file__))

# 將當前路徑與 Tesseract-OCR 資料夾組合
tesseract_path = os.path.join(base_path, "Tesseract-OCR", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_path

WINDOW_TITLE = "原神"

# 2. OBS 預設連線設定
OBS_HOST = "localhost"
OBS_PORT = 4455

# 3. 角色字典
VALID_CHARACTERS = ["亞羅伊","薇斯納","奧黛塔","旅行者/冰","阿羅夏","桑多涅","洛恩","尼可","布倫妮","莉奈婭","法爾伽","茲白","葉洛亞","哥倫比婭","杜林","雅珂達","奈芙爾","奇偶","菲林斯","菈烏瑪","愛諾","伊涅芙","絲柯克","塔利雅","愛可菲","伊法","瓦雷莎","伊安珊","夢見月瑞希","藍硯","瑪薇卡","茜特菈莉","旅行者/火","恰斯卡","歐洛倫","希諾寧","基尼奇","瑪拉妮","卡齊娜","艾梅莉埃","希格雯","克洛琳德","賽索斯","阿蕾奇諾","千織","閒雲","嘉明","夏沃蕾","娜維婭","芙寧娜","夏洛蒂","萊歐斯利","那維萊特","菲米尼","林尼","旅行者/水","琳妮特","綺良良","白朮","卡維","米卡","迪希雅","艾爾海森","瑤瑤","流浪者","琺露珊","萊依拉","納西妲","妮露","賽諾","坎蒂絲","多莉","旅行者/草","提納里","柯萊","鹿野院平藏","久岐忍","夜蘭","神里綾人","八重神子","申鶴","雲堇","荒瀧一斗","五郎","托馬","珊瑚宮心海","埃洛伊","雷電將軍","九條裟羅","宵宮","早柚","神里綾華","旅行者/雷","楓原萬葉","優菈","煙緋","羅莎莉亞","胡桃","魈","甘雨","阿貝多","鍾離","辛焱","達達利亞","迪奧娜","可莉","溫迪","迪盧克","七七","琴","旅行者/風","莫娜","旅行者/岩","刻晴","旅行者","香菱","行秋","雷澤","安柏","凝光","菲謝爾","麗莎","砂糖","諾艾爾","凱亞","班尼特","芭芭拉","北斗","重雲"]

# ==============================================

def get_window_rect(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        return None
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return (left, top, right, bottom)

# ==========================================================
# 互動式設定與提醒
# ==========================================================
os.system('cls' if os.name == 'nt' else 'clear')
print("==================================================")
print("【事前設定與確認】")
print("1. 隊伍配置：請確保第一位是「奇偶」，第二位是「主角」，第三位是「安柏」。")
print("2. 視窗設定：請將遊戲解析度設為 1920x1080 (視窗或無邊框)。")
print("3. 角色狀態：請確認所有角色的「武器」已配置正確。")
print("4. OBS 設定：請確認 OBS 已開啟，並成功擷取到原神視窗。")
print("==================================================")
input("✅ 確認完畢後，請按 Enter 鍵繼續...")

print("\n【OBS WebSocket 連線設定】")
print("提示：在 OBS 點選上方選單 [工具] -> [WebSocket 伺服器設定]，")
print("勾選「啟用」，並點擊「顯示連線資訊」將其複製密碼。")
OBS_PASSWORD = input("請貼上您的 OBS 密碼 (若無設定請直接按 Enter): ").strip()

sct = mss.MSS()
seen_names = []
timeline_records = []
skip_phase1 = False

# ==========================================================
# 啟動前詢問：是否讀取既有名單
# ==========================================================
list_filename = "characters_list.txt"
if os.path.exists(list_filename):
    print(f"\n偵測到既有名單 '{list_filename}'。")
    choice = input("是否直接讀取該名單並跳過掃描階段，直接開始錄影？(y/n): ").strip().lower()
    
    if choice == 'y':
        try:
            with open(list_filename, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("---"):
                        continue
                    if ". " in line:
                        name = line.split(". ", 1)[1].replace('\n', '')
                        seen_names.append(name)
            
            if seen_names:
                print(f"成功載入 {len(seen_names)} 名角色！將直接進入階段二 (錄影)。")
                skip_phase1 = True
            else:
                print("[警告] 名單內沒有找到角色，將重新開始掃描。")
        except Exception as e:
            print(f"[錯誤] 讀取檔案失敗 ({e})，將重新開始掃描。")

print("\n⚠️ 設定完成！請將畫面切換至原神...")
for i in range(3, 0, -1):
    print(f"倒數 {i} 秒...")
    time.sleep(1)

# ==========================================================
# 階段一：掃描角色清單 (若未跳過)
# ==========================================================
phase1_interrupted = False

if not skip_phase1:
    # 注意：這裡將中斷鍵改為 'esc'，避免與遊戲內的 'q' 鍵衝突
    print("\n=== [階段一] 開始掃描名單 (按 'Esc' 提早中斷) ===")
    
    seen_names = ["奇偶", "主角"]
    empty_count = 0
    target_character = None  

    print("跳過前兩位不須辨識的角色...")
    pyautogui.press('e')
    time.sleep(0.2)
    pyautogui.press('e')
    time.sleep(0.2)
    print("從第 3 位角色開始執行 OCR 辨識！")

    while True:
        if keyboard.is_pressed('esc'):
            print("使用者手動中斷階段一。")
            phase1_interrupted = True
            break

        rect = get_window_rect(WINDOW_TITLE)
        if not rect:
            time.sleep(1)
            continue

        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        if width < 100:
            continue

        screenshot = sct.grab({"top": top, "left": left, "width": width, "height": height})
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
        
        x_start, x_end = int(width * 0.74), int(width * 0.85)
        y_start, y_end = int(height * 0.11), int(height * 0.16)
        cropped_name = image[y_start:y_end, x_start:x_end]

        lower_white, upper_white = np.array([200, 200, 200]), np.array([255, 255, 255])
        thresh = cv2.inRange(cropped_name, lower_white, upper_white)

        raw_name = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7').strip()
        character_name = "" 
        
        if raw_name:
            matches = difflib.get_close_matches(raw_name, VALID_CHARACTERS, n=1, cutoff=0.4)
            if matches:
                character_name = matches[0]

        if character_name:
            empty_count = 0
            
            if target_character is None:
                target_character = character_name
                print(f"[掃描] 設定繞圈目標角色為：{target_character}")
                seen_names.append(character_name)
                pyautogui.press('e')
                time.sleep(0.2)
                
            elif character_name == target_character:
                print(f"\n[掃描結束] 偵測到目標角色 ({character_name})，已繞回一圈！")
                
                # 剔除最後掃描進去的 1號與2號真實名字，避免人數多出 2 個
                seen_names = seen_names[:-2]
                print(f"清單建置完成！包含奇偶與主角，共計 {len(seen_names)} 名角色。")
                
                # 第一階段結束時，畫面停留在第 3 位。退回第 1 位的動作移交給第二階段處理。
                break 
                
            else:
                print(f"[掃描] 發現新角色：{character_name}")
                seen_names.append(character_name)
                pyautogui.press('e')
                time.sleep(0.2)
        else:
            empty_count += 1
            if empty_count >= 4:
                print("[跳過] 連續辨識失敗，寫入空白。")
                seen_names.append(" ") 
                pyautogui.press('e')
                empty_count = 0
                time.sleep(1)
            else:
                time.sleep(0.5)

        cv2.imshow("Scanner", thresh)
        cv2.waitKey(1)

    cv2.destroyAllWindows()
    
    if seen_names and not phase1_interrupted:
        with open(list_filename, "w", encoding="utf-8") as f:
            f.write("--- 偵測到的角色名單 ---\n")
            for idx, name in enumerate(seen_names, 1):
                f.write(f"{idx}. {name}\n")

# ==========================================================
# 階段二：連動 OBS 錄影與產生時間軸
# ==========================================================
if len(seen_names) > 0 and not phase1_interrupted:
    print("\n=== [階段二] 準備連動 OBS 錄影 ===")
    
    if skip_phase1:
        print("等待遊戲視窗...")
        while not get_window_rect(WINDOW_TITLE):
            time.sleep(1)

    # 1. 錄影前置作業：退回第一位角色
    print("發送按鍵: 兩次 'q' (退回第一位角色「奇偶」)")
    pyautogui.press('q')
    time.sleep(1.0)
    pyautogui.press('q')
    time.sleep(1.0)

    try:
        obs_client = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
        print("成功連線至 OBS！")
        
        # 2. 開始錄影 (時間軸 0:00)
        obs_client.start_record()
        print("🔴 OBS 開始錄影... (0:00 - 0:01 為畫面停頓緩衝)")
        record_start_time = time.time()
        
        # 3. 等待 1 秒停頓
        time.sleep(1.0)
        
        # 4. 按下 's' 展開詳細資訊介面 (此時約為 0:01)
        print("發送按鍵: 's' (切換至裝備/詳細介面)")
        pyautogui.press('s')
        
        # 給一點點 UI 動畫彈出的時間，讓時間軸計算更自然
        time.sleep(0.5) 
        
        stop_program = False
        
        # 5. 每三秒按 e 並記錄時間軸
        for i, name in enumerate(seen_names):
            if stop_program:
                break
                
            # 計算當下時間並記錄
            elapsed = int(time.time() - record_start_time)
            mins, secs = divmod(elapsed, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            
            timeline_records.append(f"{time_str} - {name}")
            print(f"[{time_str}] 正在展示: {name} (進度: {i+1}/{len(seen_names)})")
            
            # 停留 3 秒
            for _ in range(30):
                if keyboard.is_pressed('esc'):
                    print("\n偵測到按下 'Esc'，緊急中斷錄影。")
                    stop_program = True
                    break
                time.sleep(0.1)
                
            if i < len(seen_names) - 1 and not stop_program:
                pyautogui.press('e')
                
        print("⏹️ 所有角色展示完畢，通知 OBS 停止錄影...")
        obs_client.stop_record()
        print("OBS 錄影已儲存！")
        
    except Exception as e:
        print(f"\n[錯誤] OBS 連線失敗，請確認 OBS 已開啟且密碼正確。\n詳細錯誤: {e}")

# ==========================================================
# 最終階段：匯出時間軸文件
# ==========================================================
if timeline_records:
    output_file = "OBS_Timeline.txt"
    print(f"\n開始匯出時間軸至 {output_file} ...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("--- 錄影角色時間軸 ---\n")
        for record in timeline_records:
            f.write(f"{record}\n")
            
    print(f"匯出完成！檔案位置: {os.path.abspath(output_file)}")
elif seen_names and phase1_interrupted:
    with open("Partial_List.txt", "w", encoding="utf-8") as f:
        for idx, name in enumerate(seen_names, 1):
            f.write(f"{idx}. {name}\n")
    print("已將中斷前的清單存為 Partial_List.txt")