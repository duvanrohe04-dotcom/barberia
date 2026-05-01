// ══ STATE ══════════════════════════════════════════════════════
console.log('🔧 app.js cargado correctamente');
let selSrv=null, selStaff=null, selTime=null, selGender=null;
let services=[], servicesF=[], barbers=[], stylists=[];
let cfg={ubicacion:'📍 Bogotá, Colombia', telefono:'+57 310 000 0000', wa:'', ig:'', wa_sty:'', ig_sty:''};
let shopName='JS BARBERSHOP', shopLogo=null;
let evoInstance=null;
let srvImgBuf={}, brbImgBuf={}, styImgBuf={}, srvFImgBuf={};

// ══ INIT ═══════════════════════════════════════════════════════
async function init(){
  // Verificar si hay sesión activa de administrador
  await checkSession();
  
  await Promise.all([
    loadServices('male'),
    loadServices('female'),
    loadStaff('male'),
    loadStaff('female'),
    loadConfig(),
    loadPublicReviews()
  ]);
  applyLogoEverywhere();
  applyNameEverywhere();
  applyConfig();
  checkDownloadAvailability();
  // Actualizar contador de profesionales en el hero
  const heroStaff = document.getElementById('heroStaff');
  if(heroStaff) heroStaff.textContent = (barbers.length + stylists.length) + '+';
  document.getElementById('bDate').min = new Date().toISOString().split('T')[0];
  setupNavDots();
}

async function checkSession(){
  try {
    const res = await fetch('/auth/check-session');
    const data = await res.json();
    if(data.authenticated){
      // Restaurar vista de administrador
      document.getElementById('adminKeyBtn').style.display='none';
      document.getElementById('adminZone').style.display='flex';
      switchView('admin');
    }
  } catch(e) {
    console.log('No hay sesión activa');
  }
}

let genderIcons = { male: null, female: null };

async function loadConfig(){
  try{
    const res = await fetch('/api/config');
    const data = await res.json();
    if(data.ubicacion) cfg.ubicacion = data.ubicacion;
    if(data.telefono)  cfg.telefono  = data.telefono;
    if(data.wa  !== undefined) cfg.wa = data.wa;
    if(data.ig  !== undefined) cfg.ig = data.ig;
    if(data.wa_sty !== undefined) cfg.wa_sty = data.wa_sty;
    if(data.ig_sty !== undefined) cfg.ig_sty = data.ig_sty;
    if(data.shop_name) shopName = data.shop_name;
    if(data.shop_logo) shopLogo = data.shop_logo;
    if(data.gender_icon_male) genderIcons.male = data.gender_icon_male;
    if(data.gender_icon_female) genderIcons.female = data.gender_icon_female;
    if(data.evo_instance !== undefined) evoInstance = data.evo_instance;
    applyGenderIcons();
  }catch(e){ console.warn('Config no disponible', e); }
}

async function loadServices(gender){
  const res = await fetch(`/api/services?gender=${gender}`);
  const data = await res.json();
  if(gender==='male') services = data;
  else servicesF = data;
}

async function loadStaff(gender){
  const res = await fetch(`/api/staff?gender=${gender}`);
  const data = await res.json();
  if(gender==='male') barbers = data;
  else stylists = data;
}

// ══ LOGIN PANEL ════════════════════════════════════════════════
let panelOpenByUser = false;

function toggleLoginPanel(e){
  if(e) e.stopPropagation();
  const panel = document.getElementById('loginPanel');
  if(!panel) {
    console.error('Panel de login no encontrado');
    return;
  }
  const isOpen = panel.style.display === 'block';
  panel.style.display = isOpen ? 'none' : 'block';
  if(!isOpen) {
    const userInput = document.getElementById('rUser');
    if(userInput) userInput.focus();
  }
}

// Cerrar panel al hacer click fuera
document.addEventListener('click', function(e){
  const panel = document.getElementById('loginPanel');
  const key = document.getElementById('adminKeyBtn');
  if(panel && panel.style.display !== 'none' && !panel.contains(e.target) && e.target !== key && e.target !== key.parentElement){
    panel.style.display = 'none';
  }
});

// ══ AUTH ═══════════════════════════════════════════════════════
async function doLogin(e){
  if(e && e.preventDefault) e.preventDefault();
  const u = document.getElementById('rUser').value.trim();
  const p = document.getElementById('rPass').value;
  const res = await fetch('/auth/login', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({username:u, password:p})
  });
  const data = await res.json();
  if(data.success){
    document.getElementById('loginPanel').style.display='none';
    document.getElementById('adminKeyBtn').style.display='none';
    document.getElementById('adminZone').style.display='flex';
    switchView('admin');
    showToast('✅ Bienvenido, Administrador!','ok');
  } else {
    showToast('🔐 ' + (data.message||'Credenciales incorrectas. Intenta de nuevo.'), 'error');
  }
}

async function doLogout(){
  await fetch('/auth/logout', {method:'POST'});
  document.getElementById('adminKeyBtn').style.display='inline-block';
  document.getElementById('adminZone').style.display='none';
  document.getElementById('rUser').value='';
  document.getElementById('rPass').value='';
  switchView('client');
  showToast('👋 Sesión cerrada correctamente', 'ok');
}

function switchView(v){
  document.getElementById('adminView').style.display = v==='admin'?'block':'none';
  document.getElementById('clientView').style.display = v==='client'?'block':'none';
  document.getElementById('navDots').style.display = v==='client'?'flex':'none';
  if(v==='admin'){ renderDash(); renderFStaff(); renderTable(); }
  if(v==='client'){ resetGender(); }
}

// ══ GENDER ═════════════════════════════════════════════════════
function setGender(g){
  selGender=g; selSrv=null; selStaff=null; selTime=null;
  document.getElementById('gBtnMale').classList.toggle('on', g==='male');
  document.getElementById('gBtnFemale').classList.toggle('on', g==='female');
  const isFemale = g==='female';

  ['services','staff','booking','waveBook','sepStaff'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.style.display='block';
  });

  const srvTag=document.getElementById('srvSecTag');
  const srvTitle=document.getElementById('srvSecTitle');
  const srvDivider=document.getElementById('srvDivider');
  if(isFemale){
    srvTag.className='sec-tag pink'; srvTag.textContent='Servicios para Mujeres';
    srvTitle.innerHTML='ELIGE TU <span class="p">SERVICIO</span>';
    srvDivider.className='divider pink';
  } else {
    srvTag.className='sec-tag'; srvTag.textContent='Nuestros Servicios';
    srvTitle.innerHTML='ELIGE TU <span class="g">ESTILO</span>';
    srvDivider.className='divider';
  }

  const staffTag=document.getElementById('staffSecTag');
  const staffTitle=document.getElementById('staffSecTitle');
  const staffSub=document.getElementById('staffSecSub');
  const staffDiv=document.getElementById('staffDivider');
  if(isFemale){
    staffTag.className='sec-tag pink'; staffTag.textContent='Nuestras Estilistas';
    staffTitle.innerHTML='NUESTRAS <span class="p">EXPERTAS</span>';
    staffSub.textContent='Escoge tu estilista de confianza';
    staffDiv.className='divider pink';
  } else {
    staffTag.className='sec-tag'; staffTag.textContent='El Equipo';
    staffTitle.innerHTML='NUESTROS <span class="g">MAESTROS</span>';
    staffSub.textContent='Escoge tu barbero de confianza';
    staffDiv.className='divider';
  }

  const bookWrap=document.getElementById('bookWrap');
  const bookTag=document.getElementById('bookSecTag');
  const bookAccent=document.getElementById('bookSecAccent');
  const bookDiv=document.getElementById('bookDivider');
  const subBtn=document.getElementById('subBtn');
  const sumBox=document.getElementById('sumBox');
  if(isFemale){
    bookWrap.className='book-wrap female-book';
    bookTag.className='sec-tag pink';
    bookAccent.className='p';
    bookDiv.className='divider pink';
    subBtn.className='sub-btn pink-sub'; subBtn.textContent='💅 CONFIRMAR RESERVACIÓN';
    sumBox.className='sum-box pink-sum';
  } else {
    bookWrap.className='book-wrap';
    bookTag.className='sec-tag';
    bookAccent.className='g';
    bookDiv.className='divider';
    subBtn.className='sub-btn'; subBtn.textContent='✂ CONFIRMAR RESERVACIÓN';
    sumBox.className='sum-box';
  }

  renderClientSrv(); renderClientStaff(); buildTimeGrid();
  setTimeout(()=>document.getElementById('services').scrollIntoView({behavior:'smooth', block:'start'}), 100);
}

function resetGender(){
  selGender=null; selSrv=null; selStaff=null; selTime=null;
  document.getElementById('gBtnMale').classList.remove('on');
  document.getElementById('gBtnFemale').classList.remove('on');
  ['services','staff','booking','waveBook','sepStaff'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.style.display='none';
  });
}

// ══ CLIENT GRIDS ═══════════════════════════════════════════════
function durFmt(min){ min=min||60; return min>=60?`${Math.floor(min/60)}h${min%60?` ${min%60}min`:''}`:`${min} min`; }

function renderClientSrv(){
  const isFemale = selGender==='female';
  const list = isFemale ? servicesF : services;
  document.getElementById('srvGrid').innerHTML = list.map(s=>`
    <div class="srv-card ${selSrv===s.id?'sel':''} ${isFemale?'female':''}" onclick="pickSrv(${s.id})">
      <div class="sel-ck ${isFemale?'pink':''}">✔</div>
      <div class="srv-img ${isFemale?'pink-bg':''}">
        ${s.image_url?`<img src="${escQ(s.image_url)}" alt="${escQ(s.name)}">`:`<span class="emo">${s.emoji}</span>`}
        <span class="srv-dur ${isFemale?'pink':''}">${durFmt(s.duration_minutes)}</span>
      </div>
      <div class="srv-body">
        <div class="srv-name">${s.name}</div>
        <div class="srv-desc">${s.description||''}</div>
        <div class="srv-foot">
          <div>
            <div class="srv-price ${isFemale?'pink':''}">$${s.price.toLocaleString()}</div>
            <div class="srv-min">Duración: ${durFmt(s.duration_minutes)}</div>
          </div>
          <button class="srv-btn ${isFemale?'pink':''}">${selSrv===s.id?'✔ Seleccionado':'Seleccionar'}</button>
        </div>
      </div>
    </div>`).join('');
}

function pickSrv(id){
  selSrv = selSrv===id ? null : id;
  renderClientSrv();
  updateSummary();
  if(selSrv){
    // Asegurar que la sección staff esté visible antes de hacer scroll
    const staffSec = document.getElementById('staff');
    const sepStaff = document.getElementById('sepStaff');
    if(staffSec) staffSec.style.display = 'block';
    if(sepStaff) sepStaff.style.display = 'block';
    setTimeout(()=> staffSec.scrollIntoView({behavior:'smooth', block:'start'}), 150);
  }
}

function renderClientStaff(){
  const isFemale = selGender==='female';
  const list = isFemale ? stylists : barbers;
  document.getElementById('staffGrid').innerHTML = list.map(p=>`
    <div class="brb-card ${selStaff===p.id?'sel':''} ${isFemale?'female':''}" onclick="pickStaff(${p.id})">
      <div class="brb-si ${isFemale?'pink':''}">✔</div>
      <div class="brb-av ${isFemale?'pink-av':''}">
        ${p.image_url?`<img src="${escQ(p.image_url)}" alt="${escQ(p.name)}">`:`<span class="emo">${p.emoji}</span>`}
      </div>
      <div class="brb-name">${p.name}</div>
      <div class="brb-title ${isFemale?'pink':''}">${p.title}</div>
      <div class="brb-stars">${'⭐'.repeat(p.stars)}</div>
      <div class="brb-exp">🕐 ${p.experience} de experiencia</div>
      <div class="brb-spec">${p.specialties||''}</div>
      ${p.phone||p.instagram?`<div class="brb-social">
        ${p.phone?`<a class="brb-social-btn wa-btn" href="https://wa.me/${p.phone.replace(/\D/g,'')}" target="_blank" onclick="event.stopPropagation()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.118 1.528 5.855L0 24l6.335-1.508A11.945 11.945 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.885 0-3.65-.51-5.17-1.4l-.37-.22-3.76.895.952-3.668-.242-.378A9.96 9.96 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
          WhatsApp
        </a>`:''}
        ${p.instagram?`<a class="brb-social-btn ig-btn" href="${p.instagram.startsWith('http')?p.instagram:'https://instagram.com/'+p.instagram}" target="_blank" onclick="event.stopPropagation()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
          Instagram
        </a>`:''}
      </div>`:''}
    </div>`).join('');
}

