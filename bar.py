import cv2
import numpy as np
import requests
import gspread
from datetime import datetime
from pyzbar.pyzbar import decode
from oauth2client.service_account import ServiceAccountCredentials

# --------------- ตั้งค่า Google Sheets API ---------------
SHEET_ID = "1xnIkpmWV7tH6qFnNIGMs1c9Uow_J3akA3jBWnJ9OlBY"  # ✅ Google Sheets ID
SHEET_BARCODE = "ติดตามบาร์โค้ด"  # ✅ ชื่อชีตที่ใช้เก็บบาร์โค้ด
SHEET_USERS = "UserIDs"  # ✅ ชื่อชีตที่ใช้เก็บ User ID ของ LINE
CREDENTIALS_FILE = "credentials.json"  # ✅ ไฟล์ JSON จาก Google Cloud

# --------------- ตั้งค่า LINE API ---------------
LINE_ACCESS_TOKEN = "wNdlBHSikSJc5tJGvPnwi0PZkuL9ZZM6PAmpjGjbeYS2jK56gZvlNBT6f68TPDy7g8PhHsXALvaSHPQ5WL7mMcslwgfl9K8wWQig3VzAe2NnyNhQqfLPh+Vk2jvbxWO0172DLU+ukr/ZTMSmVNpUMwdB04t89/1O/w1cDnyilFU="  # ✅ ใส่ LINE OA Access Token ของคุณ

# ✅ ฟังก์ชันเชื่อมต่อ Google Sheets
def connect_google_sheets(sheet_name):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).worksheet(sheet_name)
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets: {e}")
        return None

# ✅ ฟังก์ชันดึง `User ID` ทั้งหมดจาก Google Sheets
def get_all_user_ids():
    sheet = connect_google_sheets(SHEET_USERS)
    if not sheet:
        return []

    user_ids = sheet.col_values(1)  # ✅ อ่านคอลัมน์ A ที่เก็บ User ID
    return [user_id.strip() for user_id in user_ids if user_id.startswith("U")]

# ✅ ฟังก์ชันส่งข้อความไปยังทุก `User ID`
def send_line_message(message):
    user_ids = get_all_user_ids()
    if not user_ids:
        print("❌ ไม่มี User ID ในชีต UserIDs")
        return

    url = "https://api.line.me/v2/bot/message/multicast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_ids,  # ✅ ส่งให้ทุกคนในชีต UserIDs
        "messages": [{"type": "text", "text": message}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # ✅ ตรวจสอบว่าการส่งข้อความสำเร็จ
        print("📤 แจ้งเตือน LINE สำเร็จไปยังทุก User ID")
    except requests.exceptions.RequestException as e:
        print(f"❌ ไม่สามารถส่งข้อความ LINE: {e}")

# ✅ ฟังก์ชันเตรียมภาพก่อนอ่านบาร์โค้ด
def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (5, 5), 0)

# ✅ ฟังก์ชันอ่านบาร์โค้ด (รองรับ 1D & 2D)
def read_barcodes(frame, sheet):
    processed_frame = preprocess_image(frame)
    barcodes = decode(processed_frame)

    if not barcodes:
        return frame

    existing_barcodes = set(sheet.col_values(2))  # ✅ ดึง Barcode ที่เคยบันทึกเพื่อลดโหลด

    for barcode in barcodes:
        barcode_text = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        x, y, w, h = barcode.rect

        if barcode_text in existing_barcodes:
            print(f"⚠️ บาร์โค้ดซ้ำ: {barcode_text}")
            continue  # ✅ ข้ามถ้าพบว่าบาร์โค้ดเคยบันทึกแล้ว

        print(f"✅ พบ {barcode_type}: {barcode_text}")

        # ✅ วาดกรอบรอบบาร์โค้ด
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, barcode_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # ✅ บันทึกข้อมูลลง Google Sheets
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, barcode_text, barcode_type])

        # ✅ แจ้งเตือนไปที่ LINE ทุก User ID
        message = f"📢 สแกนสำเร็จ!\n🔹 รหัส: {barcode_text}\n📅 วันที่: {timestamp.split()[0]}\n⏰ เวลา: {timestamp.split()[1]}\n📌 ประเภท: {barcode_type}"
        send_line_message(message)

    return frame

# ✅ ฟังก์ชันเปิดกล้องและเริ่มการสแกน
def main():
    camera = cv2.VideoCapture(0)
    camera.set(3, 640)  # ✅ ความกว้างของวิดีโอ
    camera.set(4, 480)  # ✅ ความสูงของวิดีโอ

    sheet = connect_google_sheets(SHEET_BARCODE)
    if sheet is None:
        print("❌ ปิดโปรแกรมเนื่องจากไม่สามารถเชื่อมต่อ Google Sheets ได้")
        return

    while True:
        ret, frame = camera.read()
        if not ret:
            print("❌ ไม่สามารถรับภาพจากกล้อง")
            break

        frame = read_barcodes(frame, sheet)  # ✅ อ่านบาร์โค้ดและบันทึกข้อมูล
        cv2.imshow('📷 Barcode & QR Code Scanner', frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ✅ กด ESC เพื่อออกจากโปรแกรม
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
