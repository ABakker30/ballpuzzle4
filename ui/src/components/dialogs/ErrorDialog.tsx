import React from 'react';

export interface ErrorDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  details?: string[];
  onClose: () => void;
}

export const ErrorDialog: React.FC<ErrorDialogProps> = ({
  isOpen,
  title,
  message,
  details,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog error-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h3>{title}</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="dialog-content">
          <p className="error-message">{message}</p>
          
          {details && details.length > 0 && (
            <div className="error-details">
              <h4>Details:</h4>
              <ul>
                {details.map((detail, index) => (
                  <li key={index}>{detail}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="dialog-actions">
          <button className="button" onClick={onClose}>
            OK
          </button>
        </div>
      </div>
    </div>
  );
};
