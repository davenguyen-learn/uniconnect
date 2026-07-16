import React, { useState } from 'react';
import { reportsApi } from '../../api/reports';
import { useToast } from '../Toast/ToastContext';
import './ReportModal.css';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: 'activity' | 'document' | 'user';
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
      toast.success('Report submitted successfully. Thank you for your feedback.');
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit report');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getTargetName = () => {
    if (targetType === 'activity') return 'Activity';
    if (targetType === 'document') return 'Document';
    return 'User';
  };

  return (
    <div className="report-modal-overlay">
      <div className="report-modal-content">
        <button className="report-modal-close" onClick={onClose}>
          &times;
        </button>
        <h2 className="report-modal-title">Report {getTargetName()}</h2>
        <form onSubmit={handleSubmit} className="report-form">
          <div className="form-group">
            <label className="form-label">Reason</label>
            <select
              className="input-field"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            >
              <option value="spam">Spam</option>
              <option value="inappropriate">Inappropriate Content</option>
              <option value="harassment">Harassment</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Additional Details</label>
            <textarea
              className="input-field textarea-field"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please provide more details to help us understand the issue..."
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
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-danger"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
