// ---- dates: shown for information only; the server always uses today's date ----
const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
function pad(n){ return String(n).padStart(2,'0'); }
const _now = new Date();
const QUOTE_DATE = pad(_now.getDate()) + '-' + pad(_now.getMonth()+1) + '-' + _now.getFullYear();
const AGREEMENT_DATE = pad(_now.getDate()) + '-' + MONTHS[_now.getMonth()] + '-' + _now.getFullYear();
document.getElementById('dates').innerHTML =
  'Quotation date: <b>' + QUOTE_DATE + '</b> &nbsp;&middot;&nbsp; Agreement date: <b>' + AGREEMENT_DATE + '</b> (today, filled in automatically)';

// ---- bill validation: exactly 13 digits ----
const billInput = document.getElementById('bill');
const billHint = document.getElementById('billHint');
function billValid(){ return /^[0-9]{13}$/.test(billInput.value.trim()); }
billInput.addEventListener('input', () => {
  billInput.value = billInput.value.replace(/[^0-9]/g, '').slice(0,13);
  const ok = billValid();
  billInput.classList.toggle('invalid', billInput.value.length > 0 && !ok);
  billHint.textContent = ok ? 'Looks good.' : 'Must be exactly 13 digits.';
  billHint.classList.toggle('err', billInput.value.length > 0 && !ok);
});

function getFields(){
  return {
    name: document.getElementById('name').value.trim(),
    address: document.getElementById('address').value.trim(),
    city: document.getElementById('city').value.trim(),
    bill: billInput.value.trim()
  };
}

async function requestPdf(docType, payload, status){
  const res = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ docType, ...payload })
  });
  if (!res.ok){
    let msg = 'Request failed (' + res.status + ')';
    try { const j = await res.json(); if (j.error) msg = j.error; } catch(e){}
    throw new Error(msg);
  }
  const disposition = res.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : (docType + '.pdf');
  const blob = await res.blob();
  return { blob, filename };
}

function downloadBlob(blob, filename){
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

document.getElementById('btnQuote').addEventListener('click', async () => {
  const btn = document.getElementById('btnQuote'); const status = document.getElementById('status');
  const f = getFields();
  if (!f.name || !f.city){ status.textContent = 'Please fill in the customer name and city first.'; return; }
  btn.disabled = true; status.textContent = 'Building quotation...';
  try{
    const { blob, filename } = await requestPdf('quotation', { name: f.name, city: f.city }, status);
    downloadBlob(blob, filename);
    status.textContent = 'PDF downloaded.';
  } catch(e){ console.error(e); status.textContent = 'Something went wrong: ' + e.message; }
  finally { btn.disabled = false; }
});

document.getElementById('btnAgree').addEventListener('click', async () => {
  const btn = document.getElementById('btnAgree'); const status = document.getElementById('status');
  const f = getFields();
  if (!f.name || !f.address){ status.textContent = 'Please fill in the customer name and address first.'; return; }
  if (!billValid()){ status.textContent = 'Electricity consumer number must be exactly 13 digits.'; return; }
  btn.disabled = true; status.textContent = 'Building agreement...';
  try{
    const { blob, filename } = await requestPdf('agreement', { name: f.name, address: f.address, bill: f.bill }, status);
    downloadBlob(blob, filename);
    status.textContent = 'PDF downloaded.';
  } catch(e){ console.error(e); status.textContent = 'Something went wrong: ' + e.message; }
  finally { btn.disabled = false; }
});
