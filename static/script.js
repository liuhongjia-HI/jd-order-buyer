async function startLogin() {
    log("正在启动登录窗口...请在弹出的浏览器中扫码。");
    try {
        const res = await fetch('/api/login', { method: 'POST' });
        const data = await res.json();
        log("API响应: " + data.message);
    } catch (e) {
        log("请求失败: " + e);
    }
}

async function startScrape() {
    const range = document.getElementById('dateRange').value;
    log(`开始采集 (Filter=${range})... 此过程可能需要几分钟，请保持后端运行。`);

    document.getElementById('statusText').innerText = "运行中...";

    try {
        const res = await fetch('/api/scrape?filter_type=' + range, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            const countStr = data.order_count ? `${data.order_count} 个订单 (${data.count} 商品)` : `${data.count} 个订单`;
            log(`采集完成! 共找到 ${countStr}。`);
            document.getElementById('orderCount').innerText = data.order_count || data.count;
            document.getElementById('statusText').innerText = "完成";
        } else {
            log("采集结束: " + data.message);
            document.getElementById('statusText').innerText = "失败";
        }
    } catch (e) {
        log("采集请求错误: " + e);
        document.getElementById('statusText').innerText = "错误";
    }
}

function log(msg) {
    const box = document.getElementById('consoleBox');
    const line = document.createElement('div');
    line.className = 'log-line';
    line.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
}

// Check auth on load
window.onload = async () => {
    initDateOptions();
    const res = await fetch('/api/check-auth');
    const data = await res.json();
    if (data.authenticated) {
        log("检测到已保存的登录状态 (auth.json)。");
        document.getElementById('statusText').innerText = "已登录";
    } else {
        log("未检测到登录状态，请先点击'切换京东账号'进行扫码。");
    }
};

function initDateOptions() {
    const select = document.getElementById('dateRange');
    select.innerHTML = '';

    // Standard JD options
    const opts = [
        { val: "1", text: "近三个月订单" },
        { val: "2", text: "今年内订单" }
    ];

    const currentYear = new Date().getFullYear();
    // Add historical years from Last Year down to 2015
    for (let y = currentYear - 1; y >= 2015; y--) {
        opts.push({ val: y.toString(), text: `${y}年订单` });
    }

    opts.forEach(o => {
        const opt = document.createElement('option');
        opt.value = o.val;
        opt.innerText = o.text;
        select.appendChild(opt);
    });
}

async function loadLatestFileMeta() {
    try {
        const res = await fetch('/api/latest-file');
        const data = await res.json();
        const hasData = data && data.name;
        document.getElementById('metaName').innerText = hasData ? data.name : '-';
        document.getElementById('metaTime').innerText = hasData ? data.modified : '-';
        document.getElementById('metaSize').innerText = hasData ? formatSize(data.size) : '-';
        document.getElementById('metaPath').innerText = hasData ? (data.full_path || data.path) : '-';
        const dlBtn = document.getElementById('btnDownloadLatest');
        if (dlBtn) {
            if (hasData) {
                dlBtn.href = data.path;
                dlBtn.dataset.href = data.path;
                dlBtn.target = "_blank";
                dlBtn.style.pointerEvents = 'auto';
                dlBtn.style.opacity = 1;
            } else {
                dlBtn.href = '#';
                dlBtn.dataset.href = '';
                dlBtn.style.pointerEvents = 'none';
                dlBtn.style.opacity = 0.5;
            }
        }
    } catch (e) {
        console.error(e);
    }
}

function formatSize(bytes) {
    if (!bytes && bytes !== 0) return '-';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let idx = 0;
    while (size >= 1024 && idx < units.length - 1) {
        size /= 1024;
        idx++;
    }
    return `${size.toFixed(1)} ${units[idx]}`;
}

function switchView(view) {
    const views = {
        console: document.getElementById('viewConsole'),
        data: document.getElementById('viewData')
    };
    Object.keys(views).forEach(k => {
        if (views[k]) views[k].style.display = k === view ? 'block' : 'none';
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.dataset.view === view) item.classList.add('active');
        else item.classList.remove('active');
    });
    if (view === 'data') {
        loadLatestFileMeta();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => switchView(item.dataset.view));
    });
    const openBtn = document.getElementById('btnOpenDownloads');
    if (openBtn) {
        openBtn.addEventListener('click', async () => {
            // Updated to call API
            try {
                const res = await fetch('/api/open-folder', { method: 'POST' });
                const d = await res.json();
                if (d.status !== 'success') {
                    alert('打开目录失败: ' + d.message);
                }
            } catch (e) {
                alert('请求错误: ' + e);
            }
        });
    }
    const dlBtn = document.getElementById('btnDownloadLatest');
    if (dlBtn) {
        dlBtn.addEventListener('click', (e) => {
            const href = dlBtn.dataset.href || dlBtn.href;
            if (!href || href === '#') {
                e.preventDefault();
                return;
            }
            // Trigger download inline; desktop WebView blocks window.open.
            e.preventDefault();
            const tmpLink = document.createElement('a');
            tmpLink.href = href;
            tmpLink.download = '';
            document.body.appendChild(tmpLink);
            tmpLink.click();
            tmpLink.remove();
        });
    }
});
