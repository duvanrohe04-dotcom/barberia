// Forzar scroll al inicio solo cuando se carga la página por primera vez
if('scrollRestoration' in history) history.scrollRestoration = 'manual';
let pageJustLoaded = true;
window.addEventListener('load', () => { 
  if(pageJustLoaded) {
    window.scrollTo(0, 0);
    pageJustLoaded = false;
  }
});
document.addEventListener('DOMContentLoaded', () => { 
  if(pageJustLoaded) {
    window.scrollTo(0, 0); 
  }
});

function showToast(msg, type=false){
  const t = document.getElementById('toast');
  if(!t) return;

  clearTimeout(t._t);

  t.textContent = msg;

  // Mapear tipo a clase CSS
  let cls = 'toast';
  if(type === true  || type === 'error')  cls += ' err';
  else if(type === 'ok')                  cls += ' ok';
  else if(type === 'neutral')             cls += ' neutral';

  // Forzar reflow para reiniciar animación si ya estaba visible
  t.className = 'toast';
  void t.offsetHeight;

  t.className = cls + ' show';

  const duration = (type === 'ok') ? 5000 : 4000;
  t._t = setTimeout(() => { t.className = 'toast'; }, duration);
}

function closeErrorModal(){
  const modal = document.getElementById('errorModal');
  modal.classList.remove('open');
  modal.style.display = 'none';
  document.body.style.overflow = '';
}

function closeModal(id){ 
  const modal = document.getElementById(id);
  if(modal) {
    modal.classList.remove('open');
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function closeBookingModal(){
  const modal = document.getElementById('okModal');
  if(modal) {
    modal.classList.remove('open');
    modal.style.display = 'none';
    // Restaurar scroll del body
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
  }
  // Ir al inicio de la página inmediatamente
  window.scrollTo({top:0, behavior:'smooth'});
}

function goSec(id){ document.getElementById(id)?.scrollIntoView({behavior:'smooth'}); }

function fmtDate(d){
  if(!d) return '';
  const [y,m,da] = d.split('-');
  const dateObj = new Date(parseInt(y), parseInt(m)-1, parseInt(da));
  const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const dayName = days[dateObj.getDay()];
  return `${dayName}, ${da} ${'Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic'.split(' ')[parseInt(m)-1]} ${y}`;
}

function escQ(s){ return (s||'').replace(/"/g,'&quot;'); }

function toggleTheme(){
  const t = document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('themeBtn').textContent = t==='dark'?'🌙':'☀️';
}

// ✅ Actualización v35: Mejoras en mensajes toast y soporte para tipo 'neutral'
