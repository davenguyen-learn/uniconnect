import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import './ConflictModal.css';

interface ConflictModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmLabel?: string;
  isSwap?: boolean;
  loading?: boolean;
}

export const ConflictModal: React.FC<ConflictModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Cảnh báo xung đột thời gian',
  message,
  confirmLabel = 'Vẫn tiếp tục đăng ký',
  isSwap = false,
  loading = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="conflict-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="conflict-title">
      <div className="conflict-modal-card">
        <div className="conflict-modal-header">
          <div className="conflict-modal-icon-wrapper" aria-hidden="true">
            <AlertTriangle size={24} className="conflict-modal-icon" />
          </div>
          <h3 id="conflict-title" className="conflict-modal-title">{title}</h3>
          <button
            type="button"
            className="conflict-modal-close"
            onClick={onClose}
            aria-label="Đóng cảnh báo"
            disabled={loading}
          >
            <X size={18} />
          </button>
        </div>

        <div className="conflict-modal-body">
          <p className="conflict-modal-desc">{message}</p>
          {isSwap && (
            <div className="conflict-modal-swap-notice">
              Hệ thống sẽ tự động hủy yêu cầu tham gia ở sự kiện cũ để ưu tiên chuyển sang sự kiện này.
            </div>
          )}
        </div>

        <div className="conflict-modal-footer">
          <button
            type="button"
            className="conflict-btn conflict-btn--cancel"
            onClick={onClose}
            disabled={loading}
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            className="conflict-btn conflict-btn--confirm"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Đang xử lý...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConflictModal;
