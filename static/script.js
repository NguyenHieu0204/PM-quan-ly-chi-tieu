async function addOrUpdateExpense() {
    const id = document.getElementById('editId').value;
    const amount = document.getElementById('amount').value;
    const type = document.getElementById('type').value;
    const description = document.getElementById('desc').value;
    const date = document.getElementById('date').value;

    if (!amount || !description || !date) {
        alert("Vui lòng nhập đầy đủ thông tin!");
        return;
    }

    const data = {
        amount: parseFloat(amount.replace(/,/g, '')),
        type: type,
        description: description,
        date: date
    };

    let url = '/add';
    if (id) {
        data.id = id;
        url = '/update';
    }

    await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    resetForm();
    loadData();
}

function resetForm() {
    document.getElementById('editId').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('type').value = 'chi';
    document.getElementById('desc').value = '';
    document.getElementById('date').value = '';

    document.getElementById('formTitle').innerText = 'Ghi chép giao dịch';
    document.getElementById('submitBtn').innerText = 'Lưu giao dịch';
    document.getElementById('cancelBtn').style.display = 'none';
}

function editExpense(id, amount, type, description, date) {
    document.getElementById('editId').value = id;
    document.getElementById('amount').value = parseInt(amount).toLocaleString('en-US');
    document.getElementById('type').value = type;
    document.getElementById('desc').value = description;
    document.getElementById('date').value = date;

    document.getElementById('formTitle').innerText = 'Cập nhật giao dịch';
    document.getElementById('submitBtn').innerText = 'Cập nhật';
    document.getElementById('cancelBtn').style.display = 'inline-block';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Hàm định dạng số tiền khi nhập
document.getElementById('amount').addEventListener('input', function (e) {
    let value = e.target.value.replace(/,/g, '');
    if (value === "") return;
    if (!isNaN(value)) {
        e.target.value = parseInt(value).toLocaleString('en-US');
    }
});

// Thêm hàm xóa để giao diện hoàn thiện hơn
async function deleteExpense(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa giao dịch này?')) return;

    // Lưu ý: Cần thêm route /delete ở app.py nếu muốn chức năng này hoạt động.
    // Tạm thời tôi sẽ chỉ thực hiện nếu backend hỗ trợ.
    const res = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadData();
    } else {
        // Nếu không có route DELETE cụ thể, có thể báo lỗi hoặc bỏ qua
        console.warn('Backend DELETE route not implemented yet.');
    }
}

async function loadData() {
    const res = await fetch('/list');
    const data = await res.json();

    let html = `
        <thead>
            <tr>
                <th>Ngày</th>
                <th>Nội dung</th>
                <th>Phân loại</th>
                <th>Số tiền</th>
                <th>Hành động</th>
            </tr>
        </thead>
        <tbody>
    `;

    let totalThu = 0;
    let totalChi = 0;

    data.forEach(row => {
        const typeLabel = row.type === 'thu' ? 'Thu' : 'Chi';
        const badgeClass = row.type === 'thu' ? 'badge-thu' : 'badge-chi';
        const amountNum = parseFloat(row.amount) || 0;

        if (row.type === 'thu') totalThu += amountNum;
        else totalChi += amountNum;

        html += `
            <tr class="expense-row">
                <td>${row.date}</td>
                <td style="font-weight: 500;">${row.description}</td>
                <td><span class="badge ${badgeClass}">${typeLabel}</span></td>
                <td style="font-weight: 700; color: ${row.type === 'thu' ? 'var(--success)' : '#fff'}">
                    ${row.type === 'thu' ? '+' : '-'}${formatDisplay(amountNum)}₫
                </td>
                <td>
                    <div class="action-btns">
                        <button class="icon-btn" onclick="editExpense('${row.id}', '${row.amount}', '${row.type}', '${row.description}', '${row.date}')" title="Sửa">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4L18.5 2.5z"></path></svg>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += "</tbody>";
    document.getElementById('table').innerHTML = html;

    document.getElementById('totalThu').innerText = formatDisplay(totalThu) + '₫';
    document.getElementById('totalChi').innerText = formatDisplay(totalChi) + '₫';

    const profit = totalThu - totalChi;
    const profitElem = document.getElementById('totalLai');
    const laiCard = document.getElementById('laiCard');

    profitElem.innerText = (profit >= 0 ? '+' : '') + formatDisplay(profit) + '₫';

    if (profit > 0) {
        laiCard.className = 'card positive';
    } else if (profit < 0) {
        laiCard.className = 'card negative';
    } else {
        laiCard.className = 'card neutral';
    }
}

// Thay thế toLocaleString('vi-VN') bằng 'en-US' để dùng dấu phẩy (,) phân tách hàng nghìn
function formatDisplay(num) {
    return num.toLocaleString('en-US');
}

// Initialize date field to today
document.getElementById('date').valueAsDate = new Date();

loadData();