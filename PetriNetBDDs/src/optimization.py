import pulp
from typing import Dict, List, Tuple, Any, Optional, FrozenSet
import numpy as np
import sys
import os 

# --- IMPORT CÁC THÀNH PHẦN TỪ TASK 1 & 3 ---
try:
    from dd.autoref import BDD
    from pnml_parser import PNModel # Từ Task 1
    from symbolic import SymbolicAnalyzer # Từ Task 3

except ImportError as e:
    print(f"LỖI THIẾU MODULE: Không tìm thấy lớp hoặc thư viện cần thiết.")
    print(f"Vui lòng đảm bảo: pnml_parser.py, symbolic.py, và file này nằm cùng thư mục.")
    print(f"Lỗi chi tiết: {e}")
    sys.exit(1)

# ====================================================================
# PHẦN 1: MỞ RỘNG PNModel (TÍNH MA TRẬN SỰ CỐ)
# ====================================================================

# Thêm phương thức tính Ma trận Sự cố vào lớp PNModel
def _build_incidence_matrix(self: PNModel) -> np.ndarray:
    """Tính toán và trả về Ma trận sự cố A = Post - Pre."""
    sorted_places = sorted(self.places.keys())
    sorted_transitions = sorted(self.transitions.keys())
    n_places = len(sorted_places)
    n_trans = len(sorted_transitions)
    A = np.zeros((n_places, n_trans), dtype=int)
    
    p_idx = {p: i for i, p in enumerate(sorted_places)}
    
    for p_id in sorted_places:
        i = p_idx[p_id]
        for j, t_id in enumerate(sorted_transitions):
            post_val = 1 if t_id in self.places[p_id].inputs else 0
            pre_val = 1 if t_id in self.places[p_id].outputs else 0
            A[i, j] = post_val - pre_val
    return A

PNModel.incidence_matrix = property(_build_incidence_matrix)


# ====================================================================
# PHẦN 2: TÍCH HỢP BDD VÀ ILP CORE
# ====================================================================

def get_bdd_reach_data(model: PNModel) -> Tuple[BDD, Any, Dict[str, str]]:
    """Chạy SymbolicAnalyzer (Task 3) để lấy BDD Reachable Set và cấu hình BDD."""
    print("\n[TASK 3] Bắt đầu chạy Symbolic Analyzer...")
    analyzer = SymbolicAnalyzer(model)
    results = analyzer.analyze()
    
    bdd_instance = analyzer.bdd
    reachable_bdd = analyzer.reachable_bdd
    place_vars = analyzer.place_vars
    
    print(f"[TASK 3] Phân tích hoàn tất. BDD Nodes: {results['bdd_node_count']}. Markings: {results['num_markings']}")
    # NOTE: Kết quả của SymbolicAnalyzer (Task 3) vẫn bao gồm thời gian, nhưng chúng ta chỉ loại bỏ việc tính thời gian trong Task 5.
    return bdd_instance, reachable_bdd, place_vars

def is_reachable_bdd(marking_dict: Dict[str, int], bdd_reach: Any, place_vars: Dict[str, str], bdd_instance: BDD) -> bool:
    """Kiểm tra Marking (M) có thỏa mãn BDD (Reach(M0)) không."""
    fs_marking = frozenset(p for p, val in marking_dict.items() if val == 1)
    marking_bdd = bdd_instance.true
    
    for place_id, var_name in place_vars.items():
        var = bdd_instance.var(var_name)
        if place_id in fs_marking:
            marking_bdd = marking_bdd & var
        else:
            marking_bdd = marking_bdd & ~var

    return (marking_bdd & bdd_reach) != bdd_instance.false