function pickStaff(id){
  selStaff = selStaff===id ? null : id;
  renderClientStaff();
  updateSummary();
  if(selStaff) setTimeout(()=>document.getElementById('booking').scrollIntoView({behavior:'smooth', block:'start'}), 150);
}

// ══ TIME GRID ══════════════════════════════════════════════════
async function buildTimeGrid(){
  selTime = null;
  const date = document.getElementById('bDate').value;
  const isFemale = selGender==='female';
  if(!date){
    document.getElementById('tGrid').innerHTML='<p style="color:var(--text-muted);font-size:12px;grid-column:1/-1">Selecciona primero una fecha.</p>';
    updateSummary(); return;
  }
  const dow = new Date(date+'T00:00:00').getDay();
  if(isFemale && dow===0){
    document.getElementById('tGrid').innerHTML=`
      <div style="grid-column:1/-1;background:rgba(192,57,43,0.08);border:1px solid rgba(192,57,43,0.25);border-radius:10px;padding:14px 16px;text-align:center">
        <div style="font-size:18px;margin-bottom:6px">💅</div>
        <div style="font-size:13px;color:var(--text-muted);line-height:1.5">
          Los domingos nuestro servicio de estilismo no está disponible.<br>
          <span style="color:var(--pink);font-weight:600">Por favor elige un día de lunes a sábado.</span>
        </div>
      </div>`;
    updateSummary(); return;
  }
  const allSlots = getTimes(date, isFemale);
  if(!allSlots.length){
    document.getElementById('tGrid').innerHTML='<p style="color:var(--text-muted);font-size:12px;grid-column:1/-1">No hay horarios disponibles para este día.</p>';
    updateSummary(); return;
  }

  // Filtrar horas pasadas si la fecha es hoy
  // Obtener la fecha de hoy en formato local (YYYY-MM-DD)
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const today = `${year}-${month}-${day}`;
  
  const isToday = date === today;
  let availableSlots = allSlots;
  
  console.log(`📅 Hoy (local): ${today}, Seleccionado: ${date}, ¿Es hoy?: ${isToday}`);
  
  if(isToday) {
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTotalMinutes = currentHour * 60 + currentMinute;
    
    console.log(`⏰ Hora actual: ${currentHour}:${String(currentMinute).padStart(2,'0')} (${currentTotalMinutes} minutos)`);
    
    // Filtrar slots que ya pasaron (agregar 30 minutos de margen)
    availableSlots = allSlots.filter(slot => {
      const [h, m] = slot.split(':').map(Number);
      const slotTotalMinutes = h * 60 + m;
      const isPast = slotTotalMinutes <= currentTotalMinutes + 30;
      if(isPast) {
        console.log(`❌ Slot ${slot} filtrado (ya pasó)`);
      }
      return !isPast; // Retornar true si NO es pasado
    });
    
    console.log(`✅ Slots disponibles después del filtro: ${availableSlots.length} de ${allSlots.length}`);
    
    if(availableSlots.length === 0) {
      const isFemaleMsg = isFemale;
      document.getElementById('tGrid').innerHTML=`
        <div style="grid-column:1/-1;background:rgba(192,57,43,0.08);border:1px solid rgba(192,57,43,0.25);border-radius:10px;padding:14px 16px;text-align:center">
          <div style="font-size:18px;margin-bottom:6px">⏰</div>
          <div style="font-size:13px;color:var(--text-muted);line-height:1.5">
            Ya no hay horarios disponibles para hoy.<br>
            <span style="color:${isFemaleMsg?'var(--pink)':'var(--gold)'};font-weight:600">Por favor selecciona otra fecha.</span>
          </div>
        </div>`;
      updateSummary(); 
      return;
    }
  }

  // Duración del servicio seleccionado (en minutos)
  const list = isFemale ? servicesF : services;
  const srv = list.find(s=>s.id===selSrv);
  const durMin = srv ? (srv.duration_minutes || 60) : 60;
  const durSlots = Math.ceil(durMin / 15); // cuántos slots de 15 min ocupa

  // Obtener slots tomados para el staff seleccionado
  const staffMember = (isFemale?stylists:barbers).find(p=>p.id===selStaff);
  const staffParam = staffMember ? `&staff=${encodeURIComponent(staffMember.name)}` : '';
  
  let taken = [];
  try {
    const res = await fetch(`/api/appointments/taken?date=${date}${staffParam}`);
    if(res.ok) {
      taken = await res.json();
    }
  } catch(e) {
    console.error('Error obteniendo slots tomados:', e);
  }
  
  console.log(`📅 Fecha: ${date}, Slots tomados: ${taken.length}`, taken);

  // Mensaje de horario según el día
  let schedule;
  if(dow === 0) {
    // Domingo
    schedule = isFemale 
      ? '🕗 Domingo: No hay servicio de estilismo'
      : '🕗 Domingo: 8:00 am – 12:00 pm';
  } else if(dow === 6) {
    // Sábado
    schedule = isFemale
      ? '🕗 Sábado: 9:00 am – 8:00 pm'
      : '🕗 Sábado: 8:00 am – 8:00 pm';
  } else {
    // Lunes a Viernes
    schedule = isFemale
      ? '🕗 Lun–Vie: 9:00–11:00 am · 2:00–8:00 pm'
      : '🕗 Lun–Vie: 8:00–11:00 am · 2:00–8:00 pm';
  }

  const durLabel = durFmt(durMin);

  document.getElementById('tGrid').innerHTML =
    `<p style="color:var(--text-muted);font-size:11px;grid-column:1/-1;margin-bottom:4px">${schedule} · Duración: ${durLabel}</p>`+
    availableSlots.map((t,idx)=>{
      // Verificar si este slot y los siguientes necesarios están libres
      // Buscar en allSlots para obtener los índices correctos
      const startIdx = allSlots.indexOf(t);
      const needed = allSlots.slice(startIdx, startIdx + durSlots);
      const isBlocked = needed.length < durSlots || needed.some(s=>taken.includes(s));
      const h = parseInt(t); const m = t.split(':')[1];
      const ampm = h<12 ? `${h}:${m} am` : h===12 ? `12:${m} pm` : `${h-12}:${m} pm`;
      // Calcular hora fin
      const startMin = h*60+parseInt(m);
      const endMin = startMin + durMin;
      const eh = Math.floor(endMin/60); const em = String(endMin%60).padStart(2,'0');
      const endAmpm = eh<12?`${eh}:${em} am`:eh===12?`12:${em} pm`:`${eh-12}:${em} pm`;
      return isBlocked
        ? `<button class="tbtn taken" onclick="takenMsg()">
            ${ampm}<br><span style="font-size:9px">😔 Ocupado</span>
           </button>`
        : `<button class="tbtn ${isFemale?'pink-t':''} ${selTime===t?(isFemale?'sel-t pink-sel':'sel-t'):''}" onclick="pickTime('${t}')">
            ${ampm}<br><span style="font-size:9px;opacity:.6">–${endAmpm}</span>
           </button>`;
    }).join('');
  updateSummary();
}

function getTimes(dateStr, isFemale){
  if(!dateStr) return [];
  const dow = new Date(dateStr+'T00:00:00').getDay(); // 0=domingo, 1=lunes, ..., 6=sábado
  
  // Domingo: solo hombres 8am-12pm, mujeres no hay servicio
  if(dow === 0){
    if(isFemale) return [];
    return generateSlots(8, 12);
  }
  
  // Sábado (dow === 6)
  if(dow === 6){
    const start = isFemale ? 9 : 8;
    return generateSlots(start, 20); // Sábado: corrido de 8am/9am a 8pm
  }
  
  // Lunes a Viernes (dow 1-5)
  const slots = [];
  const startMorning = isFemale ? 9 : 8;
  
  // Mañana: 8am/9am - 11am
  slots.push(...generateSlots(startMorning, 11));
  
  // Tarde: 2pm - 8pm
  slots.push(...generateSlots(14, 20));
  
  return slots;
}

// Función auxiliar para generar slots de 15 minutos
function generateSlots(startH, endH){
  const slots = [];
  for(let m = startH*60; m < endH*60; m+=15){
    const h = Math.floor(m/60);
    const mm = m%60;
    slots.push(`${String(h).padStart(2,'0')}:${String(mm).padStart(2,'0')}`);
  }
  return slots;
}

function pickTime(t){
  selTime = t;
  const isFemale = selGender==='female';
  document.querySelectorAll('.tbtn:not(.taken)').forEach(b=>{
    const active = b.textContent.trim().startsWith(t);
    b.classList.toggle('sel-t', active);
    b.classList.toggle('pink-sel', active && isFemale);
  });
  updateSummary();

  // Scroll directo al botón de confirmar reservación
  setTimeout(() => {
    const subBtn = document.getElementById('subBtn');
    if(subBtn){
      subBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
      // Efecto visual en el botón para llamar la atención
      subBtn.style.transform = 'scale(1.04)';
      subBtn.style.boxShadow = isFemale
        ? '0 0 0 4px rgba(233,30,140,0.4), 0 12px 28px rgba(233,30,140,0.4)'
        : '0 0 0 4px rgba(212,175,55,0.4), 0 12px 28px rgba(212,175,55,0.4)';
      setTimeout(() => {
        subBtn.style.transform = '';
        subBtn.style.boxShadow = '';
      }, 900);
    }
    // Enfocar nombre si está vacío
    const nameInput = document.getElementById('cName');
    if(nameInput && !nameInput.value){
      setTimeout(() => nameInput.focus(), 600);
    }
  }, 150);
}

function takenMsg(){ showToast('😔 Ese horario ya está ocupado. Elige otra hora.', 'error'); }

// ══ SUMMARY ════════════════════════════════════════════════════
function updateSummary(){
  const box = document.getElementById('sumBox');
  const isFemale = selGender==='female';
  const list = isFemale ? servicesF : services;
  const srv = list.find(s=>s.id===selSrv);
  const staff = (isFemale?stylists:barbers).find(p=>p.id===selStaff);
  if(!srv && !staff && !selTime){ box.style.display='none'; return; }
  let h = isFemale
    ? `<div class="sum-title pink">📋 Resumen de tu cita</div>`
    : `<div class="sum-title">📋 Resumen de tu cita</div>`;
  if(srv){
    if(isFemale){
      const abono = Math.round(srv.price * 0.20);
      const total = srv.price + abono;
      h+=`<div class="sum-row"><span>Servicio</span><span>${srv.name}</span></div>`;
      h+=`<div class="sum-row"><span>Precio del servicio</span><span>$${srv.price.toLocaleString()}</span></div>`;
      h+=`<div class="sum-row" style="color:var(--pink)"><span>💅 Abono (20%)</span><span>$${abono.toLocaleString()}</span></div>`;
      h+=`<div class="sum-row pink-total"><span>Total</span><span>$${total.toLocaleString()}</span></div>`;
    } else {
      h+=`<div class="sum-row"><span>${srv.name}</span><span>$${srv.price.toLocaleString()}</span></div>`;
    }
  }
  if(staff) h+=`<div class="sum-row"><span>${isFemale?'Estilista':'Barbero'}</span><span>${staff.name}</span></div>`;
  if(selTime){
    const durMin2 = srv ? (srv.duration_minutes||60) : 60;
    const [sh,sm] = selTime.split(':').map(Number);
    const endMin2 = sh*60+sm+durMin2;
    const eh=Math.floor(endMin2/60); const em=String(endMin2%60).padStart(2,'0');
    const durLabel = durMin2>=60?`${Math.floor(durMin2/60)}h${durMin2%60?` ${durMin2%60}min`:''}`:`${durMin2} min`;
    h+=`<div class="sum-row"><span>Hora</span><span>${selTime} – ${eh}:${em}</span></div>`;
    h+=`<div class="sum-row"><span>Duración</span><span>${durLabel}</span></div>`;
  }
  if(srv && !isFemale) h+=`<div class="sum-row"><span>Total</span><span>$${srv.price.toLocaleString()}</span></div>`;
  box.innerHTML=h; box.style.display='block';
}

