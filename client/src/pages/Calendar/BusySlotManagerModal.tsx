import React, { useEffect, useState } from 'react';
import { Calendar, Clock, Repeat, Trash2, X, Plus, AlertCircle } from 'lucide-react';
import { calendarApi } from '../../api/calendar';
import { mapBusySlotToRuleViewModel, type BusySlotRuleViewModel } from '../../types/calendar-mapper';
import { useToast } from '../../components/Toast/ToastContext';

interface BusySlotManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenCreateModal: () => void;
  onRulesChanged: () => void;
}

export const BusySlotManagerModal: React.FC<BusySlotManagerModalProps> = ({
  isOpen,
  onClose,
  onOpenCreateModal,
  onRulesChanged,
}) => {
  const toast = useToast();
  const [rules, setRules] = useState<BusySlotRuleViewModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await calendarApi.listBusySlots();
      setRules(data.map(mapBusySlotToRuleViewModel));
    } catch (err: any) {
      toast.error('Không thể tải danh sách lịch bận: ' + (err.message || 'Lỗi kết nối'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchRules();
    }
  }, [isOpen]);

  const handleDelete = async (rule: BusySlotRuleViewModel) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa lịch bận "${rule.title}"?`)) return;

    setDeletingId(rule.id);
    try {
      await calendarApi.deleteBusySlot(rule.id);
      toast.success('Đã xóa quy tắc lịch bận thành công');
      await fetchRules();
      onRulesChanged();
    } catch (err: any) {
      toast.error('Không thể xóa lịch bận: ' + (err.message || 'Lỗi'));
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content busy-manager-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="busy-manager-header-title">
            <h3>Quản lý lịch bận</h3>
          </div>
          <button
            type="button"
            className="btn-close-modal"
            onClick={onClose}
            aria-label="Đóng quản lý lịch bận"
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body busy-manager-body">
          <p className="busy-manager-note">
            Các quy tắc lịch bận định kỳ và lịch bận 1 lần do bạn thiết lập. Hệ thống sẽ tự động đối soát và cảnh báo xung đột khi bạn đăng ký hoạt động.
          </p>

          {loading ? (
            <div className="busy-manager-loading">Đang tải danh sách lịch bận...</div>
          ) : rules.length === 0 ? (
            <div className="busy-manager-empty">
              <AlertCircle size={36} className="empty-icon" />
              <p>Bạn chưa thiết lập lịch bận cá nhân hoặc lịch học định kỳ nào.</p>
              <button
                type="button"
                className="btn-primary btn-sm"
                onClick={() => {
                  onClose();
                  onOpenCreateModal();
                }}
              >
                <Plus size={16} /> Thêm lịch bận mới
              </button>
            </div>
          ) : (
            <div className="busy-rules-list">
              {rules.map((r) => (
                <div key={r.id} className="busy-rule-card">
                  <div className="busy-rule-info">
                    <div className="busy-rule-title-row">
                      <span className="busy-rule-title">{r.title}</span>
                      {r.recurrence === 'weekly' ? (
                        <span className="badge-rule-weekly">
                          <Repeat size={12} /> Lặp tuần
                        </span>
                      ) : (
                        <span className="badge-rule-once">1 lần</span>
                      )}
                    </div>

                    <div className="busy-rule-meta">
                      <div className="meta-line">
                        <Clock size={14} />
                        <span>{r.timeRange}</span>
                      </div>
                      <div className="meta-line">
                        <Calendar size={14} />
                        <span>{r.validityRange}</span>
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn-del-rule"
                    title="Xóa quy tắc lịch bận"
                    disabled={deletingId === r.id}
                    onClick={() => handleDelete(r)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
