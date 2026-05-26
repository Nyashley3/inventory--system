// scan.js — uses Quagga2 to scan barcodes from device camera
// When a barcode is detected, it queries the backend for product info.

const scannerElement = document.getElementById('scanner');
const scannedInfo = document.getElementById('product-details');
const scanResult = document.getElementById('scan-result');
let scanning = false;

async function lookupBarcode(barcode){
  const token = localStorage.getItem('token');
  try{
    const res = await fetch(`/api/products?barcode=${encodeURIComponent(barcode)}` , {headers: {'Authorization': 'Bearer '+token}});
    if (!res.ok) {
      if (scannedInfo) scannedInfo.innerText = 'Product not found';
      if (scanResult) scanResult.innerText = `Scanned: ${barcode}`;
      showAlert('Barcode not recognized. Please verify the product barcode.', 'warning');
      return;
    }
    const p = await res.json();
    if (scanResult) scanResult.innerText = `Scanned: ${barcode}`;
    if (scannedInfo) scannedInfo.innerHTML = `<pre>${JSON.stringify(p, null, 2)}</pre>`;
    const productField = document.getElementById('sale-product') || document.getElementById('checkout-search');
    if (productField) productField.value = p.id;
    if (typeof CURRENT_PRODUCT !== 'undefined') {
      CURRENT_PRODUCT = p;
    }
  } catch(e) {
    if (scannedInfo) scannedInfo.innerText = 'Error: '+e.message;
    showAlert('Barcode scan failed. Please try again.', 'danger');
  }
}

function startScanner(){
  if (scanning) return;
  scanning = true;
  Quagga.init({
    inputStream: {
      name: 'Live',
      type: 'LiveStream',
      target: scannerElement,
      constraints: { facingMode: 'environment', width: 480, height: 320 }
    },
    decoder: { readers: ['code_128_reader','ean_reader','ean_8_reader','upc_reader'] }
  }, function(err){
    if (err) { console.error(err); return; }
    Quagga.start();
  });

  Quagga.onDetected(function(data){
    const code = data.codeResult.code;
    if (code) {
      // stop after detection to avoid duplicates
      stopScanner();
      lookupBarcode(code);
    }
  });
}

function stopScanner(){
  if (!scanning) return;
  scanning = false;
  try{ Quagga.stop(); }catch(e){}
  scannerElement.innerHTML = '';
}

document.getElementById('btn-start').addEventListener('click', startScanner);
document.getElementById('btn-stop').addEventListener('click', stopScanner);