// ══ SUBMIT BOOKING ═════════════════════════════════════════════
async function submitBooking(){
  console.log('🚀 === INICIO DE submitBooking() ===');
  const name = document.getElementById('cName').value.trim();
  const phone = document.getElementById('cPhone').value.trim();
  const date = document.getElementById('bDate').value;
  console.log('📝 Datos capturados:', {name, phone, date, selGender, selSrv, selStaff, selTime});
  const al = document.getElementById('selAlert');
  const isFemale = selGender==='female';
  if(!selGender){ showToast('👥 Primero selecciona tu género', 'error'); goSec('genderSec'); return; }
  if(!selSrv){ al.style.display='block'; al.textContent='⚠ Por favor selecciona un servicio.'; goSec('services'); return; }
  if(!selStaff){ al.style.display='block'; al.textContent=`⚠ Por favor selecciona ${isFemale?'una estilista':'un barbero'}.`; goSec('staff'); return; }
  al.style.display='none';
  if(!name){ showToast('📝 Por favor ingresa tu nombre completo', 'error'); return; }
  if(!phone){ showToast('📱 Por favor ingresa tu teléfono', 'error'); return; }
  if(!date){ showToast('📅 Por favor selecciona una fecha', 'error'); return; }
  if(!selTime){ showToast('🕐 Por favor selecciona una hora', 'error'); return; }

  const list = isFemale ? servicesF : services;
  const srv = list.find(s=>s.id===selSrv);
  const staffMember = (isFemale?stylists:barbers).find(p=>p.id===selStaff);
  const durMin = srv.duration_minutes || 60;
  const [sh2,sm2] = selTime.split(':').map(Number);
  const endMin2 = sh2*60+sm2+durMin;
  const end = `${Math.floor(endMin2/60)}:${String(endMin2%60).padStart(2,'0')}`;

  console.log('📤 Enviando petición al servidor...');
  const res = await fetch('/api/appointments', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      client_name: name, client_phone: phone, gender: selGender,
      service_name: srv.name, staff_name: staffMember.name,
      date, time: selTime, total: `$${isFemale ? (srv.price + Math.round(srv.price * 0.20)).toLocaleString() : srv.price.toLocaleString()}`
    })
  });
  const data = await res.json();
  console.log('📥 Respuesta recibida:', data);
  if(!data.success){ 
    console.error('❌ Reserva fallida:', data.message);
    // Mostrar modal de error con estilos inline para asegurar que aparezca
    const errorModal = document.getElementById('errorModal');
    document.getElementById('errorMessage').textContent = data.message || 'Error al reservar. Por favor selecciona otra fecha y hora.';
    
    // Forzar display con JavaScript directo
    errorModal.style.display = 'flex';
    errorModal.style.position = 'fixed';
    errorModal.style.inset = '0';
    errorModal.style.zIndex = '99999';
    errorModal.style.background = 'rgba(0,0,0,0.9)';
    errorModal.style.alignItems = 'center';
    errorModal.style.justifyContent = 'center';
    errorModal.classList.add('open');
    
    document.body.style.overflow = 'hidden';
    buildTimeGrid(); 
    return; 
  }

  console.log('✅ Reserva exitosa! Mostrando modal AHORA...');
  
  // PASO 1: MOSTRAR MODAL INMEDIATAMENTE con JavaScript puro
  const modalElement = document.getElementById('okModal');
  if(modalElement) {
    // Forzar display con JavaScript directo
    modalElement.style.display = 'flex';
    modalElement.style.position = 'fixed';
    modalElement.style.inset = '0';
    modalElement.style.zIndex = '99999';
    modalElement.style.background = 'rgba(0,0,0,0.9)';
    modalElement.style.alignItems = 'center';
    modalElement.style.justifyContent = 'center';
    modalElement.classList.add('open');
    
    // Bloquear scroll
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    
    console.log('✅ Modal mostrado con estilos inline');
  } else {
    console.error('❌ No se encontró el modal okModal');
    alert('Error: No se encontró el modal. Por favor recarga la página.');
    return;
  }
  
  // PASO 2: Mostrar toast
  showToast('✅ ¡Reserva confirmada!', 'ok');
  
  // PASO 3: Ahora sí, preparar los datos del modal (en segundo plano)
  // Verificar fidelidad SOLO para barberos (género masculino)
  let fidelityData = { count: 0 };
  if (!isFemale) {
    const fidelityRes = await fetch(`/api/appointments/fidelity?name=${encodeURIComponent(name.toLowerCase())}&phone=${encodeURIComponent(phone)}&staff=${encodeURIComponent(staffMember.name)}`);
    fidelityData = await fidelityRes.json();
  }
  const currentCount = fidelityData.count || 0;
  const newCount = currentCount + 1;
  const nextFreeCut = 10 - newCount; // cuántos faltan DESPUÉS de esta reserva

  document.getElementById('okDets').innerHTML = (()=>{
    const abono = isFemale ? Math.round(srv.price*0.20) : 0;
    const total = isFemale ? srv.price + abono : srv.price;
    let rows = `
      <div class="mdr"><span>Cliente</span><span>${name}</span></div>
      <div class="mdr"><span>Teléfono</span><span>${phone}</span></div>
      <div class="mdr"><span>Servicio</span><span>${srv.name}</span></div>
      <div class="mdr"><span>${isFemale?'Estilista':'Barbero'}</span><span>${staffMember.name}</span></div>
      <div class="mdr"><span>Fecha</span><span>${fmtDate(date)}</span></div>
      <div class="mdr"><span>Hora</span><span>${selTime} – ${end}</span></div>
      <div class="mdr"><span>Precio del servicio</span><span>$${srv.price.toLocaleString()}</span></div>`;
    if(isFemale) rows += `<div class="mdr" style="color:var(--pink)"><span>💅 Abono (20%)</span><span>$${abono.toLocaleString()}</span></div>`;
    rows += `<div class="mdr" style="font-weight:700"><span>Total</span><span>$${total.toLocaleString()}</span></div>`;
    
    // Tarjeta de fidelidad SOLO para barberos (género masculino)
    if (!isFemale) {
      const isReady = newCount >= 10;
      rows += `<div style="background:rgba(212,175,55,0.1);border:1px solid var(--gold);border-radius:8px;padding:12px;margin-top:10px">
        <div style="font-size:11px;color:var(--gold);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">💳 Tarjeta de Fidelidad</div>
        <div style="font-size:14px;color:var(--text-light);margin-bottom:6px">
          Llevas <span style="color:var(--gold);font-weight:700">${newCount}</span> de <span style="color:var(--gold);font-weight:700">10</span> cortes
        </div>
        <div style="display:flex;gap:3px;flex-wrap:wrap;margin-bottom:8px">
          ${Array.from({length:10},(_,i)=>`<span style="font-size:18px">${i < newCount ? '✂️' : '⬜'}</span>`).join('')}
        </div>
        ${isReady
          ? `<div style="color:var(--green);font-weight:700;font-size:13px;background:rgba(39,174,96,0.15);padding:8px;border-radius:6px;text-align:center">🎉 ¡Tienes un corte gratis! Díselo al barbero.</div>`
          : `<div style="font-size:12px;color:var(--text-muted)">Faltan <span style="color:var(--gold);font-weight:700">${nextFreeCut}</span> corte${nextFreeCut===1?'':'s'} para el siguiente gratis</div>`
        }
      </div>`;
    }
    
    return rows;
  })();
  
  // PASO 4: Limpiar formulario (sin re-renderizar para evitar efectos secundarios)
  selSrv=null; selStaff=null; selTime=null;
  document.getElementById('cName').value='';
  document.getElementById('cPhone').value='';
  document.getElementById('bDate').value='';
  document.getElementById('tGrid').innerHTML='<p style="color:var(--text-muted);font-size:12px;grid-column:1/-1">Selecciona primero una fecha.</p>';
  document.getElementById('sumBox').style.display='none';
  
  // PASO 5: Re-renderizar las tarjetas después de un delay (cuando el modal ya está visible)
  setTimeout(() => {
    renderClientSrv(); 
    renderClientStaff();
  }, 1000);
}

// ══ CANCEL ═════════════════════════════════════════════════════
async function searchCancel(){
  const name = document.getElementById('cancelName').value.trim().toLowerCase();
  // Limpiar teléfono: quitar espacios, guiones y el prefijo +57
  const phone = document.getElementById('cancelPhone').value.trim().replace(/[\s\-\(\)]/g,'').replace(/^\+57/,'');
  const res = document.getElementById('cancelResults');
  if(!name||!phone){ showToast('📋 Por favor ingresa tu nombre y teléfono', 'error'); return; }

  // Mostrar estado de carga
  res.innerHTML=`<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px">🔍 Buscando...</div>`;

  try {
    const r = await fetch(`/api/appointments/search?name=${encodeURIComponent(name)}&phone=${encodeURIComponent(phone)}`);
    if(!r.ok){ throw new Error('Error del servidor'); }
    const found = await r.json();
    if(!found.length){
      res.innerHTML=`<div style="background:rgba(192,57,43,0.09);border:1px solid rgba(192,57,43,0.27);color:var(--red-bright);padding:14px;border-radius:10px;font-size:14px;text-align:center;margin-top:12px">😔 No encontramos citas pendientes con esos datos.<br><span style="font-size:12px;opacity:.7">Verifica que el nombre y teléfono sean exactamente los que usaste al reservar.</span></div>`;
      return;
    }
    res.innerHTML=`<div style="margin-top:16px;display:flex;flex-direction:column;gap:10px">`+
      found.map(a=>`
        <div style="background:var(--dark-bg);border:1px solid var(--dark-border);border-radius:12px;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
          <div>
            <div style="font-family:var(--font-serif);font-weight:700;font-size:15px;margin-bottom:4px">${a.service}</div>
            <div style="font-size:13px;color:var(--text-muted)">${a.gender==='female'?'💅':'🧔'} ${a.staff} · 📅 ${fmtDate(a.date)} · 🕐 ${a.time}</div>
            <div style="font-size:13px;color:var(--gold);margin-top:3px">${a.total}</div>
          </div>
          <button onclick="doCancel(${a.id}, this)" style="background:linear-gradient(135deg,var(--red-bright),var(--red));color:#fff;border:none;padding:10px 20px;border-radius:9px;font-weight:700;font-size:13px;cursor:pointer;font-family:var(--font-body);white-space:nowrap">✖ Cancelar</button>
        </div>`).join('')+`</div>`;
  } catch(e) {
    res.innerHTML=`<div style="background:rgba(192,57,43,0.09);border:1px solid rgba(192,57,43,0.27);color:var(--red-bright);padding:14px;border-radius:10px;font-size:14px;text-align:center;margin-top:12px">❌ Error al buscar. Intenta de nuevo.</div>`;
  }
}

async function doCancel(id, btn){
  if(!confirm('¿Seguro que deseas cancelar esta cita?')) return;

  // Deshabilitar botón para evitar doble clic
  if(btn){ btn.disabled=true; btn.textContent='Cancelando...'; }

  try {
    const r = await fetch(`/api/appointments/${id}/cancel`, {method:'POST'});
    const data = await r.json();

    if(!r.ok || !data.success){
      showToast('❌ ' + (data.message||'No pudimos cancelar la cita'), 'error');
      if(btn){ btn.disabled=false; btn.textContent='✖ Cancelar'; }
      return;
    }

    // Limpiar formulario
    document.getElementById('cancelName').value='';
    document.getElementById('cancelPhone').value='';
    document.getElementById('cancelResults').innerHTML='';

    // Mostrar modal de confirmación
    const modal = document.getElementById('cancelModal');
    modal.style.display='flex';
    modal.style.position='fixed';
    modal.style.inset='0';
    modal.style.zIndex='99999';
    modal.style.background='rgba(0,0,0,0.85)';
    modal.style.alignItems='center';
    modal.style.justifyContent='center';
    modal.classList.add('open');
    document.body.style.overflow='hidden';

    buildTimeGrid();
  } catch(e) {
    showToast('❌ Error de conexión. Intenta de nuevo.', 'error');
    if(btn){ btn.disabled=false; btn.textContent='✖ Cancelar'; }
  }
}

