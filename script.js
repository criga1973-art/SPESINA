const PRODS = [
    { id: 1, n: "Bucatini n.9", p: 0.99 }, { id: 2, n: "Moretti 66cl", p: 1.19 },
    { id: 3, n: "Sugo Pomodoro", p: 1.50 }, { id: 4, n: "Sgrassatore", p: 2.30 },
    { id: 5, n: "Riso Arborio", p: 2.10 }, { id: 6, n: "Spaghetti n.5", p: 0.89 }
];

let myCart = [];

function draw() {
    let html = "";
    PRODS.forEach(p => {
        html += `<div class="card">
            <div class="qty-label" onclick="add(${p.id})">+</div>
            <p style="font-size:13px; font-weight:bold">${p.n}</p>
            <p style="color:var(--primary); font-weight:bold">${p.p.toFixed(2)}€</p>
        </div>`;
    });
    document.getElementById('catalog-list').innerHTML = html;
}

function add(id) {
    let p = PRODS.find(x => x.id === id);
    let exists = myCart.find(x => x.id === id);
    if(exists) exists.q += 1; else myCart.push({id:p.id, n:p.n, p:p.p, q:1});
    update();
}

function remove(id) {
    myCart = myCart.filter(x => x.id !== id);
    update();
}

function update() {
    let total = 0;
    let html = "";
    myCart.forEach(i => {
        total += (i.p * i.q);
        html += `<div style="display:flex; justify-content:space-between; margin-bottom:8px">
            <span>${i.q}x ${i.n}</span>
            <button class="btn-remove" onclick="remove(${i.id})">✕</button>
        </div>`;
    });
    document.getElementById('cart-list').innerHTML = html || "Il carrello è vuoto";
    document.getElementById('price-total').innerText = total.toFixed(2) + '€';
}

function showPay() { document.getElementById('payModal').style.display = 'flex'; }
function hidePay() { document.getElementById('payModal').style.display = 'none'; }
function showAddress() { document.getElementById('addressModal').style.display = 'flex'; }
function hideAddress() { document.getElementById('addressModal').style.display = 'none'; }

function doOrder(m) {
    alert("Ordine ricevuto! Pagamento: " + m);
    myCart = []; update(); hidePay();
}

draw();

