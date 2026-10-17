import React from 'react';

interface ZonePolygonSchematicProps {
  vertices: Array<[number, number]>;
  zoneName: string;
  zoneId: string;
}

export const ZonePolygonSchematic: React.FC<ZonePolygonSchematicProps> = ({
  vertices,
  zoneName,
  zoneId,
}) => {
  // SVG Canvas dimensions
  const width = 300;
  const height = 180;
  const padding = 20;

  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  // Scale normalized [0, 1] coords to SVG canvas
  const pointsString = vertices
    .map(([x, y]) => `${(padding + x * innerW).toFixed(1)},${(padding + y * innerH).toFixed(1)}`)
    .join(' ');

  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-primary)',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: 'var(--radius-sm)',
        padding: '10px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: '6px',
          left: '8px',
          fontSize: '9px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-text-dim)',
        }}
      >
        NORMALIZED [0.0, 1.0] BOUNDARY CANVAS • {zoneId}
      </div>

      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ overflow: 'visible', maxWidth: '100%', height: 'auto' }}
        aria-label={`Polygon boundary schematic for ${zoneName}`}
      >
        {/* Coordinate Grid Lines */}
        <line x1={padding} y1={padding} x2={padding + innerW} y2={padding} stroke="rgba(255,255,255,0.06)" strokeDasharray="2,2" />
        <line x1={padding} y1={padding + innerH} x2={padding + innerW} y2={padding + innerH} stroke="rgba(255,255,255,0.06)" strokeDasharray="2,2" />
        <line x1={padding} y1={padding} x2={padding} y2={padding + innerH} stroke="rgba(255,255,255,0.06)" strokeDasharray="2,2" />
        <line x1={padding + innerW} y1={padding} x2={padding + innerW} y2={padding + innerH} stroke="rgba(255,255,255,0.06)" strokeDasharray="2,2" />

        {/* Outer Frame Box */}
        <rect
          x={padding}
          y={padding}
          width={innerW}
          height={innerH}
          fill="none"
          stroke="var(--color-border-subtle)"
          strokeWidth="1"
        />

        {/* Calibrated Polygon Area */}
        <polygon
          points={pointsString}
          fill="rgba(239, 68, 68, 0.15)"
          stroke="var(--color-critical)"
          strokeWidth="2"
          strokeLinejoin="round"
        />

        {/* Vertices Pins with (x, y) tooltips */}
        {vertices.map(([x, y], idx) => {
          const cx = padding + x * innerW;
          const cy = padding + y * innerH;
          return (
            <g key={idx}>
              <circle
                cx={cx}
                cy={cy}
                r="4"
                fill="var(--color-critical)"
                stroke="#fff"
                strokeWidth="1"
              />
              <text
                x={cx + (x > 0.5 ? -6 : 6)}
                y={cy + (y > 0.5 ? -6 : 12)}
                fill="var(--color-text-dim)"
                fontSize="8"
                fontFamily="var(--font-mono)"
                textAnchor={x > 0.5 ? 'end' : 'start'}
              >
                P{idx + 1}({x.toFixed(2)}, {y.toFixed(2)})
              </text>
            </g>
          );
        })}
      </svg>

      <div
        style={{
          marginTop: '6px',
          fontSize: '10px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-text-dim)',
          display: 'flex',
          justifyContent: 'space-between',
          width: '100%',
        }}
      >
        <span>Evaluation: Ray-Casting Algorithm</span>
        <span>Anchor: bottom_center</span>
      </div>
    </div>
  );
};
