"use client";

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
  color: string;
}

export default function AnimatedParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particle colors - TINY 1mm glowing blue dust specks
    const colors = [
      'rgba(56, 189, 248, 1)',     // sky-400 - bright
      'rgba(59, 130, 246, 1)',     // blue-500 - bright
      'rgba(34, 211, 238, 1)',     // cyan-400 - bright
    ];

    // Create MANY tiny specks (smaller than 1mm)
    const particleCount = Math.min(1000, Math.floor((canvas.width * canvas.height) / 1500));
    particlesRef.current = [];

    for (let i = 0; i < particleCount; i++) {
      particlesRef.current.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.04,
        vy: (Math.random() - 0.5) * 0.04,
        radius: Math.random() * 0.6 + 1.2, // SMALLER specks (1.2-1.8px)
        opacity: Math.random() * 0.3 + 0.6, // Visible but subtle
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    // Animation loop
    const animate = () => {
      // Clear canvas with transparent background (so it shows on top of content)
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((particle, i) => {
        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Wrap around edges
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        // Draw TINY 1mm glowing speck
        ctx.save();
        const time = Date.now() * 0.002;
        const pulse = Math.sin(time + particle.x * 0.01 + particle.y * 0.01) * 0.1 + 1;
        const finalRadius = particle.radius * pulse;
        
        // Small subtle glow around the tiny speck
        const glowRadius = finalRadius * 3;
        const glow = ctx.createRadialGradient(
          particle.x,
          particle.y,
          0,
          particle.x,
          particle.y,
          glowRadius
        );
        
        // Extract RGBA values from color string
        const colorMatch = particle.color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
        if (colorMatch) {
          const r = colorMatch[1];
          const g = colorMatch[2];
          const b = colorMatch[3];
          
          // Subtle but visible glow
          glow.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.8)`);
          glow.addColorStop(0.4, `rgba(${r}, ${g}, ${b}, 0.5)`);
          glow.addColorStop(0.7, `rgba(${r}, ${g}, ${b}, 0.2)`);
          glow.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
        }
        
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, glowRadius, 0, Math.PI * 2);
        ctx.fill();

        // Small bright core speck
        ctx.shadowBlur = 8;
        ctx.shadowColor = particle.color;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.opacity;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, finalRadius, 0, Math.PI * 2);
        ctx.fill();
        
        // Tiny bright white center
        ctx.shadowBlur = 4;
        ctx.globalAlpha = 0.9;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, finalRadius * 0.4, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0"
      style={{ 
        background: 'transparent',
        width: '100vw',
        height: '100vh',
        zIndex: 1
      }}
    />
  );
}

