import os
import qrcode
import barcode
from barcode.writer import ImageWriter
from datetime import datetime

def generate_codes(building, floor, machine_start, machine_count, save_path, code_type="qr", latitude=None, longitude=None):
    """
    ฟังก์ชันสร้าง QR Code หรือ Barcode 1D (Code128) พร้อมพิกัด
    :param building: หมายเลขตึก (2 หลัก)
    :param floor: หมายเลขชั้น (2 หลัก)
    :param machine_start: หมายเลขเครื่องเริ่มต้น (3 หลัก)
    :param machine_count: จำนวนเครื่อง
    :param save_path: ที่อยู่โฟลเดอร์ที่ต้องการบันทึก
    :param code_type: ประเภทโค้ดที่ต้องการสร้าง ("qr" หรือ "barcode")
    :param latitude: ละติจูดที่ผู้ใช้ป้อน
    :param longitude: ลองจิจูดที่ผู้ใช้ป้อน
    """
    os.makedirs(save_path, exist_ok=True)  # ✅ สร้างโฟลเดอร์ถ้ายังไม่มี
    building_code = f"{building:02d}"  # ✅ หมายเลขตึกเป็นสองหลัก (เช่น 26)
    floor_code = f"{floor:02d}"  # ✅ หมายเลขชั้นเป็นสองหลัก (เช่น 05)

    for i in range(machine_count):
        machine_code = f"{machine_start + i:03d}"  # ✅ หมายเลขเครื่องเป็นสามหลัก (เช่น 001, 002)
        unique_id = f"{building_code}{floor_code}{machine_code}"  # ✅ รหัสเครื่อง เช่น "260501"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # ✅ เพิ่ม Timestamp
        data_string = f"Building: {building}, Floor: {floor}, Machine: {machine_code}, Lat: {latitude}, Long: {longitude}"  # ✅ เพิ่มข้อมูลพิกัด

        # ✅ สร้างชื่อไฟล์
        filename = os.path.join(save_path, f"{unique_id}.png")

        if code_type == "qr":
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(data_string)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            img.save(filename)
        
        elif code_type == "barcode":
            EAN = barcode.get_barcode_class('code128')
            ean = EAN(unique_id, writer=ImageWriter())
            ean.save(filename)
        
        print(f"📤 Saved {code_type.upper()} at: {filename}")

# ✅ รับค่าจากผู้ใช้
building = int(input("Enter Building No. (2 digits) : "))  # 🔹 หมายเลขตึก เช่น 26
floor = int(input("Enter Floor No. (2 digits) : "))  # 🔹 หมายเลขชั้น เช่น 5
machine_start = int(input("Enter Start Machine No. (3 digits) : "))  # 🔹 หมายเลขเครื่องเริ่มต้น เช่น 1
machine_count = int(input("Number of Machines: "))  # 🔹 จำนวนเครื่อง เช่น 10
code_type = input("Type of code (qr/barcode): ").strip().lower()  # 🔹 เลือก QR Code หรือ Barcode
latitude = input("Enter Latitude: ")  # 🔹 รับละติจูด
longitude = input("Enter Longitude: ")  # 🔹 รับลองจิจูด

# ✅ เรียกใช้ฟังก์ชัน
generate_codes(building, floor, machine_start, machine_count, "./codes", code_type, latitude, longitude)