// ══ ADMIN TABS ═════════════════════════════════════════════════
const TAB_IDS=['dash','citas','servicios','barberos','estilistas','srvmujer','inactivos','marca','resenas','fidelidad','config'];
function setTab(id){
  document.querySelectorAll('.atab').forEach((b,i)=>b.classList.toggle('on', TAB_IDS[i]===id));
  document.querySelectorAll('.acontent').forEach(c=>c.classList.remove('on'));
  document.getElementById('tab-'+id).classList.add('on');
  if(id==='dash') renderDash();
  if(id==='citas'){ renderFStaff(); renderTable(); }
  if(id==='servicios') renderSrvRows();
  if(id==='barberos') renderBrbRows();
  if(id==='estilistas') renderStyRows();
  if(id==='srvmujer') renderSrvFRows();
  if(id==='inactivos'){ setupInactiveDateInput(); renderInactiveStaffSelect(); renderInactiveDaysList(); }
  if(id==='marca') renderMarca();
  if(id==='resenas') renderAdminReviews();
  if(id==='fidelidad') renderFidelityCards();
  if(id==='config') renderConfig();
}

// ══ DASHBOARD ══════════════════════════════════════════════════
async function renderDash(){
  const res = await fetch('/api/appointments');
  const appts = await res.json();
  const tot=appts.length;
  const pend=appts.filter(a=>a.status==='Pendiente').length;
  const done=appts.filter(a=>a.status==='Completado').length;
  const canc=appts.filter(a=>a.status==='Cancelado').length;
  const rev=appts.filter(a=>a.status==='Completado').reduce((s,a)=>s+parseInt((a.total||'0').replace(/\D/g,'')),0);

  // Verificar estado del scheduler
  let schedulerHtml = '';
  try {
    const sRes = await fetch('/api/scheduler/status');
    if(sRes.ok){
      const sData = await sRes.json();
      if(sData.running){
        const resetJob = (sData.jobs||[]).find(j=>j.id==='weekly_reset');
        const nextReset = resetJob ? resetJob.next_run : 'N/A';
        schedulerHtml = `<div class="astat" style="border-color:var(--green)"><div class="astat-n" style="color:var(--green);font-size:20px">✅</div><div class="astat-l">Reset activo</div><div style="font-size:9px;color:var(--text-muted);margin-top:3px">${nextReset}</div></div>`;
      } else {
        schedulerHtml = `<div class="astat" style="border-color:var(--red-bright)"><div class="astat-n" style="color:var(--red-bright);font-size:20px">⚠️</div><div class="astat-l">Reset inactivo</div></div>`;
      }
    }
  } catch(e) {}

  document.getElementById('astats').innerHTML=`
    <div class="astat"><div class="astat-n">${tot}</div><div class="astat-l">Total Citas</div></div>
    <div class="astat"><div class="astat-n" style="color:var(--gold)">${pend}</div><div class="astat-l">Pendientes</div></div>
    <div class="astat"><div class="astat-n" style="color:var(--green)">${done}</div><div class="astat-l">Completadas</div></div>
    <div class="astat"><div class="astat-n" style="color:var(--red-bright)">${canc}</div><div class="astat-l">Canceladas</div></div>
    <div class="astat"><div class="astat-n">${rev.toLocaleString()}</div><div class="astat-l">Ingresos</div></div>
    <div class="astat"><div class="astat-n">${barbers.length+stylists.length}</div><div class="astat-l">Personal</div></div>
    ${schedulerHtml}`;
  document.getElementById('heroClients').textContent='100+';
  document.getElementById('heroStaff').textContent=(barbers.length+stylists.length)+'+';
  document.getElementById('brbStatsGrid').innerHTML=barbers.map(b=>staffStatCard(b,appts,'male')).join('');
  document.getElementById('styStatsGrid').innerHTML=stylists.map(s=>staffStatCard(s,appts,'female')).join('');
}
function staffStatCard(p, appts, gender){
  const isFemale=gender==='female';
  const pa=appts.filter(a=>a.staff===p.name);
  const done=pa.filter(a=>a.status==='Completado');
  const pend=pa.filter(a=>a.status==='Pendiente');
  const canc=pa.filter(a=>a.status==='Cancelado');
  const rev=done.reduce((s,a)=>s+parseInt((a.total||'0').replace(/\D/g,'')),0);
  return`<div class="brb-stat-card ${isFemale?'female-card':''}">
    <div class="brb-stat-av">${p.image_url?`<img src="${p.image_url}" alt="">`:`<span style="font-size:20px">${p.emoji}</span>`}</div>
    <div class="brb-stat-name">${p.name}<br><span style="font-size:10px;font-weight:400;color:${isFemale?'var(--pink)':'var(--gold)'}">${p.title}</span></div>
    <div class="brb-stat-row"><span>Total citas</span><span class="brb-stat-val">${pa.length}</span></div>
    <div class="brb-stat-row"><span>Pendientes</span><span style="color:var(--gold)">${pend.length}</span></div>
    <div class="brb-stat-row"><span>Completadas</span><span style="color:var(--green)">${done.length}</span></div>
    <div class="brb-stat-row"><span>Canceladas</span><span style="color:var(--red-bright)">${canc.length}</span></div>
    <div class="brb-stat-row"><span>Ingresos</span><span>$${rev.toLocaleString()}</span></div>
  </div>`;
}

// ══ CITAS TABLE ════════════════════════════════════════════════
function renderFStaff(){
  const sel=document.getElementById('fStaff'); const cur=sel.value;
  sel.innerHTML='<option value="">Todo el personal</option>';
  [...barbers,...stylists].forEach(p=>{ sel.innerHTML+=`<option ${cur===p.name?'selected':''}>${p.name}</option>`; });
}

async function renderTable(){
  const res = await fetch('/api/appointments');
  let list = await res.json();
  const nf=(document.getElementById('fName')?.value||'').toLowerCase();
  const sf=document.getElementById('fStaff')?.value||'';
  const stf=document.getElementById('fStatus')?.value||'';
  const gf=document.getElementById('fGender')?.value||'';
  list=list.filter(a=>
    (!nf||a.name.toLowerCase().includes(nf))&&
    (!sf||a.staff===sf)&&(!stf||a.status===stf)&&(!gf||a.gender===gf)
  );
  list.sort((a,b)=>{
    if(a.status==='Pendiente'&&b.status!=='Pendiente') return -1;
    if(a.status!=='Pendiente'&&b.status==='Pendiente') return 1;
    return (a.date+a.time)<(b.date+b.time)?-1:1;
  });
  
  // Verificar fidelidad para cada cita pendiente (solo barberos - género masculino)
  const fidelityChecks = {};
  const fidelityInfo = {};
  for(const a of list.filter(appt => appt.status === 'Pendiente' && appt.gender === 'male')) {
    const key = `${a.name.toLowerCase()}-${a.phone}-${a.staff}`;
    if (!fidelityChecks[key]) {
      try {
        const fRes = await fetch(`/api/appointments/fidelity?name=${encodeURIComponent(a.name.toLowerCase())}&phone=${encodeURIComponent(a.phone)}&staff=${encodeURIComponent(a.staff)}`);
        const fData = await fRes.json();
        const count = fData.count || 0;
        fidelityChecks[key] = count === 10; // Elegible para corte gratis
        fidelityInfo[key] = count; // Guardar el número de cortes para mostrar
      } catch(e) {
        fidelityChecks[key] = false;
        fidelityInfo[key] = 0;
      }
    }
  }
  
  const tb=document.getElementById('tBody'), nd=document.getElementById('noData');
  if(!list.length){ tb.innerHTML=''; nd.style.display='block'; return; }
  nd.style.display='none';
  tb.innerHTML=list.map(a=>{
    const fidelityKey = `${a.name.toLowerCase()}-${a.phone}-${a.staff}`;
    const isEligibleForFree = fidelityChecks[fidelityKey] || false;
    const currentCuts = fidelityInfo[fidelityKey] || 0;
    const isFreecut = a.is_free_cut || false;
    
    return `
    <tr ${a.status==='Pendiente' && a.gender==='male' && isEligibleForFree ? 'style="background:rgba(46,204,113,0.1);border-left:4px solid var(--green)"' : ''}>
      <td style="color:var(--text-muted)">#${a.id}</td>
      <td>
        <strong>${a.name}</strong>
        ${isFreecut ? ' <span style="color:var(--green);font-size:11px">🎁 GRATIS</span>' : ''}
        ${a.status==='Pendiente' && a.gender==='male' && isEligibleForFree ? ' <span style="color:var(--green);font-size:11px;font-weight:700">⭐ LISTO PARA GRATIS</span>' : ''}
        ${a.status==='Pendiente' && a.gender==='male' && currentCuts > 0 && currentCuts < 10 ? ` <span style="color:var(--gold);font-size:10px">(${currentCuts}/10)</span>` : ''}
      </td>
      <td>${a.phone}</td>
      <td><span style="font-size:14px">${a.gender==='female'?'💁‍♀️':'🧔'}</span> ${a.gender==='female'?'Mujer':'Hombre'}</td>
      <td>${a.service}</td>
      <td>${a.staff}</td>
      <td>${fmtDate(a.date)}</td>
      <td>${a.time}</td>
      <td style="color:var(--text-muted);font-size:12px">${durFmt(a.duration_minutes)}</td>
      <td style="color:var(--gold)">${a.total}</td>
      <td><span class="sbadge ${a.status==='Pendiente'?'sb-pend':a.status==='Completado'?'sb-done':'sb-canc'}">${a.status}</span></td>
      <td>
        ${a.status==='Pendiente' && a.gender==='male' && isEligibleForFree && !isFreecut ?`<button class="del-row-btn" style="background:var(--green);margin-bottom:4px;font-size:11px" onclick="markFreeCut(${a.id})">🎁 Marcar Gratis</button>`:''}
        ${a.status==='Pendiente'?`<button class="del-row-btn" style="background:var(--red);margin-bottom:4px;width:100%" onclick="cancelAppt(${a.id})">❌ Cancelar</button>`:''}
        <button class="del-row-btn" style="width:100%" onclick="delAppt(${a.id})">🗑 Eliminar</button>
      </td>
    </tr>`;
  }).join('');
}

async function delAppt(id){
  if(!confirm('¿Eliminar esta cita permanentemente?')) return;
  // Eliminar visualmente de inmediato
  const row = document.querySelector(`button[onclick="delAppt(${id})"]`)?.closest('tr');
  if(row){ row.style.opacity='0.3'; row.style.pointerEvents='none'; }
  fetch(`/api/appointments/${id}`, {method:'DELETE'}).then(()=>{
    renderTable(); renderDash(); buildTimeGrid();
  });
  showToast('✅ Cita eliminada correctamente','ok');
}

async function markFreeCut(id){
  if(!confirm('¿Marcar esta cita como corte gratis?')) return;
  
  try {
    const res = await fetch(`/api/appointments/${id}/mark-free`, {method:'POST'});
    const data = await res.json();
    
    if(res.ok) {
      showToast('🎁 ¡Cita marcada como gratis!', 'ok');
      renderTable(); // Refrescar la tabla
    } else {
      showToast(`❌ Error: ${data.error}`, 'error');
    }
  } catch(e) {
    showToast('❌ No pudimos marcar la cita como gratis', 'error');
  }
}

async function cancelAppt(id){
  if(!confirm('¿Cancelar esta cita?')) return;
  const row = document.querySelector(`button[onclick="cancelAppt(${id})"]`)?.closest('tr');
  if(row){ row.style.opacity='0.5'; row.style.pointerEvents='none'; }
  
  const res = await fetch(`/api/appointments/${id}/status`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status: 'Cancelado'})
  });
  
  if(res.ok){
    showToast('✅ Cita cancelada correctamente','ok');
    renderTable(); renderDash(); buildTimeGrid();
  } else {
    showToast('❌ No pudimos cancelar la cita','error');
    if(row){ row.style.opacity='1'; row.style.pointerEvents='auto'; }
  }
}