# Cập nhật signature: Loại bỏ tham số float (runtime)
def optimize_reachable(model: PNModel, c: Dict[str, int], timeout: int = 60) -> Tuple[Optional[Dict[str, int]], str]:
    """Task 5: Tối ưu hóa max c^T M, M in Reach(M0)."""
    
    # 1. Lấy đầu ra BDD (Thực thi Task 3)
    bdd_instance, bdd_reach, place_vars = get_bdd_reach_data(model)
    
    # 2. Setup ILP
    places = sorted(model.places.keys())
    transitions = sorted(model.transitions.keys())
    A = model.incidence_matrix
    prob = pulp.LpProblem("Petri_Optimization", pulp.LpMaximize)
    
    M_vars = pulp.LpVariable.dicts("M", places, lowBound=0, upBound=1, cat=pulp.LpBinary)
    sigma_vars = pulp.LpVariable.dicts("sigma", transitions, lowBound=0, cat=pulp.LpInteger)
    
    # 3. Objective: max sum c_p * M_p
    prob += pulp.lpSum(c.get(p, 0) * M_vars[p] for p in places)
    
    # 4. Constraints: State Equation M = M0 + A * sigma
    for i, p in enumerate(places):
        M0_p = 1 if model.places[p].marked else 0 
        prob += M_vars[p] == M0_p + pulp.lpSum(A[i, j] * sigma_vars[t] 
                                               for j, t in enumerate(transitions)), f"State_Eq_{p}"
    
    # 5. Solve & Verify
    print("Bắt đầu giải ILP...")
    
    status = prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=timeout))  
    
    log_messages = f"ILP Solver Status: {pulp.LpStatus[status]}\n"
    
    if status != pulp.LpStatusOptimal:
        log_messages += f"Không tìm thấy kết quả tối ưu. Trạng thái: {pulp.LpStatus[status]}\n"
        # Trả về None và log
        return None, log_messages
    
    optimal_M = {p: int(M_vars[p].value()) for p in places}
    
    # Verify với BDD (kết hợp Task 3)
    if not is_reachable_bdd(optimal_M, bdd_reach, place_vars, bdd_instance):
        log_messages += "Lỗi: Giải pháp ILP (State Equation) không thỏa mãn BDD Reachability.\n"
        # Trả về None và log
        return None, log_messages
    
    # Trả về kết quả và log
    return optimal_M, log_messages

# ====================================================================
# PHẦN CHẠY VÍ DỤ (MỤC TIÊU CỤ THỂ)
# ====================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python task5_example_runner.py <file.pnml>")
        print("Ví dụ: python task5_example_runner.py mutex_2proc.pnml")
        sys.exit(0)

    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"LỖI: Không tìm thấy file PNML tại đường dẫn: {filepath}")
        sys.exit(1)

    # 1. Load model (Task 1)
    model = PNModel.load_pnml(filepath)
    
    # Khởi tạo output_content
    output_content = f"\n[TASK 5] Báo cáo Tối ưu hóa cho mô hình: {os.path.basename(filepath)}\n"
    output_content += "=" * 50 + "\n"
    
    if model:
        # 2. ĐỊNH NGHĨA HÀM MỤC TIÊU CỤ THỂ
        c: Dict[str, int] = {}
        is_mutex_net = any(p.startswith('c') for p in model.places.keys())
        
        if is_mutex_net:
            for p in sorted(model.places.keys()):
                if p.startswith('c'): c[p] = 10
                elif p.startswith('r'): c[p] = 2
                else: c[p] = 1
            objective_desc = "Maximize (10 * Tokens in CS + 2 * Tokens in Request + 1 * Tokens in Idle/Mutex)."
            
        else:
            for p in sorted(model.places.keys()): c[p] = 1
            objective_desc = "Maximize tổng số tokens (c = 1 cho tất cả places)."
        
        output_content += f"Hàm Mục tiêu: {objective_desc}\n"
        output_content += f"Trọng số chi tiết: {c}\n"
        
        # 3. Chạy Tối ưu hóa (Task 5)
        # Cập nhật: Chỉ nhận 2 giá trị
        result, log_messages = optimize_reachable(model, c)
        
        # Thêm log messages vào nội dung output
        output_content += log_messages
        
        # 4. Báo cáo Kết quả cuối cùng
        output_content += "\n--- KẾT QUẢ TỐI ƯU HÓA CUỐI CÙNG ---\n"
        if result:
            objective_value = sum(c[p] * v for p, v in result.items())
            output_content += f"Marking tối ưu (M*): {result}\n"
            output_content += f"Giá trị Hàm Mục tiêu tối đa: {objective_value}\n"
        else:
            output_content += "Không tìm thấy Marking tối ưu hoặc Marking không reachable.\n"
            
        # Loại bỏ dòng báo cáo thời gian
        output_content += "=" * 50 + "\n"
        
    else:
        # Ghi log khi model load thất bại (ví dụ file PNML không hợp lệ)
        output_content += "LỖI: Không thể tải mô hình PNML. Vui lòng kiểm tra định dạng file PNML.\n"
        output_content += "=" * 50 + "\n"
        
    # --- Ghi và In kết quả ---
    output_filename = f"task5_results.txt"
    
    # 1. In ra Console
    print(output_content)
    
    # 2. Ghi ra File
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"\n✅ Kết quả Task 5 đã được ghi thành công vào file: {output_filename}")
    except Exception as e:
        print(f"\n❌ Lỗi khi ghi file {output_filename}: {e}")