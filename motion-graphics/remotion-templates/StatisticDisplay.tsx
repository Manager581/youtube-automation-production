/**
 * Statistic Display Template
 * Shows animated number counting up with label
 *
 * Usage in Remotion:
 * <StatisticDisplay number={1500000} label="Views" unit="+" duration={60} />
 */

import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface StatisticDisplayProps {
  number: number;
  label: string;
  unit?: string;
  duration?: number; // frames
  backgroundColor?: string;
  textColor?: string;
}

export const StatisticDisplay: React.FC<StatisticDisplayProps> = ({
  number,
  label,
  unit = '',
  duration = 60,
  backgroundColor = '#1a1a2e',
  textColor = '#ffffff',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Count up animation
  const count = spring({
    frame,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
      mass: 0.5,
    },
  });

  const displayNumber = Math.floor(interpolate(count, [0, 1], [0, number]));

  // Format large numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  // Fade in animation
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Scale animation
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 15,
      stiffness: 100,
    },
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        opacity,
      }}
    >
      {/* Main Number */}
      <div
        style={{
          fontSize: 120,
          fontWeight: 'bold',
          color: textColor,
          transform: `scale(${scale})`,
          fontFamily: 'Arial, sans-serif',
        }}
      >
        {unit}
        {formatNumber(displayNumber)}
      </div>

      {/* Label */}
      <div
        style={{
          fontSize: 48,
          color: textColor,
          opacity: 0.8,
          marginTop: 20,
          fontFamily: 'Arial, sans-serif',
        }}
      >
        {label}
      </div>
    </div>
  );
};

/**
 * Python script to generate this animation:
 *
 * from remotion_generator import generate_statistic
 *
 * generate_statistic(
 *   number=1500000,
 *   label="People Affected",
 *   unit="+",
 *   output="statistic_1.mp4"
 * )
 */
