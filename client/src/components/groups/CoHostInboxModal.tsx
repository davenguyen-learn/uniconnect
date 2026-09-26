import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Inbox,
  CheckCircle,
  XCircle,
  AlertCircle,
  X,
  Loader2
} from 'lucide-react';
import { groupsApi } from '../../api/groups';
import { mapCoHostInvitationToViewModel, type CoHostInvitationViewModel } from '../../types/groups-mapper';
import './GroupModals.css';

interface CoHostInboxModalProps {
  groupId: string;
  groupName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const CoHostInboxModal: React.FC<CoHostInboxModalProps> = ({
  groupId,
  groupName,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const navigate = useNavigate();
  const [invitations, setInvitations] = useState<CoHostInvitationViewModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'pending' | 'all'>('pending');

  const fetchInvitations = async () => {
    try {
      setLoading(true);
      setError(null);
      const statusParam = activeTab === 'pending' ? 'pending' : undefined;
      const res = await groupsApi.getCoHostInvitations(groupId, { status: statusParam, limit: 50 });
      setInvitations(res.map(mapCoHostInvitationToViewModel));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Không thể tải danh sách lời mời phối hợp');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchInvitations();
    }
  }, [isOpen, activeTab, groupId]);

  const handleRespond = async (invitationId: string, action: 'accepted' | 'declined') => {
    try {
      setProcessingId(invitationId);
      setError(null);
      await groupsApi.respondCoHostInvitation(invitationId, action);
      await fetchInvitations();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Không thể xử lý lời mời lúc này');
    } finally {
      setProcessingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="group-modal-container cohost-inbox-modal">
        {/* Header */}
        <div className="group-modal-header">
          <div className="group-modal-header-info">
            <Inbox className="w-5 h-5" style={{ color: '#000000' }} />
            <div>
              <h2 className="group-modal-title" style={{ color: '#000000' }}>
                Hộp thư mời đồng tổ chức
              </h2>
              {groupName && (
                <p className="group-modal-subtitle" style={{ color: '#000000' }}>
                  Quản lý các lời mời hợp tác tổ chức sự kiện cho <strong style={{ color: '#000000' }}>{groupName}</strong>
                </p>
              )}
            </div>
          </div>
          <button onClick={onClose} className="group-modal-close-btn" style={{ color: '#000000' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Filters */}
        <div className="group-modal-tabs">
          <button
            onClick={() => setActiveTab('pending')}
            className={`group-modal-tab ${activeTab === 'pending' ? 'active' : ''}`}
            style={{ color: '#000000', borderColor: activeTab === 'pending' ? '#000000' : 'transparent' }}
          >
            Chờ phản hồi
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`group-modal-tab ${activeTab === 'all' ? 'active' : ''}`}
            style={{ color: '#000000', borderColor: activeTab === 'all' ? '#000000' : 'transparent' }}
          >
            Tất cả lời mời
          </button>
        </div>

        {/* Content Body */}
        <div className="group-modal-body">
          {error && (
            <div className="group-modal-alert group-modal-alert--error">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="group-modal-empty-state">
              <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#000000' }} />
              <p style={{ color: '#000000' }}>Đang tải danh sách lời mời...</p>
            </div>
          ) : invitations.length === 0 ? (
            <div className="group-modal-empty-state">
              <Inbox className="w-12 h-12 stroke-[1.5]" style={{ color: '#000000' }} />
              <p className="group-modal-empty-title" style={{ color: '#000000' }}>
                {activeTab === 'pending' ? 'Không có lời mời nào đang chờ phản hồi' : 'Chưa có lịch sử lời mời nào'}
              </p>
              <p className="group-modal-empty-desc" style={{ color: '#000000' }}>
                Khi các nhóm khác mời bạn làm đồng tổ chức, thông tin sẽ hiển thị tại đây.
              </p>
            </div>
          ) : (
            <div className="group-modal-list">
              {invitations.map((inv) => (
                <div
                  key={inv.id}
                  className="group-modal-item group-modal-item--clickable"
                  onClick={() => {
                    onClose();
                    navigate(`/activities/${inv.activityId}`);
                  }}
                  title="Nhấn để xem chi tiết hoạt động"
                >
                  <div className="group-modal-item-header">
                    <div className="group-modal-item-info">
                      <div className="group-modal-item-title-row">
                        <Link
                          to={`/activities/${inv.activityId}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onClose();
                          }}
                          className="group-modal-item-name"
                          style={{ color: '#000000', textDecoration: 'none' }}
                        >
                          {inv.activityTitle}
                        </Link>
                      </div>
                      <div className="group-modal-item-meta" style={{ color: '#000000' }}>
                        <span style={{ color: '#000000' }}>Nhóm tổ chức: <strong style={{ color: '#000000' }}>{inv.hostGroupName}</strong></span>
                        <span style={{ color: '#000000' }}>•</span>
                        <span style={{ color: '#000000' }}>{inv.createdDateFormatted}</span>
                      </div>
                    </div>

                    <span
                      className={`group-modal-badge ${inv.statusBadge.variant === 'warning'
                        ? 'group-modal-badge--warning'
                        : inv.statusBadge.variant === 'success'
                          ? 'group-modal-badge--success'
                          : 'group-modal-badge--error'
                        }`}
                    >
                      {inv.statusBadge.label}
                    </span>
                  </div>

                  {inv.message && (
                    <div className="group-modal-message-box" style={{ color: '#000000' }}>
                      <p className="italic" style={{ color: '#000000' }}>"{inv.message}"</p>
                    </div>
                  )}

                  {inv.status === 'pending' && (
                    <div
                      className="group-modal-item-actions"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRespond(inv.id, 'declined');
                        }}
                        disabled={processingId === inv.id}
                        className="group-modal-btn group-modal-btn--outline"
                        style={{ color: '#000000' }}
                      >
                        <XCircle className="w-3.5 h-3.5" style={{ color: '#000000' }} />
                        Từ chối
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRespond(inv.id, 'accepted');
                        }}
                        disabled={processingId === inv.id}
                        className="group-modal-btn group-modal-btn--primary"
                      >
                        {processingId === inv.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="w-3.5 h-3.5" />
                        )}
                        Đồng ý làm Đồng tổ chức
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="group-modal-footer">
          <button onClick={onClose} className="group-modal-btn group-modal-btn--ghost" style={{ color: '#000000' }}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
