let currentFilter = { start: '', end: '' };

async function addOrUpdateExpense() {
    const id = document.getElementById('editId').value;
    const amountRaw = document.getElementById('amount').value.replace(/,/g, '');
    const type = document.getElementById('type').value;
    const description = document.getElementById('desc').value;
    const date = document.getElementById('date').value;

    if (!amountRaw || !description || !date) {
        alert("Vui lòng nhập đầy đủ thông tin!");
        return;
    }

    const data = {
        amount: parseFloat(amountRaw),
        type: type,
        description: description,
        date: date
    };

    let url = '/add';
    if (id) {
        data.id = id;
        url = '/update';
    }

    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.status === 401) {
        window.location.href = '/auth';
        return;
    }

    if (res.ok) {
        resetForm();
        loadData();
    }
}

function resetForm() {
    document.getElementById('editId').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('type').value = 'chi';
    document.getElementById('desc').value = '';
    document.getElementById('date').valueAsDate = new Date();

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

async function deleteExpense(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa giao dịch này?')) return;

    const res = await fetch(`/delete/${id}`, { method: 'DELETE' });
    if (res.status === 401) {
        window.location.href = '/auth';
        return;
    }
    if (res.ok) {
        loadData();
    }
}

async function loadData() {
    let url = '/list';
    if (currentFilter.start && currentFilter.end) {
        url += `?start=${currentFilter.start}&end=${currentFilter.end}`;
    }

    const res = await fetch(url);
    if (res.status === 401) {
        window.location.href = '/auth';
        return;
    }
    const data = await res.json();

    let html = `
        <thead>
            <tr>
                <th>Ngày</th>
                <th>Nội dung</th>
                <th>Loại</th>
                <th>Số tiền</th>
                <th>Hành động</th>
            </tr>
        </thead>
        <tbody>
    `;

    let totalThu = 0;
    let totalChi = 0;

    data.forEach(row => {
        const isThu = row.type === 'thu';
        const amountNum = parseFloat(row.amount) || 0;

        if (isThu) totalThu += amountNum;
        else totalChi += amountNum;

        html += `
            <tr class="expense-row">
                <td style="white-space: nowrap">${row.date}</td>
                <td style="font-weight: 500;">${row.description}</td>
                <td><span class="badge ${isThu ? 'badge-thu' : 'badge-chi'}">${isThu ? 'Thu' : 'Chi'}</span></td>
                <td style="font-weight: 700; color: ${isThu ? 'var(--success)' : '#ef4444'}">
                    ${isThu ? '+' : '-'}${formatDisplay(amountNum)}₫
                </td>
                <td>
                    <div class="action-btns">
                        <button class="icon-btn" onclick="editExpense('${row.id}', '${row.amount}', '${row.type}', '${row.description}', '${row.date}')" title="Sửa">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4L18.5 2.5z"></path></svg>
                        </button>
                        <button class="icon-btn" onclick="deleteExpense('${row.id}')" title="Xóa" style="color: #ef4444">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
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
    laiCard.className = `card ${profit > 0 ? 'positive' : (profit < 0 ? 'negative' : 'neutral')}`;
}

function applyFilter() {
    currentFilter.start = document.getElementById('filterStart').value;
    currentFilter.end = document.getElementById('filterEnd').value;
    if (!currentFilter.start || !currentFilter.end) {
        alert("Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc!");
        return;
    }
    loadData();
}

function resetFilter() {
    currentFilter = { start: '', end: '' };
    document.getElementById('filterStart').value = '';
    document.getElementById('filterEnd').value = '';
    loadData();
}

function exportExcel() {
    let url = '/export';
    if (currentFilter.start && currentFilter.end) {
        url += `?start=${currentFilter.start}&end=${currentFilter.end}`;
    }
    window.location.href = url;
}

async function importData(input) {
    if (!input.files || !input.files[0]) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);

    const res = await fetch('/import', {
        method: 'POST',
        body: formData
    });

    if (res.ok) {
        alert("Nhập dữ liệu thành công!");
        loadData();
    } else {
        const error = await res.json();
        alert("Lỗi: " + error.error);
    }
    input.value = '';
}

function formatDisplay(num) {
    return num.toLocaleString('en-US');
}

document.getElementById('amount').addEventListener('input', function (e) {
    let value = e.target.value.replace(/,/g, '');
    if (value === "") return;
    if (!isNaN(value)) {
        e.target.value = parseInt(value).toLocaleString('en-US');
    }
});

document.getElementById('date').valueAsDate = new Date();
loadData();