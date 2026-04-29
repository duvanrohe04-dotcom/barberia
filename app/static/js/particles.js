(function(){
  const canvas = document.getElementById('particleCanvas');
  const ctx    = canvas.getContext('2d');
  let W, H, mouse = {x: -999, y: -999};
  let particles = [];
  let isDark = true;

  function resize(){
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function getTheme(){
    return document.documentElement.getAttribute('data-theme') !== 'light';
  }

  // ── Particle class ──────────────────────────────────────────
  function Particle(){
    this.reset();
  }
  Particle.prototype.reset = function(){
    this.x  = Math.random() * W;
    this.y  = Math.random() * H;
    this.vx = (Math.random() - 0.5) * 0.6;
    this.vy = (Math.random() - 0.5) * 0.6;
    this.size = Math.random() * 1.8 + 0.4;
    this.alpha = isDark ? Math.random() * 0.5 + 0.15 : Math.random() * 0.7 + 0.35;
    this.life  = 1;
    // Color según tema
    if(isDark){
      // Dorado / ámbar
      const hue = 38 + Math.random() * 20;
      this.color = `hsl(${hue},90%,${55 + Math.random()*20}%)`;
    } else {
      // Pastel más saturado y visible
      const hues = [340,280,200,160,40,0,60];
      const hue  = hues[Math.floor(Math.random()*hues.length)];
      this.color = `hsl(${hue},75%,${50 + Math.random()*15}%)`;
    }
  };
  Particle.prototype.update = function(){
    // Atracción suave al cursor
    const dx = mouse.x - this.x;
    const dy = mouse.y - this.y;
    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
    if(dist < 180){
      const force = (180 - dist) / 180 * 0.018;
      this.vx += dx / dist * force;
      this.vy += dy / dist * force;
    }
    // Velocidad máxima
    const speed = Math.sqrt(this.vx*this.vx + this.vy*this.vy);
    if(speed > 2.2){ this.vx = this.vx/speed*2.2; this.vy = this.vy/speed*2.2; }
    this.x += this.vx;
    this.y += this.vy;
    // Rebote en bordes
    if(this.x < 0 || this.x > W) this.vx *= -1;
    if(this.y < 0 || this.y > H) this.vy *= -1;
    this.x = Math.max(0, Math.min(W, this.x));
    this.y = Math.max(0, Math.min(H, this.y));
  };
  Particle.prototype.draw = function(){
    ctx.save();
    ctx.globalAlpha = this.alpha;
    ctx.fillStyle   = this.color;
    ctx.shadowColor = this.color;
    ctx.shadowBlur  = isDark ? 8 : 12;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI*2);
    ctx.fill();
    ctx.restore();
  };

  // ── Ray / line between close particles ─────────────────────
  function drawConnections(){
    const maxDist = isDark ? 110 : 90;
    for(let i=0; i<particles.length; i++){
      for(let j=i+1; j<particles.length; j++){
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx*dx + dy*dy);
        if(d < maxDist){
          const alpha = (1 - d/maxDist) * (isDark ? 0.22 : 0.45);
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.strokeStyle = isDark ? '#D4AF37' : particles[i].color;
          ctx.lineWidth   = isDark ? 0.8 : 0.5;
          ctx.shadowColor = isDark ? '#D4AF37' : particles[i].color;
          ctx.shadowBlur  = isDark ? 6 : 8;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
          ctx.restore();
        }
      }
    }
  }

  // ── Init particles ──────────────────────────────────────────
  function initParticles(){
    const count = Math.min(Math.floor(W * H / 14000), 90);
    particles = [];
    for(let i=0; i<count; i++) particles.push(new Particle());
  }

  // ── Main loop ───────────────────────────────────────────────
  function loop(){
    ctx.clearRect(0, 0, W, H);
    const newDark = getTheme();
    if(newDark !== isDark){
      isDark = newDark;
      particles.forEach(p => p.reset());
    }
    drawConnections();
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(loop);
  }

  // ── Events ──────────────────────────────────────────────────
  window.addEventListener('resize', () => { resize(); initParticles(); });
  window.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
  window.addEventListener('touchmove', e => {
    if(e.touches[0]){ mouse.x = e.touches[0].clientX; mouse.y = e.touches[0].clientY; }
  }, {passive:true});
  window.addEventListener('mouseleave', () => { mouse.x = -999; mouse.y = -999; });

  // ── Start ───────────────────────────────────────────────────
  resize();
  initParticles();
  loop();
})();
