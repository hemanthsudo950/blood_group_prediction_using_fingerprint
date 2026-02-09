// ----------------------------
// ELEMENTS
// ----------------------------
const fingerprintInput = document.getElementById('fingerprintInput');
const fileName = document.getElementById('fileName');
const previewImg = document.getElementById('previewImg');
const scannerBox = document.getElementById('scannerBox');
const scanLine = document.getElementById('scanLine');
const detectBtn = document.getElementById('detectBtn');
const resetBtn = document.getElementById('resetBtn');
const loader = document.getElementById('loader');
const resultArea = document.getElementById('resultArea');
const detectedGroup = document.getElementById('detectedGroup');
const detectedUser = document.getElementById('detectedUser');
const speakBtn = document.getElementById('speakBtn');

let chart = null;
let lastResult = null;

// ----------------------------
// FILE SELECT
// ----------------------------
fingerprintInput.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) {
    fileName.textContent = 'No file chosen';
    previewImg.style.display = 'none';
    return;
  }

  fileName.textContent = f.name;
  const url = URL.createObjectURL(f);
  previewImg.src = url;
  previewImg.style.display = 'block';
  scannerBox.classList.add('active');
});

// ----------------------------
// RESET
// ----------------------------
resetBtn.addEventListener('click', () => {
  fingerprintInput.value = '';
  fileName.textContent = 'No file chosen';
  previewImg.style.display = 'none';
  scannerBox.classList.remove('active');
  resultArea.style.display = 'none';

  if (chart) {
    chart.destroy();
    chart = null;
  }
});

// ----------------------------
// SPEAK RESULT
// ----------------------------
speakBtn.addEventListener('click', () => {
  if (!lastResult) return;

  const msg = `Detected blood group is ${lastResult.blood_group}`;
  const utter = new SpeechSynthesisUtterance(msg);
  utter.lang = 'en-US';
  speechSynthesis.cancel();
  speechSynthesis.speak(utter);
});

// ----------------------------
// DRAW CHART
// ----------------------------
function drawChart(bloodGroup, confidences) {
  const labels = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
  let data;

  if (confidences && typeof confidences === 'object') {
    data = labels.map(l => Math.round((confidences[l] || 0) * 100));
  } else {
    data = labels.map(l => (l === bloodGroup ? 95 : 8));
  }

  const ctx = document.getElementById('bloodChart').getContext('2d');

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: labels.map(l =>
          l === bloodGroup ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.2)'
        ),
        borderRadius: 8
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, ticks: { color: '#fff' } },
        x: { ticks: { color: '#fff' } }
      }
    }
  });
}

// ----------------------------
// DETECT BUTTON
// ----------------------------
detectBtn.addEventListener('click', async () => {
  const file = fingerprintInput.files[0];
  if (!file) return alert('Please choose a fingerprint image (bmp/png/jpg).');

  loader.style.display = 'block';
  scanLine.classList.add('active');
  detectBtn.disabled = true;

  const fd = new FormData();
  fd.append('fingerprint', file);

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      body: fd
    });

    const data = await res.json();

    loader.style.display = 'none';
    scanLine.classList.remove('active');
    detectBtn.disabled = false;

    if (!res.ok) {
      const message = data.error || `Server returned ${res.status}`;
      alert(message);
      return;
    }

    if (!data.blood_group) {
      alert('Server returned no blood group. Check backend logs.');
      return;
    }

    lastResult = data;

    detectedGroup.textContent = data.blood_group;
    detectedUser.textContent = data.name ? `For: ${data.name}` : 'For: Registered User';
    resultArea.style.display = 'block';

    const confidences = data.confidences || data.confidence || null;
    drawChart(data.blood_group, confidences);

    // Auto speak
    try {
      const utter = new SpeechSynthesisUtterance(`Detected blood group is ${data.blood_group}`);
      utter.lang = 'en-US';
      speechSynthesis.cancel();
      speechSynthesis.speak(utter);
    } catch (err) {
      console.warn('Speech not supported', err);
    }

  } catch (err) {
    loader.style.display = 'none';
    scanLine.classList.remove('active');
    detectBtn.disabled = false;
    alert('Could not reach backend. Make sure python app.py is running.\n' + err.message);
  }
});
