# Phân tích Symbolic BDD cho Mạng Petri (PetriNet)

## Giới thiệu

Dự án này là bài tập lớn cho môn học Mô hình hóa Toán học (CO2011), tập trung vào việc áp dụng các phương pháp hình thức để phân tích mạng Petri. Cụ thể, dự án thực hiện **phân tích tập hợp trạng thái có thể đạt được (reachability analysis)** bằng phương pháp **symbolic**, sử dụng **Sơ đồ Quyết định Nhị phân (Binary Decision Diagrams - BDDs)**.

Mục tiêu chính là thực thi **Task 3: Symbolic computation of reachable markings by using BDD** trên một số mô hình mạng Petri được định nghĩa bằng file PNML. Script sẽ tự động chạy phân tích, xuất kết quả ra màn hình và lưu vào file, bao gồm các thông số như tổng số trạng thái, số nút BDD, thời gian thực thi, và tạo một bảng ở định dạng LaTeX để tiện cho việc báo cáo.

Dự án cung cấp hai cách để chạy:
1.  **Chạy trực tiếp trên máy local**: Sử dụng Python và các thư viện được chỉ định trong `requirements.txt`.
2.  **Chạy bằng Docker**: Sử dụng một môi trường đã được đóng gói sẵn, đảm bảo tính tương thích và không cần cài đặt phức tạp.

---

## Cấu trúc thư mục

```
Petrinet/
├─ Dockerfile               # Dockerfile để build và chạy project trong một container
├─ Setup.md                 # Hướng dẫn cài đặt môi trường Python và dependencies
├─ README.md                # File này - Hướng dẫn tổng quan về dự án
└─ PetriNetBDDs/
   ├─ requirements.txt       # Các package Python cần thiết cho dự án
   └─ src/
      ├─ run_task3_experiments.py # Script chính để chạy thực nghiệm Task 3
      ├─ symbolic.py          # Module thực thi phân tích symbolic BDD (Task 3)
      ├─ explicit.py          # Module thực thi phân tích tường minh (Task 2 - để tham khảo)
      ├─ pnml_parser.py       # Module đọc và phân tích file PNML (Task 1)
      ├─ example.pnml         # Mô hình mạng Petri đơn giản nhất
      ├─ chain_4.pnml         # Mô hình mạng Petri dạng chuỗi tuần tự
      └─ mutex_2proc.pnml     # Mô hình mạng Petri mô phỏng bài toán loại trừ tương hỗ
```

---

## Chức năng các file chính

### 1. Các file mã nguồn (`src/`)

| File | Chức năng | Chi tiết |
| :--- | :--- | :--- |
| `run_task3_experiments.py` | **Script thực thi chính** | Đây là điểm khởi đầu của chương trình. Script này sẽ: 1. Tải các mô hình mạng Petri từ các file `.pnml`. 2. Gọi `SymbolicAnalyzer` để thực hiện phân tích BDD. 3. In kết quả tóm tắt ra console, tạo bảng LaTeX và lưu báo cáo chi tiết vào file `task3_experimental_results.txt`. |
| `symbolic.py` | **Phân tích Symbolic (Task 3)** | Chứa lớp `SymbolicAnalyzer` thực hiện phân tích không gian trạng thái bằng BDD. Nó mã hóa các marking của mạng Petri thành các biểu thức BDD, sau đó tính toán lặp lại để tìm ra tất cả các trạng thái có thể đạt được một cách hiệu quả, đặc biệt với các hệ thống lớn. |
| `explicit.py` | **Phân tích Tường minh (Task 2)** | Thực hiện duyệt không gian trạng thái một cách tường minh (explicit) bằng thuật toán tìm kiếm theo chiều rộng (BFS). Module này dùng để tham khảo và so sánh kết quả với phương pháp symbolic, giúp xác minh tính đúng đắn của `symbolic.py`. |
| `pnml_parser.py` | **Parser PNML (Task 1)** | Đọc file `.pnml` (định dạng XML chuẩn cho mạng Petri) và xây dựng một đối tượng `PNModel` trong bộ nhớ. Đối tượng này chứa thông tin về các place, transition, và arc, làm đầu vào cho các module phân tích. |

### 2. Các file mô hình (`.pnml`)

| File | Mô tả mô hình |
| :--- | :--- |
| `example.pnml` | **Mô hình cơ bản**: Một mạng Petri rất nhỏ, chỉ có 2 place và 1 transition, dùng để kiểm tra nhanh tính đúng đắn của các thuật toán. |
| `chain_4.pnml` | **Mô hình chuỗi tuần tự**: Mô tả một quy trình gồm 4 bước nối tiếp nhau. Mô hình này giúp kiểm tra khả năng xử lý các hệ thống có hành vi tuần tự. |
| `mutex_2proc.pnml` | **Mô hình loại trừ tương hỗ**: Mô phỏng bài toán kinh điển về loại trừ tương hỗ (mutual exclusion) giữa hai tiến trình cùng tranh chấp một tài nguyên. Mô hình này có tính tương tranh, dẫn đến không gian trạng thái phức tạp hơn. |

---

## Hướng dẫn chạy

Bạn có thể chọn một trong hai cách sau.

### 1️⃣ Chạy trực tiếp (theo `Setup.md`)

Cách này phù hợp nếu bạn muốn phát triển hoặc gỡ lỗi mã nguồn.

1.  **Tạo môi trường ảo (khuyến khích)**:
    ```bash
    # Lệnh cho Windows
    cd d:\MyProject\PetriNet\Petrinet
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Cài đặt các thư viện cần thiết**:
    ```bash
    pip install --upgrade pip
    pip install -r PetriNetBDDs/requirements.txt
    ```
    *Lưu ý: Trên Linux, bạn có thể cần cài `build-essential`, `libxml2-dev`, `libxslt1-dev` để build thư viện `lxml`.*

3.  **Chạy thực nghiệm Task 3**:
    ```bash
    python PetriNetBDDs/src/run_task3_experiments.py
    ```

Kết quả sẽ được hiển thị trên console và được lưu vào file `PetriNetBDDs/src/task3_experimental_results.txt`.

### 2️⃣ Chạy bằng Docker

Cách này đơn giản nhất để chạy chương trình mà không cần quan tâm đến môi trường hay cài đặt.

1.  **Build Docker image**:
    Mở terminal tại thư mục gốc `d:\MyProject\PetriNet\Petrinet` và chạy lệnh:
    ```bash
    docker build -t petrinet-app .
    ```

2.  **Chạy container**:
    ```bash
    docker run --rm petrinet-app
    ```
    Lệnh này sẽ khởi tạo một container từ image vừa build, chạy script `run_task3_experiments.py`, in kết quả ra màn hình, và tự động xóa container sau khi chạy xong. `Dockerfile` đã được cấu hình để sao chép tất cả các file cần thiết vào đúng vị trí.
