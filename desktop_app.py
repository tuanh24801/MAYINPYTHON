from websocket_server import WebsocketServer
import json
import win32print
import win32ui
import tkinter as tk
from tkinter import messagebox
import threading

current_printer = None  # Biến lưu máy in hiện tại

def select_printer():
    """Hàm này sẽ hiển thị giao diện để chọn máy in."""
    global current_printer
    root = tk.Tk()
    root.title("Chọn máy in")

    # Lấy danh sách máy in từ hệ thống
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    
    if not printers:
        messagebox.showerror("Lỗi", "Không tìm thấy máy in nào.")
        return None

    selected_printer = tk.StringVar(value=printers[0])

    label = tk.Label(root, text="Chọn máy in:")
    label.pack(anchor=tk.W)
    
    for printer in printers:
        radio_button = tk.Radiobutton(root, text=printer, variable=selected_printer, value=printer)
        radio_button.pack(anchor=tk.W)
    
    def confirm_selection():
        global current_printer
        current_printer = selected_printer.get()  # Cập nhật máy in đã chọn
        root.destroy()  # Đóng cửa sổ sau khi chọn máy in

    confirm_button = tk.Button(root, text="Xác nhận", command=confirm_selection)
    confirm_button.pack()

    root.geometry("400x200")  # Điều chỉnh kích thước cửa sổ
    root.mainloop()  # Bắt đầu giao diện tkinter

    return current_printer

def print_order(order_data, printer_name):
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        
        hDC.StartDoc("Đơn hàng")
        hDC.StartPage()

        font = win32ui.CreateFont({
            "name": "Arial Unicode MS",
            "height": 40,
            "weight": 100,
        })
        hDC.SelectObject(font)

        max_width = 600
        content_lines = [
            f"TUẤN ANH POS",
            f"Đơn hàng: {order_data['order_id']}",
            f"Khách hàng: {order_data['customer_name']}",
            f"Sản phẩm: {order_data['item']}",
            f"Số lượng: {order_data['quantity']}",
            f"Giá: {order_data['price']}"
        ]
        
        start_y = 10
        line_spacing = 100
        y = start_y

        for line in content_lines:
            split_lines = split_text_to_fit_width(hDC, line, max_width)
            for split_line in split_lines:
                hDC.TextOut(50, y, split_line)
                y += line_spacing

        hDC.EndPage()
        hDC.EndDoc()
        win32print.ClosePrinter(hPrinter)
    except Exception as e:
        print(f"Không thể in đơn hàng: {str(e)}")

def split_text_to_fit_width(hDC, text, max_width):
    """Chia nhỏ dòng văn bản thành nhiều đoạn để vừa với chiều rộng tối đa."""
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        # Kiểm tra chiều rộng của dòng
        width = hDC.GetTextExtent(test_line)[0]
        
        # Nếu chiều rộng vượt quá giới hạn, thêm dòng mới
        if width < max_width:
            current_line = test_line
        else:
            if current_line:  # Nếu có nội dung trong dòng hiện tại, thêm vào danh sách dòng
                lines.append(current_line)
            current_line = word  # Bắt đầu dòng mới với từ hiện tại
    
    if current_line:
        lines.append(current_line)  # Thêm dòng cuối cùng nếu còn văn bản
    
    return lines

def on_message(client, server, message):
    """Xử lý tin nhắn nhận được từ ứng dụng web."""
    order_data = json.loads(message)  # Chuyển đổi chuỗi JSON thành đối tượng Python
    print_order(order_data, current_printer)  # In đơn hàng

def on_new_client(client, server):
    """Xử lý khi có kết nối mới."""
    print(f"Client {client['id']} đã kết nối.")

def start_server():
    global current_printer
    current_printer = select_printer()  # Chọn máy in khi bắt đầu server
    if not current_printer:
        print("Không có máy in nào được chọn.")
        return

    server = WebsocketServer(9999)  # Khởi tạo WebSocket server mà không cần tham số host
    server.set_fn_message_received(on_message)  # Đặt hàm xử lý tin nhắn
    server.set_fn_new_client(on_new_client)  # Đặt hàm xử lý khi có kết nối mới
    print("Server đang chờ kết nối từ web app...")
    server.run_forever()

# Sử dụng cách này để bắt đầu luồng server
if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server, daemon=True)  # Đảm bảo thread chạy trong background
    server_thread.start()

    try:
        # Giữ chương trình chạy để server WebSocket không bị dừng
        while True:
            pass
    except KeyboardInterrupt:
        print("Server bị dừng.")
