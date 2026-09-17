import React, { useEffect, useState } from 'react';
import { participationApi, type CertificateResponse } from '../../api/participation';
import Button from '../Button/Button';
import './CertificateModal.css';

interface CertificateModalProps {
  isOpen: boolean;
  onClose: () => void;
  activityId: string;
  userId?: string;
}

export const CertificateModal: React.FC<CertificateModalProps> = ({
  isOpen,
  onClose,
  activityId,
  userId,
}) => {
  const [data, setData] = useState<CertificateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && activityId) {
      setLoading(true);
      setError(null);
      participationApi
        .getCertificate(activityId, userId)
        .then((res) => setData(res))
        .catch((err) => {
          setError(err.response?.data?.detail || err.message || 'Không thể tải giấy chứng nhận');
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, activityId, userId]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const verifyUrl = data
    ? `${window.location.origin}/verify-certificate?code=${encodeURIComponent(data.certificate_code)}`
    : '';

  return (
    <div className="certificate-modal-overlay animate-fade-in">
      <div className="certificate-modal-container glass">
        <div className="certificate-modal-header no-print">
          <div className="flex items-center gap-2">
            <span className="text-xl">🎓</span>
            <h2 className="text-lg font-bold text-[var(--color-text-primary)]">Giấy chứng nhận tham gia</h2>
          </div>
          <div className="flex items-center gap-2">
            {data && (
              <Button size="sm" variant="primary" onClick={handlePrint}>
                🖨️ In / Tải PDF
              </Button>
            )}
            <button className="certificate-modal-close" onClick={onClose}>
              ✕
            </button>
          </div>
        </div>

        <div className="certificate-modal-body">
          {loading && (
            <div className="certificate-loading py-16 text-center text-[var(--color-text-secondary)]">
              <span className="inline-block animate-spin text-2xl mb-2">⏳</span>
              <p>Đang khởi tạo giấy chứng nhận chính thức...</p>
            </div>
          )}

          {error && (
            <div className="certificate-error py-12 text-center">
              <span className="text-3xl mb-2 block">⚠️</span>
              <p className="text-red-500 font-medium mb-4">{error}</p>
              <Button variant="secondary" onClick={onClose}>
                Đóng
              </Button>
            </div>
          )}

          {data && !loading && !error && (
            <div className="certificate-printable-wrapper">
              <div className="certificate-sheet">
                {/* Ornate corners */}
                <div className="cert-corner cert-corner--tl" />
                <div className="cert-corner cert-corner--tr" />
                <div className="cert-corner cert-corner--bl" />
                <div className="cert-corner cert-corner--br" />

                <div className="cert-inner-border">
                  {/* Certificate Top Header */}
                  <div className="cert-top">
                    <div className="cert-subheading">HỆ THỐNG QUẢN LÝ HOẠT ĐỘNG SINH VIÊN UNICONNECT</div>
                    <h1 className="cert-main-title">GIẤY CHỨNG NHẬN</h1>
                    <div className="cert-title-en">CERTIFICATE OF PARTICIPATION</div>
                  </div>

                  {/* Recipient */}
                  <div className="cert-body">
                    <p className="cert-presentation-text">Trân trọng chứng nhận sinh viên</p>
                    <h2 className="cert-recipient-name">{data.participant_name}</h2>
                    {data.participant_university && (
                      <p className="cert-university">{data.participant_university}</p>
                    )}

                    <p className="cert-completion-text">
                      Đã hoàn thành xuất sắc và được xác nhận tham gia hoạt động
                    </p>
                    <h3 className="cert-activity-title">"{data.activity_title}"</h3>

                    <div className="cert-meta-row">
                      <span><strong>Ngày tổ chức:</strong> {data.activity_date}</span>
                      {data.location_name && <span>• <strong>Địa điểm:</strong> {data.location_name}</span>}
                      <span>• <strong>Đơn vị tổ chức:</strong> {data.host_name}</span>
                    </div>

                    {/* Highlights: Social work days and Trophy */}
                    <div className="cert-highlights-row">
                      {data.social_work_days !== null && data.social_work_days !== undefined && data.social_work_days > 0 && (
                        <div className="cert-badge cert-badge--social">
                          <span className="cert-badge-icon">🌱</span>
                          <div className="cert-badge-text">
                            <span className="cert-badge-val">{data.social_work_days} Ngày</span>
                            <span className="cert-badge-lbl">Công tác Xã hội (CTXH)</span>
                          </div>
                        </div>
                      )}

                      {data.trophy_name && (
                        <div className="cert-badge cert-badge--trophy">
                          <span className="cert-badge-icon">{data.trophy_icon || '🏆'}</span>
                          <div className="cert-badge-text">
                            <span className="cert-badge-val">{data.trophy_name}</span>
                            <span className="cert-badge-lbl">+{data.trophy_points} Điểm danh hiệu</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Footer & QR Verification */}
                  <div className="cert-footer">
                    <div className="cert-verification">
                      <img
                        src={`https://api.qrserver.com/v1/create-qr-code/?size=90x90&data=${encodeURIComponent(verifyUrl)}`}
                        alt="Verification QR"
                        className="cert-qr-img"
                      />
                      <div className="cert-verification-text">
                        <span className="cert-code-label">MÃ SỐ XÁC MINH:</span>
                        <strong className="cert-code-val">{data.certificate_code}</strong>
                        <span className="cert-code-hint">Quét QR để tra cứu tính hợp lệ trực tuyến</span>
                      </div>
                    </div>

                    <div className="cert-seal-box">
                      <div className="cert-digital-seal">
                        <span>UNICONNECT</span>
                        <span className="cert-seal-star">★ VERIFIED ★</span>
                        <span>OFFICIAL</span>
                      </div>
                    </div>

                    <div className="cert-signature-box">
                      <span className="cert-sig-date">Ngày cấp: {new Date(data.issued_at).toLocaleDateString('vi-VN')}</span>
                      <span className="cert-sig-title">ĐẠI DIỆN BAN TỔ CHỨC</span>
                      <div className="cert-sig-name">{data.host_name}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
