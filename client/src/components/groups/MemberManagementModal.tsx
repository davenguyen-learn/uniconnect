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

interface MemberManagementModalProps {
  groupId: string;
  groupName: string;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: () => void;
}

export const MemberManagementModal: React.FC<MemberManagementModalProps> = ({
  groupId,
  groupName,
  isOpen,
  onClose,
  onUpdated,
}) => {
  const [activeTab, setActiveTab] = useState<'members' | 'requests'>('requests');
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-900/50">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Quản lý Thành viên & Yêu cầu gia nhập
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                CLB: <span className="font-semibold text-slate-700 dark:text-slate-300">{groupName}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:bg-slate-800 rounded-xl transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center gap-4 px-6 pt-3 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setActiveTab('requests')}
            className={`pb-2.5 px-1 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'requests'
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            <Clock className="w-4 h-4" />
            Yêu cầu chờ duyệt
            {joinRequests.length > 0 && activeTab === 'requests' && (
              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 rounded-full font-bold">
                {joinRequests.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('members')}
            className={`pb-2.5 px-1 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'members'
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            <Users className="w-4 h-4" />
            Danh sách thành viên
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

          {successMsg && (
            <div className="flex items-center gap-2 p-3 text-sm rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mb-2" />
              <p className="text-sm">Đang tải dữ liệu...</p>
            </div>
          ) : activeTab === 'requests' ? (
            /* Join Requests Tab */
            joinRequests.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-slate-400">
                <UserCheck className="w-12 h-12 stroke-[1.5] mb-2 text-slate-300 dark:text-slate-600" />
                <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                  Không có yêu cầu tham gia nào đang chờ duyệt
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Khi có sinh viên nộp đơn xin gia nhập câu lạc bộ, yêu cầu sẽ xuất hiện tại đây.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {joinRequests.map((req) => (
                  <div
                    key={req.id}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60 shadow-sm hover:border-blue-200 dark:hover:border-blue-900/60 transition"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 dark:text-white text-base">
                            {req.applicantName}
                          </span>
                          {req.applicantUsername && (
                            <span className="text-xs text-slate-400">{req.applicantUsername}</span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          Ngày nộp đơn: {req.requestedDateFormatted}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleActionRequest(req.id, 'rejected')}
                          disabled={processingId === req.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg border border-slate-200 dark:border-slate-700 transition disabled:opacity-50"
                        >
                          <UserX className="w-3.5 h-3.5" />
                          Từ chối
                        </button>
                        <button
                          onClick={() => handleActionRequest(req.id, 'approved')}
                          disabled={processingId === req.id}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition disabled:opacity-50"
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
                      <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300">
                          <FileText className="w-3.5 h-3.5 text-blue-500" />
                          <span>Câu trả lời form ứng tuyển:</span>
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1 pl-5">
                          {Object.entries(req.formResponses).map(([key, val]) => (
                            <div key={key}>
                              <span className="font-medium text-slate-700 dark:text-slate-200">{key}: </span>
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
            <div className="space-y-2">
              {members.map((m) => (
                <div
                  key={m.userId}
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-700 dark:text-slate-300 text-sm border border-slate-200 dark:border-slate-700">
                      {m.displayName.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-white text-sm">
                        {m.displayName}
                      </div>
                      <div className="text-xs text-slate-400">
                        {m.username} • Gia nhập {m.joinedDateFormatted}
                      </div>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                      m.roleBadge.variant === 'gold'
                        ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900/50'
                        : m.roleBadge.variant === 'blue'
                        ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-900/50'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    {m.roleBadge.variant === 'gold' && <Crown className="w-3 h-3 text-amber-500" />}
                    {m.roleBadge.variant === 'blue' && <Shield className="w-3 h-3 text-blue-500" />}
                    {m.roleBadge.label}
                  </span>
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
