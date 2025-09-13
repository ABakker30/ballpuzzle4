import React, { useState, useRef, useCallback } from 'react';

interface SliderProps {
  min: number;
  max: number;
  value: number;
  step?: number;
  onChange: (value: number) => void;
  width?: string;
  label?: string;
  formatValue?: (value: number) => string;
}

export const Slider: React.FC<SliderProps> = ({
  min,
  max,
  value,
  step = 1,
  onChange,
  width = '150px',
  label,
  formatValue
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const sliderRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  const clamp = (val: number, minimum: number, maximum: number) => {
    return Math.min(Math.max(val, minimum), maximum);
  };

  const getValueFromPosition = useCallback((clientX: number) => {
    if (!trackRef.current) return value;
    
    const rect = trackRef.current.getBoundingClientRect();
    const percentage = clamp((clientX - rect.left) / rect.width, 0, 1);
    const rawValue = min + percentage * (max - min);
    
    // Round to nearest step
    const steppedValue = Math.round(rawValue / step) * step;
    return clamp(steppedValue, min, max);
  }, [min, max, step, value]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    
    const newValue = getValueFromPosition(e.clientX);
    onChange(newValue);
  }, [getValueFromPosition, onChange]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    e.preventDefault();
    const newValue = getValueFromPosition(e.clientX);
    onChange(newValue);
  }, [isDragging, getValueFromPosition, onChange]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add global mouse event listeners when dragging
  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Calculate thumb position
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div 
      ref={sliderRef}
      style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        userSelect: 'none'
      }}
    >
      {label && <span>{label}:</span>}
      
      <div
        ref={trackRef}
        onMouseDown={handleMouseDown}
        style={{
          position: 'relative',
          width,
          height: '6px',
          backgroundColor: 'var(--border)',
          borderRadius: '3px',
          cursor: 'pointer'
        }}
      >
        {/* Track fill */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            height: '100%',
            width: `${percentage}%`,
            backgroundColor: 'var(--accent)',
            borderRadius: '3px',
            pointerEvents: 'none'
          }}
        />
        
        {/* Thumb */}
        <div
          style={{
            position: 'absolute',
            left: `${percentage}%`,
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: '18px',
            height: '18px',
            backgroundColor: 'var(--accent)',
            borderRadius: '50%',
            border: '2px solid var(--surface)',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
            cursor: isDragging ? 'grabbing' : 'grab',
            pointerEvents: 'none',
            transition: isDragging ? 'none' : 'transform 0.1s ease'
          }}
        />
      </div>
      
      {formatValue && (
        <span style={{ minWidth: '60px', fontSize: '14px' }}>
          {formatValue(value)}
        </span>
      )}
    </div>
  );
};
