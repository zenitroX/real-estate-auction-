import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function ToastContainer({ toasts, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-wrap" aria-live="polite" role="status">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type || 'info'}`}>
          <div className="toast-icon">
            {t.type === 'success' && <CheckCircle2 size={20} color="#16A34A" />}
            {t.type === 'error' && <AlertCircle size={20} color="#DC2626" />}
            {(!t.type || t.type === 'info') && <Info size={20} color="#E8B849" />}
          </div>
          <div className="toast-content" style={{ flex: 1 }}>
            <strong>{t.title}</strong>
            {t.message && <p>{t.message}</p>}
          </div>
          <button
            onClick={() => onDismiss(t.id)}
            style={{ color: '#94A3B8', padding: 4 }}
            aria-label="Dismiss alert"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
