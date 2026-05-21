// scan.js — uses Quagga2 to scan barcodes from device camera
// When a barcode is detected, it queries the backend for product info.

const scannerElement = document.getElementById('scanner');
let scanning = false;

async function lookupBarcode(barcode){
  const token = localStorage.getItem('token');
  try{
    const res = await fetch(`/api/products?barcode=${encodeURIComponent(barcode)}` , {headers: {'Authorization': 'Bearer '+token}});
    if (!res.ok) {
      document.getElementById('product-info').innerText = 'Product not found';
      showAlert('Barcode not recognized. Please verify the product barcode.', 'warning');
      return;
    }
    const p = await res.json();
    document.getElementById('scan-result').innerText = `Scanned: ${barcode}`;
    document.getElementById('product-info').innerHTML = `<pre>${JSON.stringify(p, null, 2)}</pre>`;
    document.getElementById('sale-product').value = p.id;
  }catch(e){
    document.getElementById('product-info').innerText = 'Error: '+e.message;
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