// ══ EDIT ROWS ══════════════════════════════════════════════════
function buildEditRow(item, i, type){
  const isStaff = type==='brb'||type==='sty';
  const isFemale = type==='sty';
  const thClass = isStaff ? `edit-thumb circle ${isFemale?'pink-circle':''}` : 'edit-thumb';
  const thumbContent = item.image_url ? `<img src="${item.image_url}" alt="">` : (item.emoji||'?');
  return`<div class="edit-row">
    <div class="${thClass}" id="${type}Thumb-${i}">${thumbContent}</div>
    <div class="edit-field">
      <label class="edit-label">Nombre</label>
      <input class="ei" id="${type}N-${i}" value="${escQ(item.name)}" placeholder="Nombre">
    </div>
    ${isStaff?`
    <div class="edit-field">
      <label class="edit-label">Título</label>
      <input class="ei" id="${type}T-${i}" value="${escQ(item.title||'')}" placeholder="Ej. Master Barber">
    </div>
    <div class="edit-field" style="max-width:90px">
      <label class="edit-label">Experiencia</label>
      <input class="ei sm" id="${type}E-${i}" value="${escQ(item.experience||'')}" placeholder="Ej. 3 años">
    </div>
    <div class="edit-field" style="flex:1.5">
      <label class="edit-label">Especialidades</label>
      <input class="ei" id="${type}Sp-${i}" value="${escQ(item.specialties||'')}" placeholder="Ej. Fades, Barba">
    </div>
    <div class="edit-field" style="max-width:110px">
      <label class="edit-label">📞 WhatsApp</label>
      <input class="ei sm" id="${type}Ph-${i}" value="${escQ(item.phone||'')}" placeholder="573001234567">
    </div>
    <div class="edit-field" style="max-width:120px">
      <label class="edit-label">📸 Instagram</label>
      <input class="ei sm" id="${type}Ig-${i}" value="${escQ(item.instagram||'')}" placeholder="usuario o URL">
    </div>`:''}
    ${!isStaff?`
    <div class="edit-field" style="flex:2">
      <label class="edit-label">Descripción</label>
      <input class="ei" id="${type}D-${i}" value="${escQ(item.description||'')}" placeholder="Descripción del servicio">
    </div>
    <div class="edit-field" style="max-width:90px">
      <label class="edit-label">Precio $</label>
      <input class="ei sm" id="${type}P-${i}" value="${item.price||0}" placeholder="0">
    </div>
    <div class="edit-field" style="max-width:72px">
      <label class="edit-label">Duración</label>
      <input class="ei sm" id="${type}DUR-${i}" value="${item.duration_minutes||60}" placeholder="Min" title="Duración en minutos">
    </div>`:''}
    <div class="edit-field" style="max-width:62px">
      <label class="edit-label">Emoji</label>
      <input class="ei xs" id="${type}Em-${i}" value="${escQ(item.emoji||'')}" placeholder="😊" oninput="updThumb('${type}',${i})">
    </div>
    <input type="hidden" id="${type}IH-${i}" value="${escQ(item.image_url&&!item.image_url.startsWith('http')?item.image_url:'')}">
    <div class="img-mini">
      <label class="edit-label">URL imagen</label>
      <input class="ei xs" id="${type}IU-${i}" value="${escQ(item.image_url||'')}" placeholder="https://..." oninput="updThumb('${type}',${i})" style="max-width:120px">
      <label class="edit-label" style="margin-top:4px">o subir archivo</label>
      <input type="file" accept="image/*" onchange="loadImgFile('${type}',${i},this)">
    </div>
    <button class="delbtn" onclick="delItem('${type}',${i},${item.id})">🗑</button>
  </div>`;
}

function updThumb(type,i){
  const url=document.getElementById(`${type}IU-${i}`).value.trim();
  const emo=document.getElementById(`${type}Em-${i}`).value||'?';
  const d=document.getElementById(`${type}Thumb-${i}`);
  const buf=type==='brb'?brbImgBuf:type==='sty'?styImgBuf:type==='srvF'?srvFImgBuf:srvImgBuf;
  if(url){ d.innerHTML=`<img src="${url}" alt="">`; return; }
  if(buf[i]){ d.innerHTML=`<img src="${buf[i]}" alt="">`; return; }
  d.innerHTML=emo;
}

async function loadImgFile(type,i,inp){
  const f=inp.files[0]; if(!f) return;
  const buf=type==='brb'?brbImgBuf:type==='sty'?styImgBuf:type==='srvF'?srvFImgBuf:srvImgBuf;
  // Subir archivo al servidor y obtener URL
  const fd=new FormData(); fd.append('file',f);
  const res=await fetch('/api/upload-image',{method:'POST',body:fd});
  const data=await res.json();
  if(!data.success){ showToast('❌ No pudimos subir la imagen. Intenta de nuevo.','error'); return; }
  buf[i]=data.url;
  document.getElementById(`${type}Thumb-${i}`).innerHTML=`<img src="${data.url}" alt="">`;
  // Actualizar también el input URL para que getImgVal lo tome
  const urlInput=document.getElementById(`${type}IU-${i}`);
  if(urlInput) urlInput.value=data.url;
}

async function delItem(type,i,id){
  if(!confirm('¿Eliminar?')) return;
  // Eliminar del array local y re-renderizar inmediatamente
  if(type==='srv')   { services.splice(i,1);  renderSrvRows();  renderClientSrv(); }
  if(type==='srvF')  { servicesF.splice(i,1); renderSrvFRows(); renderClientSrv(); }
  if(type==='brb')   { barbers.splice(i,1);   renderBrbRows();  renderClientStaff(); renderFStaff(); renderDash(); }
  if(type==='sty')   { stylists.splice(i,1);  renderStyRows();  renderClientStaff(); renderFStaff(); renderDash(); }
  showToast('✅ Elemento eliminado correctamente','ok');
  // Sincronizar con servidor en background (solo si tiene id real)
  if(id){
    const endpoint = (type==='srv'||type==='srvF') ? `/api/services/${id}` : `/api/staff/${id}`;
    fetch(endpoint, {method:'DELETE'});
  }
}

function getImgVal(type,i,list){
  const urlVal=document.getElementById(`${type}IU-${i}`)?.value.trim()||'';
  const hidVal=document.getElementById(`${type}IH-${i}`)?.value||'';
  const buf=type==='brb'?brbImgBuf:type==='sty'?styImgBuf:type==='srvF'?srvFImgBuf:srvImgBuf;
  return urlVal||buf[i]||hidVal||list[i].image_url||null;
}

