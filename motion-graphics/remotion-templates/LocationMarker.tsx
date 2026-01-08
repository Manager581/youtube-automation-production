/**
 * Location Marker Template
 * Shows map with animated pin at location
 *
 * Usage in Remotion:
 * <LocationMarker lat={40.7128} lng={-74.0060} label="New York" duration={90} />
 */

import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface LocationMarkerProps {
  lat: number;
  lng: number;
  label: string;
  duration?: number;
  mapStyle?: 'satellite' | 'streets';
}

export const LocationMarker: React.FC<LocationMarkerProps> = ({
  lat,
  lng,
  label,
  duration = 90,
  mapStyle = 'satellite',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Zoom in animation
  const zoom = interpolate(frame, [0, 60], [3, 10], {
    extrapolateRight: 'clamp',
  });

  // Pin drop animation
  const pinY = spring({
    frame: frame - 30, // Start after zoom
    fps,
    config: {
      damping: 20,
      stiffness: 300,
    },
    from: -200,
    to: 0,
  });

  // Label fade in
  const labelOpacity = interpolate(frame, [50, 70], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Pulse animation for pin
  const pinScale = interpolate(
    frame % 30, // Repeat every 30 frames
    [0, 15, 30],
    [1, 1.2, 1]
  );

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: '#000',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Map Background (Placeholder - integrate with Mapbox in production) */}
      <div
        style={{
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          transform: `scale(${zoom / 5})`,
          transformOrigin: 'center',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        {/* In production, use Mapbox static image:
            https://api.mapbox.com/styles/v1/mapbox/${mapStyle}-v9/static/${lng},${lat},${zoom},0/1280x720?access_token=YOUR_TOKEN
        */}
      </div>

      {/* Location Pin */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(-50%, ${pinY}px) scale(${pinScale})`,
        }}
      >
        {/* Pin Icon */}
        <svg
          width="60"
          height="80"
          viewBox="0 0 24 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 0C5.4 0 0 5.4 0 12C0 21 12 32 12 32C12 32 24 21 24 12C24 5.4 18.6 0 12 0Z"
            fill="#FF0000"
          />
          <circle cx="12" cy="12" r="4" fill="#FFFFFF" />
        </svg>
      </div>

      {/* Location Label */}
      <div
        style={{
          position: 'absolute',
          bottom: 100,
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: '15px 30px',
          borderRadius: 10,
          opacity: labelOpacity,
        }}
      >
        <div
          style={{
            fontSize: 36,
            fontWeight: 'bold',
            color: '#fff',
            fontFamily: 'Arial, sans-serif',
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: 20,
            color: '#ccc',
            fontFamily: 'Arial, sans-serif',
            marginTop: 5,
          }}
        >
          {lat.toFixed(4)}°, {lng.toFixed(4)}°
        </div>
      </div>
    </div>
  );
};

/**
 * Python script to generate:
 *
 * from remotion_generator import generate_location
 *
 * generate_location(
 *   lat=40.7128,
 *   lng=-74.0060,
 *   label="New York City",
 *   output="location_nyc.mp4"
 * )
 */
