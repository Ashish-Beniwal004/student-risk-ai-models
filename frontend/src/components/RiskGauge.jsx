import { useEffect, useRef } from 'react';

const SIZE = 200;
const STROKE = 16;
const R = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = Math.PI * R; // semicircle

function polarToXY(angleDeg, r) {
  const rad = (angleDeg - 180) * (Math.PI / 180);
  const cx = SIZE / 2;
  const cy = SIZE / 2;
  return {
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad),
  };
}

export default function RiskGauge({ score = 0, riskLevel = 'LOW', animated = true }) {
  const needleRef = useRef(null);
  const arcRef = useRef(null);

  // score 0-100 → angle 0-180 (left to right)
  const clampedScore = Math.max(0, Math.min(100, score));
  const angleDeg = (clampedScore / 100) * 180; // 0 → left, 180 → right

  const COLORS = {
    HIGH: '#ef4444',
    MEDIUM: '#f59e0b',
    LOW: '#10b981',
  };
  const color = COLORS[riskLevel] || '#6366f1';

  // Arc fill ratio
  const arcRatio = clampedScore / 100;
  const arcLength = arcRatio * CIRCUMFERENCE;

  useEffect(() => {
    if (!animated) return;

    // Animate needle from 0 to target
    const start = performance.now();
    const duration = 1200;
    const targetAngle = angleDeg;

    function frame(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      const currentAngle = eased * targetAngle;

      if (needleRef.current) {
        needleRef.current.setAttribute('transform',
          `rotate(${currentAngle}, ${SIZE / 2}, ${SIZE / 2})`
        );
      }
      if (arcRef.current) {
        const currentLength = (currentAngle / 180) * CIRCUMFERENCE;
        arcRef.current.style.strokeDasharray = `${currentLength} ${CIRCUMFERENCE}`;
      }
      if (progress < 1) requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }, [score, animated, angleDeg]);

  // Needle tip position
  const needleTip = polarToXY(0, R - 4); // will be rotated via transform
  const needleBase1 = { x: SIZE / 2 - 3, y: SIZE / 2 + 4 };
  const needleBase2 = { x: SIZE / 2 + 3, y: SIZE / 2 + 4 };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '12px',
    }}>
      <div style={{ position: 'relative', width: SIZE, height: SIZE / 2 + 20 }}>
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          style={{ overflow: 'visible', display: 'block' }}
        >
          {/* Gauge track (grey arc) */}
          <path
            d={`M ${STROKE / 2} ${SIZE / 2} A ${R} ${R} 0 0 1 ${SIZE - STROKE / 2} ${SIZE / 2}`}
            fill="none"
            stroke="rgba(99, 102, 241, 0.12)"
            strokeWidth={STROKE}
            strokeLinecap="round"
          />

          {/* Color segments guide lines */}
          {[33, 66].map(pct => {
            const angle = (pct / 100) * 180;
            const outer = polarToXY(angle - 180, R + STROKE);
            const inner = polarToXY(angle - 180, R - STROKE * 0.5);
            return (
              <line
                key={pct}
                x1={SIZE/2 + (outer.x - SIZE/2)}
                y1={SIZE/2 + (outer.y - SIZE/2)}
                x2={SIZE/2 + (inner.x - SIZE/2)}
                y2={SIZE/2 + (inner.y - SIZE/2)}
                stroke="rgba(11,15,25,0.8)"
                strokeWidth={2}
              />
            );
          })}

          {/* Filled progress arc */}
          <path
            ref={arcRef}
            d={`M ${STROKE / 2} ${SIZE / 2} A ${R} ${R} 0 0 1 ${SIZE - STROKE / 2} ${SIZE / 2}`}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            style={{
              strokeDasharray: animated ? `0 ${CIRCUMFERENCE}` : `${arcLength} ${CIRCUMFERENCE}`,
              filter: `drop-shadow(0 0 8px ${color}80)`,
              transition: animated ? 'none' : 'stroke-dasharray 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />

          {/* Zone labels */}
          <text x="12" y={SIZE / 2 + 16} fontSize="9" fill="#10b981" fontWeight="600" fontFamily="Inter,sans-serif">LOW</text>
          <text x={SIZE / 2 - 12} y="22" fontSize="9" fill="#f59e0b" fontWeight="600" fontFamily="Inter,sans-serif">MED</text>
          <text x={SIZE - 38} y={SIZE / 2 + 16} fontSize="9" fill="#ef4444" fontWeight="600" fontFamily="Inter,sans-serif">HIGH</text>

          {/* Center dot */}
          <circle cx={SIZE / 2} cy={SIZE / 2} r={5} fill={color} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />

          {/* Needle */}
          <polygon
            ref={needleRef}
            points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
            fill={color}
            style={{
              filter: `drop-shadow(0 2px 4px rgba(0,0,0,0.6))`,
              transform: animated ? `rotate(0deg)` : `rotate(${angleDeg}deg)`,
              transformOrigin: `${SIZE / 2}px ${SIZE / 2}px`,
              transition: animated ? 'none' : 'transform 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
        </svg>
      </div>

      {/* Score display */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: '48px',
          fontWeight: '900',
          fontFamily: 'Space Grotesk, sans-serif',
          color: color,
          lineHeight: 1,
          textShadow: `0 0 30px ${color}60`,
        }}>
          {clampedScore.toFixed(1)}
        </div>
        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>Risk Score / 100</div>
        <div style={{
          marginTop: '10px',
          padding: '5px 20px',
          borderRadius: '20px',
          background: `rgba(${
            riskLevel === 'HIGH' ? '239,68,68' :
            riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
          }, 0.12)`,
          border: `1px solid ${color}50`,
          display: 'inline-block',
          fontSize: '13px',
          fontWeight: '700',
          color: color,
          letterSpacing: '0.1em',
        }}>
          {riskLevel} RISK
        </div>
      </div>
    </div>
  );
}