// ══ SERVICES HOMBRE ════════════════════════════════════════════
function renderSrvRows(){ srvImgBuf={}; document.getElementById('srvList').innerHTML=services.map((s,i)=>buildEditRow(s,i,'srv')).join(''); }
function addSrv(){ services.push({id:0,name:'Nuevo Servicio',description:'Descripción',price:20000,duration_minutes:60,emoji:'✂',image_url:null}); renderSrvRows(); }
async function saveSrv(){
  let totalUpdated=0;
  const promises = services.map(async (s, i) => {
    const dur=parseInt(document.getElementById(`srvDUR-${i}`)?.value)||s.duration_minutes||60;
    const priceVal = document.getElementById(`srvP-${i}`)?.value;
    const price = priceVal !== '' && priceVal !== null && priceVal !== undefined ? parseInt(priceVal) : s.price;
    const payload={name:document.getElementById(`srvN-${i}`).value||s.name,description:document.getElementById(`srvD-${i}`).value,price:price,emoji:document.getElementById(`srvEm-${i}`).value||s.emoji,image_url:getImgVal('srv',i,services),duration_minutes:dur,gender:'male'};
    const res = s.id
      ? await fetch(`/api/services/${s.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      : await fetch('/api/services',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await res.json(); if(d.appointments_updated) totalUpdated+=d.appointments_updated;
  });
  await Promise.all(promises);
  await loadServices('male'); srvImgBuf={}; renderClientSrv();
  showToast(totalUpdated?`✅ Guardado · ${totalUpdated} cita(s) actualizadas`:'✅ Servicios guardados correctamente','ok');
}

// ══ BARBEROS ═══════════════════════════════════════════════════
function renderBrbRows(){ brbImgBuf={}; document.getElementById('brbList').innerHTML=barbers.map((b,i)=>buildEditRow(b,i,'brb')).join(''); }
function addBrb(){ barbers.push({id:0,name:'Nuevo Barbero',title:'Barber',experience:'1 año',stars:4,emoji:'💈',image_url:null,specialties:'General'}); renderBrbRows(); }
async function saveBrb(){
  const promises = barbers.map(async (b, i) => {
    const payload={name:document.getElementById(`brbN-${i}`).value||b.name,title:document.getElementById(`brbT-${i}`).value||b.title,experience:document.getElementById(`brbE-${i}`).value||b.experience,specialties:document.getElementById(`brbSp-${i}`).value||b.specialties,emoji:document.getElementById(`brbEm-${i}`).value||b.emoji,image_url:getImgVal('brb',i,barbers),phone:document.getElementById(`brbPh-${i}`)?.value||b.phone||'',instagram:document.getElementById(`brbIg-${i}`)?.value||b.instagram||'',gender:'male'};
    if(b.id) return fetch(`/api/staff/${b.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    else return fetch('/api/staff',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  });
  await Promise.all(promises);
  await loadStaff('male'); brbImgBuf={}; renderClientStaff(); renderFStaff(); renderDash();
  const hs=document.getElementById('heroStaff'); if(hs) hs.textContent=(barbers.length+stylists.length)+'+'; showToast('✅ Barberos guardados correctamente','ok');
}

// ══ ESTILISTAS ═════════════════════════════════════════════════
function renderStyRows(){ styImgBuf={}; document.getElementById('styList').innerHTML=stylists.map((s,i)=>buildEditRow(s,i,'sty')).join(''); }
function addSty(){ stylists.push({id:0,name:'Nueva Estilista',title:'Stylist',experience:'1 año',stars:4,emoji:'💅',image_url:null,specialties:'General'}); renderStyRows(); }
async function saveSty(){
  const promises = stylists.map(async (s, i) => {
    const payload={name:document.getElementById(`styN-${i}`).value||s.name,title:document.getElementById(`styT-${i}`).value||s.title,experience:document.getElementById(`styE-${i}`).value||s.experience,specialties:document.getElementById(`stySp-${i}`).value||s.specialties,emoji:document.getElementById(`styEm-${i}`).value||s.emoji,image_url:getImgVal('sty',i,stylists),phone:document.getElementById(`styPh-${i}`)?.value||s.phone||'',instagram:document.getElementById(`styIg-${i}`)?.value||s.instagram||'',gender:'female'};
    if(s.id) return fetch(`/api/staff/${s.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    else return fetch('/api/staff',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  });
  await Promise.all(promises);
  await loadStaff('female'); styImgBuf={}; renderClientStaff(); renderFStaff(); renderDash();
  const hs=document.getElementById('heroStaff'); if(hs) hs.textContent=(barbers.length+stylists.length)+'+'; showToast('✅ Estilistas guardadas correctamente','ok');
}

// ══ SERVICIOS MUJER ════════════════════════════════════════════
function renderSrvFRows(){ srvFImgBuf={}; document.getElementById('srvFList').innerHTML=servicesF.map((s,i)=>buildEditRow(s,i,'srvF')).join(''); }
function addSrvF(){ servicesF.push({id:0,name:'Nuevo Servicio',description:'Descripción',price:20000,duration_minutes:60,emoji:'💅',image_url:null}); renderSrvFRows(); }
async function saveSrvF(){
  let totalUpdated=0;
  const promises = servicesF.map(async (s, i) => {
    const dur=parseInt(document.getElementById(`srvFDUR-${i}`)?.value)||s.duration_minutes||60;
    const priceVal = document.getElementById(`srvFP-${i}`)?.value;
    const price = priceVal !== '' && priceVal !== null && priceVal !== undefined ? parseInt(priceVal) : s.price;
    const payload={name:document.getElementById(`srvFN-${i}`).value||s.name,description:document.getElementById(`srvFD-${i}`).value,price:price,emoji:document.getElementById(`srvFEm-${i}`).value||s.emoji,image_url:getImgVal('srvF',i,servicesF),duration_minutes:dur,gender:'female'};
    const res = s.id
      ? await fetch(`/api/services/${s.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      : await fetch('/api/services',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await res.json(); if(d.appointments_updated) totalUpdated+=d.appointments_updated;
  });
  await Promise.all(promises);
  await loadServices('female'); srvFImgBuf={}; renderClientSrv();
  showToast(totalUpdated?`✅ Guardado · ${totalUpdated} cita(s) actualizadas`:'✅ Servicios guardados correctamente','ok');
}

async function reloadAll(){
  await Promise.all([loadServices('male'),loadServices('female'),loadStaff('male'),loadStaff('female')]);
  renderClientSrv(); renderClientStaff(); renderFStaff();
}

// ══ MARCA ══════════════════════════════════════════════════════
function renderMarca(){
  document.getElementById('shopNameInput').value=shopName;
  refreshLogoPrev();
  // Actualizar previews de iconos de género
  _refreshGenderPrev('male');
  _refreshGenderPrev('female');
  // Rellenar inputs URL si hay valor guardado
  if(genderIcons.male && genderIcons.male.startsWith('http'))
    document.getElementById('maleIconUrl').value = genderIcons.male;
  if(genderIcons.female && genderIcons.female.startsWith('http'))
    document.getElementById('femaleIconUrl').value = genderIcons.female;
}
function saveShopName(){ const v=document.getElementById('shopNameInput').value.trim().toUpperCase(); if(!v){showToast('📝 Por favor ingresa un nombre válido','error');return;} shopName=v; applyNameEverywhere(); _postConfig({shop_name:shopName}).then(ok=>{ if(ok) showToast('✅ Nombre actualizado correctamente','ok'); }); }
function applyNameEverywhere(){
  ['ribbonName','adminShopName','footerName'].forEach(id=>{ const el=document.getElementById(id); if(el) el.textContent=shopName; });
  document.title=shopName+' | Barbería & Estilismo';
  const w=shopName.split(' ');
  const heroOut=document.getElementById('heroOut'); const heroAcc=document.getElementById('heroAcc');
  if(heroOut) heroOut.textContent=w.length>1?w.slice(0,-1).join(' '):shopName;
  if(heroAcc) heroAcc.textContent=w.length>1?w[w.length-1]:'';
  const pn=document.getElementById('prevName'); if(pn) pn.textContent=shopName;
}
function switchLogoTab(t){
  document.querySelectorAll('.itab').forEach((b,i)=>b.classList.toggle('on',['url','file'][i]===t));
  document.getElementById('logo-url-panel').classList.toggle('on',t==='url');
  document.getElementById('logo-file-panel').classList.toggle('on',t==='file');
}
function applyLogoUrl(){ const url=document.getElementById('logoUrlInput').value.trim(); if(!url){showToast('🔗 Por favor ingresa una URL válida','error');return;} shopLogo=url; applyLogoEverywhere(); refreshLogoPrev(); _postConfig({shop_logo:shopLogo}).then(ok=>{ if(ok) showToast('✅ Logo actualizado correctamente','ok'); }); }
function applyLogoFile(inp){ const f=inp.files[0]; if(!f) return; const r=new FileReader(); r.onload=e=>{shopLogo=e.target.result;applyLogoEverywhere();refreshLogoPrev();_postConfig({shop_logo:shopLogo}).then(ok=>{ if(ok) showToast('✅ Logo cargado correctamente','ok'); });}; r.readAsDataURL(f); }
function removeLogo(){ shopLogo=null; applyLogoEverywhere(); refreshLogoPrev(); _postConfig({shop_logo:''}).then(ok=>{ if(ok) showToast('✅ Logo quitado correctamente', 'ok'); }); }

// ── Iconos de género ──────────────────────────────────────────
function switchGenderTab(gender, t){
  const prefix = gender;
  document.querySelectorAll(`#${prefix}-url-panel, #${prefix}-file-panel`).forEach(p=>p.classList.remove('on'));
  document.getElementById(`${prefix}-${t}-panel`).classList.add('on');
}

function _refreshGenderPrev(gender){
  const el = document.getElementById(`prev${gender==='male'?'Male':'Female'}Icon`);
  if(!el) return;
  const url = genderIcons[gender];
  el.innerHTML = url
    ? `<img src="${url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`
    : (gender==='male' ? '🧔' : '💁‍♀️');
}

function applyGenderIcons(){
  ['male','female'].forEach(g=>{
    const wrap = document.getElementById(g==='male'?'maleIconWrap':'femaleIconWrap');
    if(!wrap) return;
    if(genderIcons[g]){
      // Reemplazar contenido del wrapper con imagen
      wrap.innerHTML = `<img src="${genderIcons[g]}" style="width:100px;height:106px;object-fit:contain;filter:drop-shadow(0 8px 20px rgba(0,0,0,.3))">`;
    }
    // Si no hay imagen personalizada, el SVG original ya está en el HTML
  });
}

async function applyGenderIcon(gender){
  const inputId = gender==='male' ? 'maleIconUrl' : 'femaleIconUrl';
  const url = document.getElementById(inputId).value.trim();
  if(!url){ showToast('🔗 Por favor ingresa una URL válida', 'error'); return; }
  genderIcons[gender] = url;
  applyGenderIcons();
  _refreshGenderPrev(gender);
  const key = gender==='male' ? 'gender_icon_male' : 'gender_icon_female';
  _postConfig({[key]: url}).then(ok=>{ if(ok) showToast('✅ Imagen actualizada correctamente','ok'); });
}

async function applyGenderIconFile(gender, inp){
  const f = inp.files[0]; if(!f) return;
  const fd = new FormData(); fd.append('file', f);
  const res = await fetch('/api/upload-image',{method:'POST',body:fd});
  const data = await res.json();
  if(!data.success){ showToast('❌ No pudimos subir la imagen. Intenta de nuevo.', 'error'); return; }
  genderIcons[gender] = data.url;
  applyGenderIcons();
  _refreshGenderPrev(gender);
  const key = gender==='male' ? 'gender_icon_male' : 'gender_icon_female';
  _postConfig({[key]: data.url}).then(ok=>{ if(ok) showToast('✅ Imagen cargada correctamente','ok'); });
}

function removeGenderIcon(gender){
  genderIcons[gender] = null;
  // Restaurar SVG original
  const wrap = document.getElementById(gender==='male'?'maleIconWrap':'femaleIconWrap');
  if(wrap){
    // Recargar página para restaurar SVG original embebido
    const key = gender==='male' ? 'gender_icon_male' : 'gender_icon_female';
    _postConfig({[key]: ''}).then(ok=>{
      if(ok){ showToast('✅ Imagen quitada correctamente', 'ok'); location.reload(); }
    });
  }
}
function logoInner(size){ if(shopLogo) return`<img src="${shopLogo}" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%">`; return`<span style="font-size:${Math.round(size*.52)}px;line-height:1">💈</span>`; }
function applyLogoEverywhere(){
  const ids=[['ribbonLogoWrap',30],['adminLogoBox',50],['footerLogoBox',46]];
  ids.forEach(([id,sz])=>{ const el=document.getElementById(id); if(el) el.innerHTML=logoInner(sz); });
  const he=document.getElementById('heroLogoEl');
  if(he){ if(shopLogo){he.innerHTML=`<img src="${shopLogo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`;he.style.fontSize='';}else{he.innerHTML='💈';he.style.fontSize='105px';} }
}
function refreshLogoPrev(){ const el=document.getElementById('logoPrev'); if(el) el.innerHTML=logoInner(54); }

// ══ CONFIG ═════════════════════════════════════════════════════
function renderConfig(){
  document.getElementById('cfgUbicacion').value=cfg.ubicacion;
  document.getElementById('cfgTelefono').value=cfg.telefono;
  document.getElementById('cfgWa').value=cfg.wa;
  document.getElementById('cfgIg').value=cfg.ig;
  document.getElementById('cfgWaSty').value=cfg.wa_sty||'';
  document.getElementById('cfgIgSty').value=cfg.ig_sty||'';
  document.getElementById('cfgWaInstance').value=evoInstance;
  ['newUser','newPass','confPass'].forEach(id=>document.getElementById(id).value='');
  const m=document.getElementById('credMsg'); m.style.display='none';
}
// helper para guardar config con manejo de error
async function _postConfig(payload){
  const res = await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!res.ok){ showToast('🔐 Tu sesión expiró. Por favor inicia sesión de nuevo.','error'); return false; }
  return true;
}

function saveCfg(){
  cfg.ubicacion=document.getElementById('cfgUbicacion').value||cfg.ubicacion;
  cfg.telefono=document.getElementById('cfgTelefono').value||cfg.telefono;
  _postConfig({ubicacion:cfg.ubicacion,telefono:cfg.telefono})
    .then(ok=>{ if(ok){ applyConfig(); showToast('✅ Información guardada correctamente','ok'); } });
}
function saveSocialBrb(){
  cfg.wa = document.getElementById('cfgWa').value.trim().replace(/\s/g,'') || '';
  cfg.ig = (document.getElementById('cfgIg').value.trim().replace(/^@/,'')) || '';
  _postConfig({wa:cfg.wa, ig:cfg.ig})
    .then(ok=>{ if(ok) showToast('✅ Redes del barbero guardadas correctamente','ok'); });
}
function saveSocialSty(){
  cfg.wa_sty = document.getElementById('cfgWaSty').value.trim().replace(/\s/g,'') || '';
  cfg.ig_sty = (document.getElementById('cfgIgSty').value.trim().replace(/^@/,'')) || '';
  _postConfig({wa_sty:cfg.wa_sty, ig_sty:cfg.ig_sty})
    .then(ok=>{ if(ok) showToast('✅ Redes de la estilista guardadas correctamente','ok'); });
}
function saveWaConfig(){
  evoInstance = document.getElementById('cfgWaInstance').value.trim();
  _postConfig({evo_instance:evoInstance})
    .then(ok=>{ if(ok) showToast('✅ Nombre de instancia guardado','ok'); });
}

async function loadWaQr(){
  const btn = document.getElementById('btnShowQr');
  const container = document.getElementById('waQrContainer');
  const qrDiv = document.getElementById('waQrCode');
  const msgDiv = document.getElementById('waStatusMsg');

  btn.disabled = true;
  btn.textContent = '⌛ Cargando...';
  msgDiv.style.display = 'none';
  qrDiv.innerHTML = '';

  try {
    const res = await fetch('/api/whatsapp/qr');
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.message || `Error ${res.status}`);
    }
    
    const data = await res.json();

    // Si ya está conectado
    if(data.instance && data.instance.state === 'open'){
      msgDiv.textContent = '✅ WhatsApp ya está vinculado y activo.';
      msgDiv.style.color = 'var(--green)';
      msgDiv.style.display = 'block';
      container.style.display = 'none';
    } 
    // Si hay QR
    else if(data.base64){
      qrDiv.innerHTML = `<img src="${data.base64}" style="width:250px;height:250px;border:2px solid var(--gold);border-radius:8px;padding:10px;background:white">`;
      container.style.display = 'flex';
      msgDiv.textContent = '📱 Escanea el código QR con WhatsApp';
      msgDiv.style.color = 'var(--text-light)';
      msgDiv.style.display = 'block';
    } 
    // Si hay error
    else if(data.success === false){
      const err = data.message || 'No se pudo generar el QR';
      msgDiv.textContent = `❌ ${err}`;
      msgDiv.style.color = 'var(--red-bright)';
      msgDiv.style.display = 'block';
      container.style.display = 'none';
      showToast(`❌ ${err}`, 'error');
    }
    // Formato desconocido
    else {
      msgDiv.textContent = '❌ Respuesta inesperada del servidor';
      msgDiv.style.color = 'var(--red-bright)';
      msgDiv.style.display = 'block';
      container.style.display = 'none';
      console.error('Respuesta inesperada:', data);
    }
  } catch(e) {
    console.error('Error al cargar QR:', e);
    msgDiv.textContent = `❌ ${e.message || 'Error de conexión con el servidor de WhatsApp'}`;
    msgDiv.style.color = 'var(--red-bright)';
    msgDiv.style.display = 'block';
    container.style.display = 'none';
    showToast(`❌ ${e.message || 'Error de conexión'}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔗 Vincular WhatsApp (QR)';
  }
}
function applyConfig(){ const el=document.getElementById('footerInfo'); if(el) el.textContent=cfg.ubicacion+' | 📞 '+cfg.telefono; }
function openWa(e){
  const num = cfg.wa.replace(/\D/g,'');
  if(!num){ showToast('📱 WhatsApp aún no está configurado','neutral'); return false; }
  if(num.length < 7){ showToast('📱 El número de WhatsApp no es válido','error'); return false; }
  window.open('https://wa.me/'+num,'_blank');
  return false;
}
function openIg(e){
  if(!cfg.ig){ showToast('📸 Instagram aún no está configurado','neutral'); return false; }
  // Limpiar @ si lo tiene
  const ig = cfg.ig.replace(/^@/,'').trim();
  window.open(ig.startsWith('http') ? ig : 'https://instagram.com/'+ig, '_blank');
  return false;
}
function openWaSty(e){
  const num = (cfg.wa_sty||'').replace(/\D/g,'');
  if(!num){ showToast('📱 WhatsApp de la estilista aún no está configurado','neutral'); return false; }
  if(num.length < 7){ showToast('📱 El número de WhatsApp no es válido','error'); return false; }
  window.open('https://wa.me/'+num,'_blank');
  return false;
}
function openIgSty(e){
  if(!cfg.ig_sty){ showToast('📸 Instagram de la estilista aún no está configurado','neutral'); return false; }
  const ig = cfg.ig_sty.replace(/^@/,'').trim();
  window.open(ig.startsWith('http') ? ig : 'https://instagram.com/'+ig, '_blank');
  return false;
}
function saveCreds(){
  const u=document.getElementById('newUser').value.trim();
  const p=document.getElementById('newPass').value;
  const c=document.getElementById('confPass').value;
  const msg=document.getElementById('credMsg');
  const err=t=>{msg.style.cssText='display:block;background:rgba(192,57,43,0.12);color:var(--red-bright);border:1px solid rgba(192,57,43,0.3);padding:10px;border-radius:8px;font-size:13px;margin-bottom:10px';msg.textContent=t;};
  if(!u) return err('⚠ El usuario no puede estar vacío.');
  if(!p) return err('⚠ La contraseña no puede estar vacía.');
  if(p.length<4) return err('⚠ La contraseña debe tener al menos 4 caracteres.');
  if(p!==c) return err('⚠ Las contraseñas no coinciden.');
  fetch('/auth/update-credentials',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})})
    .then(r=>r.json()).then(data=>{
      if(data.success){
        msg.style.cssText='display:block;background:rgba(39,174,96,0.12);color:var(--green);border:1px solid rgba(39,174,96,0.3);padding:10px;border-radius:8px;font-size:13px;margin-bottom:10px';
        msg.textContent='✅ Credenciales actualizadas.';
        showToast('✅ Credenciales actualizadas','ok');
        ['newUser','newPass','confPass'].forEach(id=>document.getElementById(id).value='');
      } else {
        err('❌ '+(data.message||'Error al actualizar'));
      }
    });
}

// ══ RESET DATABASE ═════════════════════════════════════════════
async function resetDatabase(){
  const confirmed = confirm(
    '⚠️ REINICIAR DASHBOARD ⚠️\n\n' +
    'Esta acción eliminará:\n' +
    '• Citas COMPLETADAS y CANCELADAS\n' +
    '• Todas las reseñas\n' +
    '• Días inactivos pasados\n\n' +
    'Se MANTENDRÁN:\n' +
    '• Citas PENDIENTES\n' +
    '• Tarjetas de fidelidad\n\n' +
    'Esta acción NO se puede deshacer.\n\n' +
    '¿Estás seguro de que deseas continuar?'
  );
  
  if(!confirmed) return;
  
  // Segunda confirmación
  const doubleConfirm = confirm(
    '🚨 ÚLTIMA CONFIRMACIÓN 🚨\n\n' +
    'Vas a reiniciar el dashboard eliminando citas completadas/canceladas y reseñas.\n' +
    'Las citas pendientes y tarjetas de fidelidad se mantendrán.\n\n' +
    '¿Realmente deseas continuar?'
  );
  
  if(!doubleConfirm) return;
  
  try {
    showToast('🔄 Reiniciando dashboard...', 'neutral');
    
    const res = await fetch('/api/reset-appointments', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
    
    const data = await res.json();
    
    if(data.success){
      showToast('✅ Dashboard reiniciado correctamente', 'ok');
      
      // Mostrar detalles de lo eliminado
      const details = data.deleted;
      alert(
        '✅ Dashboard reiniciado exitosamente\n\n' +
        `📋 Citas completadas/canceladas eliminadas: ${details.completed_cancelled_appointments}\n` +
        `💳 Tarjetas de fidelidad conservadas: ${details.fidelity_cards_kept}\n` +
        `⭐ Reseñas eliminadas: ${details.reviews}\n` +
        `🚫 Días inactivos pasados eliminados: ${details.past_inactive_days}`
      );
      
      // Recargar el dashboard
      renderDash();
      renderTable();
    } else {
      showToast('❌ ' + (data.message || 'Error al reiniciar el dashboard'), 'error');
    }
  } catch(error) {
    console.error('Error al reiniciar dashboard:', error);
    showToast('❌ Error al reiniciar el dashboard', 'error');
  }
}

// ══ REVIEWS ════════════════════════════════════════════════════
let selRating = 0;

function pickStar(v){
  selRating = v;
  document.querySelectorAll('#starPicker .star').forEach((s,i)=>{
    s.classList.toggle('on', i < v);
  });
}

async function loadPublicReviews(){
  try{
    const res = await fetch('/api/reviews');
    const list = await res.json();
    renderPublicReviews(list);
  }catch(e){ console.warn('Reviews no disponibles', e); }
}

function renderPublicReviews(list){
  const grid = document.getElementById('reviewsGrid');
  if(!grid) return;
  
  // Filtrar solo 4 estrellas o más, ordenar por calificación (desc) y fecha (desc), limitar a 15
  const filtered = list.filter(r => r.rating >= 4)
    .sort((a,b) => {
      if(a.rating !== b.rating) return b.rating - a.rating; // Primero por calificación (5★, 4★)
      return new Date(b.created_at) - new Date(a.created_at); // Luego por fecha (más reciente primero)
    })
    .slice(0, 15);
  
  if(!filtered.length){
    grid.innerHTML='<p style="color:var(--text-muted);font-size:14px;text-align:center;grid-column:1/-1;font-family:var(--font-serif);font-style:italic">Sé el primero en dejar una reseña ⭐</p>';
    return;
  }
  grid.innerHTML = filtered.map(r=>`
    <div class="review-card ${r.rating === 5 ? 'review-excellent' : ''}">
      <div class="review-stars">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div>
      ${r.comment?`<p class="review-comment">"${r.comment}"</p>`:''}
      <div class="review-author">— ${r.client_name}</div>
      ${r.staff_name?`<div class="review-date">Atendido por ${r.staff_name} · ${r.created_at}</div>`:`<div class="review-date">${r.created_at}</div>`}
    </div>`).join('');
}

async function submitReview(){
  const name    = document.getElementById('rvName').value.trim();
  const comment = document.getElementById('rvComment').value.trim();
  if(!name){ showToast('📝 Por favor ingresa tu nombre', 'error'); return; }
  if(!selRating){ showToast('⭐ Por favor selecciona una calificación', 'error'); return; }
  const res = await fetch('/api/reviews',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({client_name:name, rating:selRating, comment})
  });
  const data = await res.json();
  if(!data.success){ showToast('❌ '+(data.message||'No pudimos enviar tu reseña'), 'error'); return; }
  showToast('✅ ¡Gracias por tu reseña!','ok');
  document.getElementById('rvName').value='';
  document.getElementById('rvComment').value='';
  selRating=0;
  document.querySelectorAll('#starPicker .star').forEach(s=>s.classList.remove('on'));
  await loadPublicReviews();
}

async function renderAdminReviews(){
  const res = await fetch('/api/reviews/all');
  const list = await res.json();
  const el = document.getElementById('adminReviewsList');
  if(!list.length){
    el.innerHTML='<p style="color:var(--text-muted);font-size:13px">No hay reseñas aún.</p>';
    return;
  }
  
  // Ordenar por calificación (desc) y luego por fecha (desc)
  const sortedList = list.sort((a,b) => {
    if(a.rating !== b.rating) return b.rating - a.rating; // Primero por calificación (5★, 4★)
    return new Date(b.created_at) - new Date(a.created_at); // Luego por fecha (más reciente primero)
  });
  
  el.innerHTML = sortedList.map(r=>`
    <div class="admin-review-card ${r.rating === 5 ? 'admin-review-excellent' : ''}">
      <div class="admin-review-info">
        <div class="admin-review-stars">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}
          <span class="admin-review-badge ${r.rating>=4?'badge-high':'badge-low'}">${r.rating>=4?'Pública':'Oculta'}</span>
          ${r.rating === 5 ? '<span class="admin-review-badge badge-excellent">Excelente</span>' : ''}
        </div>
        ${r.comment?`<div class="admin-review-comment">"${r.comment}"</div>`:'<div class="admin-review-comment" style="opacity:.4">Sin comentario</div>'}
        <div class="admin-review-meta">👤 ${r.client_name}${r.staff_name?' · '+r.staff_name:''} · ${r.created_at}</div>
      </div>
      <button class="delbtn" onclick="deleteReview(${r.id})">🗑</button>
    </div>`).join('');
}

async function deleteReview(id){
  if(!confirm('¿Eliminar esta reseña?')) return;
  // Eliminar visualmente de inmediato
  const card = document.querySelector(`button[onclick="deleteReview(${id})"]`)?.closest('.admin-review-card');
  if(card){ card.style.transition='all .2s'; card.style.opacity='0'; card.style.height='0'; card.style.overflow='hidden'; card.style.margin='0'; card.style.padding='0'; }
  fetch(`/api/reviews/${id}`,{method:'DELETE'}).then(()=>loadPublicReviews());
  showToast('Reseña eliminada','ok');
}

// ══ NAV DOTS ═══════════════════════════════════════════════════
function setupNavDots(){
  ['hero','genderSec','services','staff','booking','cancelSec'].forEach((id,idx)=>{
    const el=document.getElementById(id); if(!el) return;
    new IntersectionObserver(entries=>{
      if(entries[0].isIntersecting) document.querySelectorAll('.ndot').forEach((d,j)=>d.classList.toggle('on',j===idx));
    },{threshold:.4}).observe(el);
  });
}

// ══ START ══════════════════════════════════════════════════════
async function renderFidelityCards(){
  const res = await fetch('/api/appointments/fidelity/cards');
  const data = await res.json();
  const el = document.getElementById('fidelityCardsList');
  if(!data.cards.length){
    el.innerHTML='<p style="color:var(--text-muted);font-size:13px">No hay tarjetas de fidelidad registradas aún.</p>';
    return;
  }
  el.innerHTML=data.cards.map(c=>`
    <div style="background:var(--dark-card);border:1px solid ${c.count >= 10 ? 'var(--green)' : 'var(--dark-border)'};border-radius:12px;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;${c.count >= 10 ? 'box-shadow:0 0 10px rgba(46,204,113,0.3)' : ''}">
      <div>
        <div style="font-family:var(--font-serif);font-weight:700;font-size:15px;margin-bottom:4px">
          ${c.name}
          ${c.count >= 10 ? ' <span style="color:var(--green);font-size:12px;font-weight:700">⭐ LISTO PARA GRATIS</span>' : ''}
        </div>
        <div style="font-size:13px;color:var(--text-muted)">📞 ${c.phone} · 👤 ${c.staff}</div>
        <div style="font-size:13px;color:var(--gold);margin-top:3px">📅 Última visita: ${c.last_visit||'—'}</div>
        <div style="display:flex;gap:2px;flex-wrap:wrap;margin-top:6px">
          ${Array.from({length:10},(_,i)=>`<span style="font-size:14px">${i < c.count ? '✂️' : '⬜'}</span>`).join('')}
        </div>
      </div>
      <div style="text-align:right">
        <div style="font-size:28px;font-family:var(--font-display);color:${c.count >= 10 ? 'var(--green)' : 'var(--gold)'}">${c.count}/10</div>
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px">Cortes</div>
        <div style="font-size:12px;margin-top:4px;font-weight:${c.count >= 10 ? '700' : '400'};color:${c.count >= 10 ? 'var(--green)' : 'var(--text-muted)'}">
          ${c.count >= 10 ? '🎉 ¡CORTE GRATIS!' : `🎁 Faltan ${10-c.count}`}
        </div>
      </div>
    </div>`).join('');
}

// ══ INACTIVE DAYS ══════════════════════════════════════════════
let inactiveDays = [];

function renderInactiveStaffSelect(){
  const allStaff = [...barbers, ...stylists];
  const sel = document.getElementById('inactiveStaffSelect');
  sel.innerHTML = '<option value="">-- Elige un barbero o estilista --</option>' + 
    allStaff.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
}

function setupInactiveDateInput(){
  // Establecer fecha mínima (hoy) para los inputs de fecha
  const dateStart = document.getElementById('inactiveDateStart');
  const dateEnd = document.getElementById('inactiveDateEnd');
  
  if(dateStart || dateEnd){
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const minDate = `${year}-${month}-${day}`;
    
    if(dateStart) dateStart.min = minDate;
    if(dateEnd) dateEnd.min = minDate;
    
    // Cuando se selecciona fecha inicial, establecer como mínimo en fecha final
    if(dateStart) {
      dateStart.addEventListener('change', () => {
        if(dateEnd && dateStart.value) {
          dateEnd.min = dateStart.value;
          // Si la fecha final es menor que la inicial, limpiarla
          if(dateEnd.value && dateEnd.value < dateStart.value) {
            dateEnd.value = '';
          }
        }
      });
    }
  }
}

async function renderInactiveDaysList(){
  try {
    const res = await fetch('/api/inactive-days', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    inactiveDays = data;
    
    const el = document.getElementById('inactiveDaysList');
    if(!inactiveDays.length){
      el.innerHTML = '<div style="color:var(--text-muted);font-size:13px;text-align:center;padding:30px">No hay días marcados como inactivos.</div>';
      return;
    }
    
    // Agrupar por empleado
    const grouped = {};
    inactiveDays.forEach(d => {
      if(!grouped[d.staff_name]) grouped[d.staff_name] = [];
      grouped[d.staff_name].push(d);
    });
    
    el.innerHTML = Object.entries(grouped).map(([staffName, days]) => {
      const staff = [...barbers, ...stylists].find(s => s.name === staffName);
      const isFemale = staff?.gender === 'female';
      return `
        <div style="background:var(--dark-card);border-left:4px solid ${isFemale?'var(--pink)':'var(--gold)'};border-radius:8px;padding:14px 16px;overflow:hidden">
          <div style="font-weight:600;font-size:14px;margin-bottom:10px;display:flex;align-items:center;gap:8px">
            <span>${staff?.emoji || '👤'}</span>
            <span>${staffName}</span>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            ${days.map(d => `
              <div style="background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.3);border-radius:6px;padding:6px 10px;display:flex;align-items:center;gap:8px;font-size:12px">
                <span>📅 ${d.date}</span>
                ${d.reason ? `<span style="color:var(--text-muted)">(${d.reason})</span>` : ''}
                <button style="background:none;border:none;color:var(--red-bright);cursor:pointer;font-size:14px;padding:0 4px" onclick="deleteInactiveDay(${d.id})">✕</button>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');
  } catch(e) {
    console.error('Error al cargar días inactivos:', e);
    document.getElementById('inactiveDaysList').innerHTML = '<div style="color:var(--red-bright);font-size:13px">Error al cargar los datos.</div>';
  }
}

async function addInactiveDay(){
  const staffName = document.getElementById('inactiveStaffSelect').value?.trim();
  const dateStart = document.getElementById('inactiveDateStart').value?.trim();
  const dateEnd = document.getElementById('inactiveDateEnd').value?.trim();
  const reason = document.getElementById('inactiveReasonInput').value?.trim() || '';
  
  if(!staffName || !dateStart || !dateEnd){
    showToast('❌ Por favor selecciona un profesional y un rango de fechas', 'error');
    return;
  }
  
  // Validar que la fecha final sea >= a la inicial
  if(dateEnd < dateStart){
    showToast('❌ La fecha final debe ser igual o posterior a la fecha inicial', 'error');
    return;
  }
  
  try {
    // Generar array de fechas entre dateStart y dateEnd
    const dates = [];
    const current = new Date(dateStart + 'T00:00:00');
    const end = new Date(dateEnd + 'T00:00:00');
    
    while(current <= end){
      const year = current.getFullYear();
      const month = String(current.getMonth() + 1).padStart(2, '0');
      const day = String(current.getDate()).padStart(2, '0');
      dates.push(`${year}-${month}-${day}`);
      current.setDate(current.getDate() + 1);
    }
    
    console.log(`📅 Marcando ${dates.length} fecha(s) como inactivas para ${staffName}`);
    
    // Enviar cada fecha al servidor
    let successCount = 0;
    let errorCount = 0;
    
    for(const date of dates){
      try {
        const res = await fetch('/api/inactive-days', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ staff_name: staffName, date: date, reason: reason })
        });
        
        const data = await res.json();
        if(data.success){
          successCount++;
        } else {
          errorCount++;
        }
      } catch(e) {
        errorCount++;
      }
    }
    
    const msgEl = document.getElementById('inactiveMsg');
    
    if(successCount > 0){
      msgEl.style.display = 'block';
      msgEl.style.background = 'rgba(76, 175, 80, 0.15)';
      msgEl.style.color = 'var(--green)';
      msgEl.style.borderLeft = '4px solid var(--green)';
      msgEl.innerHTML = `✅ ${successCount} fecha(s) marcada(s) como inactiva(s)${errorCount > 0 ? ` (${errorCount} ya existían)` : ''}`;
      
      // Limpiar formulario
      document.getElementById('inactiveStaffSelect').value = '';
      document.getElementById('inactiveDateStart').value = '';
      document.getElementById('inactiveDateEnd').value = '';
      document.getElementById('inactiveReasonInput').value = '';
      
      // Recargar lista
      await renderInactiveDaysList();
      
      setTimeout(() => { msgEl.style.display = 'none'; }, 4000);
    } else {
      msgEl.style.display = 'block';
      msgEl.style.background = 'rgba(244, 67, 54, 0.15)';
      msgEl.style.color = 'var(--red-bright)';
      msgEl.style.borderLeft = '4px solid var(--red-bright)';
      msgEl.innerHTML = `❌ No se pudieron marcar las fechas (todas pueden ya existir)`;
    }
  } catch(e) {
    console.error('Error al agregar días inactivos:', e);
    showToast('❌ No pudimos procesar la solicitud', 'error');
  }
}

async function deleteInactiveDay(id){
  if(!confirm('¿Quitar este día inactivo?')) return;
  
  try {
    const res = await fetch(`/api/inactive-days/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await res.json();
    if(data.success){
      showToast(`✅ ${data.message}`, 'ok');
      await renderInactiveDaysList();
    }
  } catch(e) {
    console.error('Error al eliminar día inactivo:', e);
    showToast('❌ No pudimos eliminar el día', 'error');
  }
}

init();

// ══ PWA INSTALL ════════════════════════════════════════════════
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const installBtn = document.getElementById('installBtn');
  if (installBtn) installBtn.style.display = 'inline-block';
});

function installPWA() {
  if (!deferredPrompt) {
    showToast('📱 La app ya está instalada o no está disponible', 'neutral');
    return;
  }
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      showToast('✅ App instalada correctamente', 'ok');
      const ib = document.getElementById('installBtn');
      if (ib) ib.style.display = 'none';
    }
    deferredPrompt = null;
  });
}

