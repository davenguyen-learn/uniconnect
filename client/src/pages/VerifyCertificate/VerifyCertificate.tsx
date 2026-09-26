import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import { participationApi, type CertificateResponse } from '../../api/participation';
import { formatCtxh } from '../../utils/format';
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
      <div className="bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/60 border-0 text-center">
        {loading && (
          <div className="py-12">
            <span className="inline-block animate-spin text-4xl mb-3">🔍</span>
            <p className="text-black font-medium">Đang xác thực thông tin chứng nhận trên UniConnect...</p>
          </div>
        )}

        {error && !loading && (
          <div className="py-8">
            <div className="w-16 h-16 rounded-full bg-red-600 flex items-center justify-center mx-auto mb-4">
              <X className="w-8 h-8 text-white stroke-[2.5]" />
            </div>
            <h1 className="text-2xl font-black text-red-600 mb-2">
              Xác thực không thành công
            </h1>
            <p className="text-sm text-black mb-6">{error}</p>
            <Link to="/">
              <Button variant="secondary">Trở về trang chủ</Button>
            </Link>
          </div>
        )}

        {cert && !loading && !error && (
          <div className="py-4">
            <div className="w-20 h-20 rounded-full bg-emerald-600 flex items-center justify-center mx-auto mb-5">
              <Check className="w-10 h-10 text-white stroke-[3]" />
            </div>

            <h1 className="text-xl font-bold text-black mb-1">
              Giấy chứng nhận hợp lệ
            </h1>
            <p className="text-sm text-black mb-6">
              Mã số: <strong className="font-bold text-black">{cert.certificate_code}</strong>
            </p>

            {/* Certificate Details Card */}
            <div className="bg-white/80 rounded-2xl p-6 text-left shadow-lg shadow-slate-100/80 flex flex-col gap-3.5 mb-6 text-sm text-black">
              {/* Row: Người tham gia / Người tổ chức */}
              <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                <span className="text-neutral-500 font-medium sm:w-44 shrink-0">
                  {cert.is_host ? 'Người tổ chức:' : 'Người tham gia:'}
                </span>
                <div className="flex items-center gap-2 flex-wrap">
                  {cert.is_host && (cert.host_id || cert.user_id) ? (
                    <Link
                      to={`/profile/${cert.host_id || cert.user_id}`}
                      className="font-bold text-black hover:underline"
                    >
                      {cert.participant_name}
                    </Link>
                  ) : (
                    <span className="font-bold text-black">{cert.participant_name}</span>
                  )}

                </div>
              </div>

              {/* Row: Email */}
              {cert.participant_email && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Email:</span>
                  <span className="font-semibold text-black">{cert.participant_email}</span>
                </div>
              )}

              {/* Row: Đơn vị / Trường */}
              {cert.participant_university && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Đơn vị / Trường:</span>
                  <span className="font-semibold text-black">{cert.participant_university}</span>
                </div>
              )}

              {/* Custom fields */}
              {cert.custom_fields && cert.custom_fields.length > 0 && cert.custom_fields.map((f, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">{f.label}:</span>
                  <span className="font-semibold text-black">{f.value}</span>
                </div>
              ))}

              {/* Row: Hoạt động */}
              <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                <span className="text-neutral-500 font-medium sm:w-44 shrink-0">
                  {cert.is_host ? 'Hoạt động đã tổ chức:' : 'Hoạt động đã tham gia:'}
                </span>
                <span className="font-bold text-black">{cert.activity_title}</span>
              </div>

              {/* Row: Thời gian */}
              <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Thời gian tổ chức:</span>
                <span className="font-semibold text-black">{cert.activity_date}</span>
              </div>

              {/* Row: Địa điểm */}
              {(cert.meeting_location || cert.location_name) && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Địa điểm:</span>
                  <span className="font-semibold text-black">{cert.meeting_location || cert.location_name}</span>
                </div>
              )}

              {/* Row: Đơn vị tổ chức */}
              {cert.group_name && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Đơn vị tổ chức:</span>
                  {cert.group_id && !cert.group_is_private ? (
                    <Link
                      to={`/groups/${cert.group_id}`}
                      className="font-bold text-black hover:underline"
                    >
                      {cert.group_name}
                    </Link>
                  ) : (
                    <span className="font-semibold text-black">{cert.group_name}</span>
                  )}
                </div>
              )}

              {/* Row: Người tổ chức (nếu xem chứng nhận của participant) */}
              {!cert.is_host && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Người tổ chức:</span>
                  {cert.host_id ? (
                    <Link
                      to={`/profile/${cert.host_id}`}
                      className="font-bold text-black hover:underline"
                    >
                      {cert.host_name}
                    </Link>
                  ) : (
                    <span className="font-semibold text-black">{cert.host_name}</span>
                  )}
                </div>
              )}

              {/* Row: Số ngày CTXH */}
              {cert.social_work_days !== null && cert.social_work_days !== undefined && cert.social_work_days > 0 && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 pb-3 border-b border-slate-100">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Ngày công tác xã hội:</span>
                  <span className="font-bold text-black">+{formatCtxh(cert.social_work_days)} ngày</span>
                </div>
              )}

              {/* Row: Danh hiệu */}
              {cert.trophy_name && (
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
                  <span className="text-neutral-500 font-medium sm:w-44 shrink-0">Danh hiệu đạt được:</span>
                  <span className="font-bold text-black">{cert.trophy_name}</span>
                </div>
              )}
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

