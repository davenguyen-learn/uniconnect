import React, { useState, useEffect } from 'react';
import {
  Users,
  UserCheck,
  UserX,
  Shield,
  Crown,
  Clock,
  X,
  Loader2,
  AlertCircle,
  FileText,
  CheckCircle2
} from 'lucide-react';
import { groupsApi } from '../../api/groups';
import {
  mapGroupMemberToViewModel,
  mapGroupJoinRequestToViewModel,
  type GroupMemberViewModel,
  type GroupJoinRequestViewModel
} from '../../types/groups-mapper';
import './GroupModals.css';

interface MemberManagementModalProps {
  groupId: string;
  groupName: string;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: () => void;
  isAdmin?: boolean;
}

export const MemberManagementModal: React.FC<MemberManagementModalProps> = ({
  groupId,
  isOpen,
  onClose,
  onUpdated,
  isAdmin = false,
}) => {
  const [activeTab, setActiveTab] = useState<'members' | 'requests'>(isAdmin ? 'requests' : 'members');

  useEffect(() => {
    if (isOpen) {
      setActiveTab(isAdmin ? 'requests' : 'members');
    }
  }, [isOpen, isAdmin]);

  const [members, setMembers] = useState<GroupMemberViewModel[]>([]);
  const [joinRequests, setJoinRequests] = useState<GroupJoinRequestViewModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      if (activeTab === 'members') {
        const res = await groupsApi.getGroupMembers(groupId, { limit: 50 });
        setMembers(res.map(mapGroupMemberToViewModel));
      } else {
        const res = await groupsApi.getJoinRequests(groupId, { status: 'pending', limit: 50 });
        setJoinRequests(res.map(mapGroupJoinRequestToViewModel));
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Không thể tải dữ liệu thành viên');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, activeTab, groupId]);

  const handleActionRequest = async (requestId: string, action: 'approved' | 'rejected') => {
    try {
      setProcessingId(requestId);
      setError(null);
      setSuccessMsg(null);
      await groupsApi.actionJoinRequest(groupId, requestId, action);
      setSuccessMsg(action === 'approved' ? 'Đã phê duyệt thành viên mới!' : 'Đã từ chối yêu cầu gia nhập.');
      await fetchData();
      if (onUpdated) onUpdated();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Lỗi khi xử lý yêu cầu gia nhập');
    } finally {
      setProcessingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="group-modal-container">
        {/* Header */}
        <div className="group-modal-header">
          <div className="group-modal-header-info">
            <Users className="w-5 h-5" style={{ color: 'var(--color-text-primary)' }} />
            <div>
              <h2 className="group-modal-title">
                {isAdmin ? 'Quản lý Thành viên & Yêu cầu gia nhập' : 'Danh sách Thành viên'}
              </h2>
            </div>
          </div>
          <button onClick={onClose} className="group-modal-close-btn">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection (Admins only) */}
        {isAdmin && (
          <div className="group-modal-tabs">
            <button
              onClick={() => setActiveTab('requests')}
              className={`group-modal-tab ${activeTab === 'requests' ? 'active' : ''}`}
            >
              <Clock className="w-4 h-4" />
              Yêu cầu chờ duyệt
              {joinRequests.length > 0 && activeTab === 'requests' && (
                <span className="group-modal-tab-count">{joinRequests.length}</span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('members')}
              className={`group-modal-tab ${activeTab === 'members' ? 'active' : ''}`}
            >
              <Users className="w-4 h-4" />
              Danh sách thành viên
            </button>
          </div>
        )}

        {/* Content Body */}
        <div className="group-modal-body">
          {error && (
            <div className="group-modal-alert group-modal-alert--error">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="group-modal-alert group-modal-alert--success">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="group-modal-empty-state">
              <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-text-tertiary)' }} />
              <p>Đang tải dữ liệu...</p>
            </div>
          ) : activeTab === 'requests' ? (
            /* Join Requests Tab */
            joinRequests.length === 0 ? (
              <div className="group-modal-empty-state">
                <UserCheck className="w-12 h-12 stroke-[1.5]" style={{ color: 'var(--color-text-tertiary)' }} />
                <p className="group-modal-empty-title">
                  Không có yêu cầu tham gia nào đang chờ duyệt
                </p>
                <p className="group-modal-empty-desc">
                  Khi có sinh viên nộp đơn xin gia nhập nhóm, yêu cầu sẽ xuất hiện tại đây.
                </p>
              </div>
            ) : (
              <div className="group-modal-list">
                {joinRequests.map((req) => (
                  <div key={req.id} className="group-modal-item">
                    <div className="group-modal-item-header">
                      <div className="group-modal-item-info">
                        <div className="group-modal-item-title-row">
                          <span className="group-modal-item-name">{req.applicantName}</span>
                          {req.applicantUsername && (
                            <span className="group-modal-item-username">{req.applicantUsername}</span>
                          )}
                        </div>
                        <p className="group-modal-item-meta">
                          Ngày nộp đơn: {req.requestedDateFormatted}
                        </p>
                      </div>

                      <div className="group-modal-item-actions" style={{ borderTop: 'none', marginTop: 0, paddingTop: 0 }}>
                        <button
                          onClick={() => handleActionRequest(req.id, 'rejected')}
                          disabled={processingId === req.id}
                          className="group-modal-btn group-modal-btn--outline"
                        >
                          <UserX className="w-3.5 h-3.5" />
                          Từ chối
                        </button>
                        <button
                          onClick={() => handleActionRequest(req.id, 'approved')}
                          disabled={processingId === req.id}
                          className="group-modal-btn group-modal-btn--primary"
                        >
                          {processingId === req.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <UserCheck className="w-3.5 h-3.5" />
                          )}
                          Phê duyệt
                        </button>
                      </div>
                    </div>

                    {req.formResponses && Object.keys(req.formResponses).length > 0 && (
                      <div className="group-modal-message-box">
                        <div className="group-modal-form-response-header">
                          <FileText className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                          <span>Câu trả lời form ứng tuyển:</span>
                        </div>
                        <div className="group-modal-form-response-list">
                          {Object.entries(req.formResponses).map(([key, val]) => (
                            <div key={key}>
                              <span style={{ fontWeight: 600 }}>{key}: </span>
                              <span>{String(val)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
          ) : (
            /* Members List Tab */
            <div className="group-modal-list">
              {members.map((m) => (
                <div key={m.userId} className="group-modal-member-row">
                  <div className="group-modal-member-info">
                    <div className="group-modal-member-avatar">
                      {m.displayName.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="group-modal-member-name">{m.displayName}</div>
                      <div className="group-modal-member-meta">
                        {m.username} • Gia nhập {m.joinedDateFormatted}
                      </div>
                    </div>
                  </div>

                  <span
                    className={`group-modal-role-badge ${m.roleBadge.variant === 'gold'
                      ? 'group-modal-role-badge--gold'
                      : m.roleBadge.variant === 'blue'
                        ? 'group-modal-role-badge--blue'
                        : 'group-modal-role-badge--default'
                      }`}
                  >
                    {m.roleBadge.variant === 'gold' && <Crown className="w-3 h-3" />}
                    {m.roleBadge.variant === 'blue' && <Shield className="w-3 h-3" />}
                    {m.roleBadge.label}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="group-modal-footer">
          <button onClick={onClose} className="group-modal-btn group-modal-btn--ghost">
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
