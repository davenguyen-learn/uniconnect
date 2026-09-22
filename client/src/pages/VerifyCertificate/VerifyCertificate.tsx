import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { participationApi, type CertificateResponse } from '../../api/participation';
import Button from '../../components/Button/Button';

export default function VerifyCertificate() {
  const [searchParams] = useSearchParams();
  const code = searchParams.get('code');

  const [loading, setLoading] = useState(true);
  const [cert, setCert] = useState<CertificateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (code) {
      setLoading(true);
      setError(null);
      participationApi
        .verifyCertificate(code)
        .then((res) => setCert(res))
        .catch((err) => {
          setError(err.response?.data?.detail || 'Giấy chứng nhận không tồn tại hoặc không hợp lệ.');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
      setError('Vui lòng cung cấp mã số giấy chứng nhận để tra cứu.');
    }
  }, [code]);

  return (
    <div className="container py-12 max-w-2xl mx-auto px-4 animate-fade-in">
      <div className="glass p-8 rounded-3xl border border-white/20 shadow-2xl text-center">
        {loading && (
          <div className="py-12">
            <span className="inline-block animate-spin text-4xl mb-3">🔍</span>
            <p className="text-[var(--color-text-secondary)] font-medium">Đang xác thực thông tin chứng nhận với hệ thống...</p>
          </div>
        )}

        {error && !loading && (
          <div className="py-8">
            <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-4 text-3xl text-red-500">
              ✕
            </div>
            <h1 className="text-2xl font-black text-red-600 dark:text-red-400 mb-2">
              Xác thực không thành công
            </h1>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">{error}</p>
            <Link to="/">
              <Button variant="secondary">Trở về trang chủ</Button>
            </Link>
          </div>
        )}

        {cert && !loading && !error && (
          <div className="py-4">
            <div className="w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-950/60 border-2 border-emerald-600 dark:border-emerald-500 flex items-center justify-center mx-auto mb-4 text-4xl text-emerald-700 dark:text-emerald-300 shadow-lg shadow-emerald-500/15">
              ✓
            </div>

            <div className="inline-block px-4 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-bold uppercase tracking-wider mb-2">
              Xác thực điện tử chính thức (Official Verified)
            </div>

            <h1 className="text-2xl font-black text-[var(--color-text-primary)] mb-1">
              Giấy chứng nhận hợp lệ
            </h1>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">
              Mã số: <strong className="font-mono text-indigo-600 dark:text-indigo-400">{cert.certificate_code}</strong>
            </p>

            {/* Certificate Details Card */}
            <div className="bg-white/50 dark:bg-black/20 rounded-2xl p-6 text-left border border-black/5 dark:border-white/10 flex flex-col gap-4 mb-6">
              <div>
                <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider block">Người tham gia:</span>
                <span className="text-lg font-bold text-[var(--color-text-primary)]">{cert.participant_name}</span>
                {cert.participant_university && (
                  <span className="text-sm text-blue-600 dark:text-blue-400 block font-medium">
                    {cert.participant_university}
                  </span>
                )}
              </div>

              <div className="pt-3 border-t border-gray-200 dark:border-gray-800">
                <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider block">Hoạt động đã tham gia:</span>
                <span className="text-base font-bold text-[var(--color-text-primary)]">"{cert.activity_title}"</span>
                <span className="text-xs text-[var(--color-text-secondary)] block mt-1">
                  📅 {cert.activity_date} {(cert.meeting_location || cert.location_name) ? `• 📍 ${cert.meeting_location || cert.location_name}` : ''}
                </span>
              </div>

              <div className="pt-3 border-t border-gray-200 dark:border-gray-800">
                <span className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wider block">Đơn vị tổ chức:</span>
                <span className="text-sm font-semibold text-[var(--color-text-primary)]">{cert.host_name}</span>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-3 pt-2">
                {cert.social_work_days !== null && cert.social_work_days !== undefined && cert.social_work_days > 0 && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 font-bold text-sm">
                    <span>🌱</span>
                    <span>+{cert.social_work_days} Ngày Công tác Xã hội (CTXH)</span>
                  </div>
                )}

                {cert.trophy_name && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-300 font-bold text-sm">
                    <span>{cert.trophy_icon || '🏆'}</span>
                    <span>Trophy: {cert.trophy_name}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-center gap-3">
              <Link to={`/activities/${cert.activity_id}`}>
                <Button variant="primary">
                  Xem chi tiết hoạt động
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
