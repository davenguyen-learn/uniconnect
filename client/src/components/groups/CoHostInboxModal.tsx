import React, { useState, useEffect } from 'react';
import { 
  Inbox, 
  CheckCircle, 
  XCircle, 
  Building2, 
  Calendar, 
  MessageSquare, 
  AlertCircle, 
  X,
  Loader2
} from 'lucide-react';
import { groupsApi } from '../../api/groups';
import { mapCoHostInvitationToViewModel, type CoHostInvitationViewModel } from '../../types/groups-mapper';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/50">
              <Inbox className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Hộp thư mời Đồng tổ chức (Co-Hosting)
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Quản lý các lời mời hợp tác tổ chức sự kiện cho <span className="font-semibold text-slate-700 dark:text-slate-300">{groupName}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-2 px-6 pt-3 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setActiveTab('pending')}
            className={`pb-2.5 px-2 text-sm font-semibold border-b-2 transition ${
              activeTab === 'pending'
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            Chờ phản hồi
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`pb-2.5 px-2 text-sm font-semibold border-b-2 transition ${
              activeTab === 'all'
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            Tất cả lời mời
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 text-sm rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900/50">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mb-2" />
              <p className="text-sm">Đang tải danh sách lời mời...</p>
            </div>
          ) : invitations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-slate-400">
              <Inbox className="w-12 h-12 stroke-[1.5] mb-2 text-slate-300 dark:text-slate-600" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                {activeTab === 'pending' ? 'Không có lời mời nào đang chờ phản hồi' : 'Chưa có lịch sử lời mời nào'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Khi các câu lạc bộ khác mời bạn làm Đồng tổ chức, thông tin sẽ hiển thị tại đây.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {invitations.map((inv) => (
                <div
                  key={inv.id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60 shadow-sm hover:border-indigo-200 dark:hover:border-indigo-900/60 transition"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-indigo-500 shrink-0" />
                        <span className="font-bold text-slate-900 dark:text-white text-base">
                          {inv.activityTitle}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                        <Building2 className="w-3.5 h-3.5" />
                        <span>CLB tổ chức: <strong className="text-slate-700 dark:text-slate-200">{inv.hostGroupName}</strong></span>
                        <span>•</span>
                        <span>{inv.createdDateFormatted}</span>
                      </div>
                    </div>

                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        inv.statusBadge.variant === 'warning'
                          ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900/50'
                          : inv.statusBadge.variant === 'success'
                          ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50'
                          : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-900/50'
                      }`}
                    >
                      {inv.statusBadge.label}
                    </span>
                  </div>

                  {inv.message && (
                    <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/60 text-xs text-slate-600 dark:text-slate-300 border border-slate-100 dark:border-slate-800 flex items-start gap-2">
                      <MessageSquare className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <p className="italic">"{inv.message}"</p>
                    </div>
                  )}

                  {inv.status === 'pending' && (
                    <div className="mt-4 flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800/80">
                      <button
                        onClick={() => handleRespond(inv.id, 'declined')}
                        disabled={processingId === inv.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg border border-slate-200 dark:border-slate-700 transition disabled:opacity-50"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Từ chối
                      </button>
                      <button
                        onClick={() => handleRespond(inv.id, 'accepted')}
                        disabled={processingId === inv.id}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50"
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
        <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
