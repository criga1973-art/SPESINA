const PRODS = [
    { id: 1, n: "Bucatini n.9", p: 0.99, c: "Pasta" },
    { id: 2, n: "Moretti 66cl", p: 1.19, c: "Bevande" },
    { id: 3, n: "Sugo Pomodoro", p: 1.50, c: "Sughi" },
    { id: 5, n: "Riso Arborio", p: 2.10, c: "Riso" },
    { id: 6, n: "Spaghetti n.5", p: 0.89, c: "Pasta" },
    { id: 21, n: "Mele Golden", p: 1.80, c: "Frutta e Verdura" },
    { id: 22, n: "Petto di Pollo", p: 5.50, c: "Carne e Pesce" },
    { id: 23, n: "Latte Intero", p: 1.20, c: "Latticini e Uova" }
];

let myCart = [];

function draw() {
    let html = "";
    PRODS.forEach(p => {
        html += `<div class="card">
            <div class="qty-label" onclick="add(${p.id})">+</div>
            <p style="font-size:13px; font-weight:bold; margin-top:25px">${p.n}</p>
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
    if(myCart.length === 0) {
        html = '<p style="color:#999; margin-top:20px">Il carrello è vuoto</p>';
    } else {
        myCart.forEach(i => {
            total += (i.p * i.q);
            html += `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #f0f0f0; padding-bottom:5px">
                <div style="text-align:left"><b>${i.q}x</b> ${i.n}</div>
                <button class="btn-remove" onclick="remove(${i.id})">✕</button>
            </div>`;
        });
    }
    document.getElementById('cart-list').innerHTML = html;
    document.getElementById('price-total').innerText = total.toFixed(2) + '€';
}

function showPay() { if(myCart.length > 0) document.getElementById('payModal').style.display = 'flex'; }
function hidePay() { document.getElementById('payModal').style.display = 'none'; }
function showAddress() { document.getElementById('addressModal').style.display = 'flex'; }
function hideAddress() { document.getElementById('addressModal').style.display = 'none'; }

function doOrder(m) {
    alert("Ordine ricevuto! Pagamento: " + m);
    myCart = []; update(); hidePay();
}

draw();
