import React from 'react';

export interface WarningBannerProps {
  message: string;
  onDismiss: () => void;
}

export const WarningBanner: React.FC<WarningBannerProps> = ({
  message,
  onDismiss
}) => {
  return (
    <div className="warning-banner">
      <div className="warning-content">
        <span className="warning-icon">⚠️</span>
        <span className="warning-text">{message}</span>
        <button className="warning-dismiss" onClick={onDismiss}>×</button>
      </div>
    </div>
  );
};
