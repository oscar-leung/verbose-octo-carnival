import { useEffect, useRef } from 'react';

/**
 * Original animated backdrop: the once-in-fifty-years meteor shower over a
 * silhouetted capital — drawn from scratch, no anime frames. Static when the
 * viewer prefers reduced motion.
 */
export default function NightSky({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0;
    let H = 0;
    let stars: { x: number; y: number; r: number; p: number; s: number }[] = [];
    const meteors: { x: number; y: number; vx: number; vy: number; life: number }[] = [];
    let raf = 0;
    let t = 0;
    let lastMeteor = 0;
    let alive = true;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      stars = [];
      for (let i = 0; i < 150; i++) {
        stars.push({
          x: Math.random() * W,
          y: Math.random() * H * 0.75,
          r: Math.random() * 1.3 + 0.3,
          p: Math.random() * Math.PI * 2,
          s: 0.6 + Math.random() * 1.8,
        });
      }
    };

    const skyline = () => {
      ctx.fillStyle = '#0a0c12';
      const base = H * 0.88;
      ctx.beginPath();
      ctx.moveTo(0, H);
      ctx.lineTo(0, base + 6);
      let x = 0;
      const blocks = [0.07, 0.05, 0.1, 0.06, 0.12, 0.05, 0.09, 0.06, 0.1, 0.07, 0.08, 0.15];
      for (let i = 0; i < blocks.length; i++) {
        const w = W * (blocks[i] ?? 0.08);
        const rise = (i % 3 === 1 ? 0.08 : i % 4 === 2 ? 0.13 : 0.04) * H;
        ctx.lineTo(x, base - rise);
        if (i % 4 === 2) {
          ctx.lineTo(x + w * 0.4, base - rise - H * 0.08);
          ctx.lineTo(x + w * 0.5, base - rise - H * 0.13);
          ctx.lineTo(x + w * 0.6, base - rise - H * 0.08);
        }
        if (i === 7) ctx.arc(x + w / 2, base - rise, w / 2, Math.PI, 0);
        ctx.lineTo(x + w, base - rise);
        x += w;
      }
      ctx.lineTo(W, base + 6);
      ctx.lineTo(W, H);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = 'rgba(255, 196, 120, 0.5)';
      for (let j = 0; j < 30; j++) {
        const wx = (j * 137.5) % W;
        const wy = base - ((j * 53) % (H * 0.07)) - 3;
        ctx.fillRect(wx, wy, 2.2, 3.2);
      }
    };

    const frame = (now: number) => {
      if (!alive) return;
      t += 1 / 60;
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, '#0b1226');
      g.addColorStop(0.55, '#131b30');
      g.addColorStop(1, '#1d1a26');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
      for (const s of stars) {
        const a = 0.35 + 0.6 * Math.abs(Math.sin(s.p + t * s.s));
        ctx.fillStyle = `rgba(222, 234, 255, ${a.toFixed(2)})`;
        ctx.fillRect(s.x, s.y, s.r, s.r);
      }
      if (!reduced && now - lastMeteor > 1500 + Math.random() * 2400) {
        meteors.push({
          x: W * (0.15 + Math.random() * 0.8),
          y: H * 0.05 + Math.random() * H * 0.25,
          vx: -(2.4 + Math.random() * 2.4),
          vy: 1.4 + Math.random() * 1.2,
          life: 1,
        });
        lastMeteor = now;
      }
      for (let m = meteors.length - 1; m >= 0; m--) {
        const mt = meteors[m];
        if (!mt) continue;
        mt.x += mt.vx;
        mt.y += mt.vy;
        mt.life -= 0.016;
        if (mt.life <= 0) {
          meteors.splice(m, 1);
          continue;
        }
        const grad = ctx.createLinearGradient(mt.x, mt.y, mt.x - mt.vx * 12, mt.y - mt.vy * 12);
        grad.addColorStop(0, `rgba(210, 236, 255, ${(0.9 * mt.life).toFixed(2)})`);
        grad.addColorStop(1, 'rgba(126, 203, 255, 0)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(mt.x, mt.y);
        ctx.lineTo(mt.x - mt.vx * 12, mt.y - mt.vy * 12);
        ctx.stroke();
      }
      skyline();
      if (!reduced) raf = requestAnimationFrame(frame);
    };

    resize();
    const onResize = () => {
      resize();
      if (reduced) frame(0);
    };
    window.addEventListener('resize', onResize);
    if (reduced) frame(0);
    else raf = requestAnimationFrame(frame);

    return () => {
      alive = false;
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />;
}
