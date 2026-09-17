import React, { useState } from 'react';
import { reportsApi } from '../../api/reports';
import { useToast } from '../Toast/ToastContext';
import './ReportModal.css';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: 'activity' | 'user';
  targetId: string;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  targetType,
  targetId
}) => {
  const toast = useToast();
  const [reason, setReason] = useState('spam');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await reportsApi.createReport({
        target_type: targetType,
        target_id: targetId,
        reason,
        description
      });
      toast.success('Đã gửi báo cáo thành công. Cảm ơn bạn đã phản hồi.');
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Không thể gửi báo cáo');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getTargetName = () => {
    if (targetType === 'activity') return 'Hoạt động';
    return 'Người dùng';
  };

  return (
    <div className="report-modal-overlay">
      <div className="report-modal-content">
        <button className="report-modal-close" onClick={onClose}>
          &times;
        </button>
        <h2 className="report-modal-title">Báo cáo {getTargetName()}</h2>
        <form onSubmit={handleSubmit} className="report-form">
          <div className="form-group">
            <label className="form-label">Lý do</label>
            <select
              className="input-field"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            >
              <option value="spam">Spam (Thư rác)</option>
              <option value="inappropriate">Nội dung không phù hợp</option>
              <option value="harassment">Quấy rối</option>
              <option value="other">Khác</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Thông tin bổ sung</label>
            <textarea
              className="input-field textarea-field"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Vui lòng cung cấp thêm thông tin để giúp chúng tôi hiểu rõ hơn vấn đề..."
              rows={4}
            />
          </div>
          <div className="report-modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="btn btn-danger"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Đang gửi...' : 'Gửi báo cáo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