// ══ DOWNLOAD BY OS ════════════════════════════════════════════
// Check if downloads are available on page load
async function checkDownloadAvailability() {
  try {
    const res = await fetch('/api/download-available');
    if (res.ok) {
      const data = await res.json();
      if (!data.android && !data.pc) {
        // Hide download button if no files available
        document.querySelectorAll('.btn-out').forEach(btn => {
          if (btn.textContent.includes('Descargar App')) {
            btn.style.display = 'none';
          }
        });
      }
    }
  } catch (e) {
    // Silently fail - button will still show but download may fail
  }
}

function downloadApp() {
  if (deferredPrompt) {
    installPWA();
    return;
  }

  const ua = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(ua);

  if (isIOS) {
    // En iPhone el toast queda al fondo, lejos del botón. Mostramos un banner contextual.
    showIosBanner();
  } else if (/android/.test(ua)) {
    showToast('📱 Android: Toca el menú de Chrome y selecciona "Añadir a la pantalla de inicio" o "Instalar aplicación"', 'neutral');
  } else {
    showToast('💻 En tu navegador de PC (Chrome/Edge), busca el icono de instalar app en la barra de direcciones', 'neutral');
  }
}

function showIosBanner() {
  // Eliminar banner previo si existe
  const prev = document.getElementById('iosBanner');
  if (prev) { prev.remove(); }

  // Buscar el botón de descargar para anclarse junto a él
  let anchorEl = null;
  document.querySelectorAll('.btn-out').forEach(btn => {
    if (btn.textContent.includes('Descargar')) anchorEl = btn;
  });

  const banner = document.createElement('div');
  banner.id = 'iosBanner';
  banner.innerHTML = `
    <span style="font-size:20px">🍎</span>
    <div style="flex:1;text-align:left">
      <div style="font-weight:700;font-size:13px;margin-bottom:3px">Instalar en iPhone</div>
      <div style="font-size:12px;opacity:.85">En Safari toca <strong>Compartir</strong> → <strong>"Añadir a pantalla de inicio"</strong></div>
    </div>
    <button onclick="document.getElementById('iosBanner').remove()" style="background:none;border:none;color:#fff;font-size:18px;cursor:pointer;padding:0;line-height:1;opacity:.7">✕</button>
  `;
  Object.assign(banner.style, {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: 'linear-gradient(135deg,#1a1400,#2a2000)',
    border: '2px solid var(--gold)',
    borderRadius: '14px',
    padding: '14px 16px',
    color: '#fff',
    boxShadow: '0 8px 32px rgba(212,175,55,0.35)',
    zIndex: '99999',
    maxWidth: '360px',
    width: 'calc(100% - 40px)',
    animation: 'iosBannerIn .35s cubic-bezier(.34,1.56,.64,1)'
  });

  // Agregar animación keyframes si no existe
  if (!document.getElementById('iosBannerStyle')) {
    const style = document.createElement('style');
    style.id = 'iosBannerStyle';
    style.textContent = '@keyframes iosBannerIn{from{opacity:0;transform:translateY(-12px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}';
    document.head.appendChild(style);
  }

  if (anchorEl) {
    // Insertar inmediatamente debajo del botón, dentro del mismo contenedor
    banner.style.position = 'relative';
    banner.style.marginTop = '10px';
    anchorEl.parentNode.insertBefore(banner, anchorEl.nextSibling);
  } else {
    // Fallback: banner fijo en la parte superior
    banner.style.position = 'fixed';
    banner.style.top = '72px';
    banner.style.left = '50%';
    banner.style.transform = 'translateX(-50%)';
    document.body.appendChild(banner);
  }

  // Auto-cerrar después de 7 segundos
  setTimeout(() => { if (banner.parentNode) banner.remove(); }, 7000);
}


// ══ AUTO-REFRESH DASHBOARD ═════════════════════════════════════
let dashboardRefreshInterval = null;

function startDashboardAutoRefresh() {
  // Actualizar dashboard cada 30 segundos si está en vista admin
  dashboardRefreshInterval = setInterval(() => {
    const adminView = document.getElementById('adminView');
    const dashTab = document.getElementById('tab-dash');
    
    // Solo actualizar si está visible el admin y la pestaña de dashboard
    if(adminView && adminView.style.display === 'block' && dashTab && dashTab.classList.contains('on')) {
      console.log('🔄 Actualizando dashboard...');
      renderDash();
    }
  }, 30000); // 30 segundos
}

function stopDashboardAutoRefresh() {
  if(dashboardRefreshInterval) {
    clearInterval(dashboardRefreshInterval);
    dashboardRefreshInterval = null;
  }
}

// Iniciar auto-refresh cuando se entra a admin
const originalSwitchView = switchView;
switchView = function(v) {
  originalSwitchView(v);
  if(v === 'admin') {
    startDashboardAutoRefresh();
  } else {
    stopDashboardAutoRefresh();
  }
};

