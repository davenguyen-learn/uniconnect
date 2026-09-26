import React, { useEffect, useRef, useState } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { participationApi, type CertificateResponse } from '../../api/participation';
import { formatCtxh } from '../../utils/format';
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
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const certRef = useRef<HTMLDivElement>(null);

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

  const handleDownload = async () => {
    if (!data || !certRef.current || downloading) return;
    setDownloading(true);

    try {
      const element = certRef.current;
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const margin = 15;
      const contentWidth = pdfWidth - margin * 2;
      const contentHeight = (canvas.height * contentWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', margin, margin, contentWidth, contentHeight);

      const safeTitle = data.activity_title.replace(/[/\\?%*:|"<>]/g, '-').trim();
      const fileName = `Giấy xác nhận tham gia hoạt động ${safeTitle}.pdf`;
      pdf.save(fileName);
    } catch (err) {
      console.error('Lỗi khi tải file PDF:', err);
    } finally {
      setDownloading(false);
    }
  };

  const verifyUrl = data
    ? `${window.location.origin}/verify-certificate?code=${encodeURIComponent(data.certificate_code)}`
    : '';

  return (
    <div className="certificate-modal-overlay animate-fade-in">
      <div className="certificate-modal-container">
        <div className="certificate-modal-header no-print">
          <h2 className="cert-modal-title">Giấy xác nhận tham gia hoạt động</h2>
          <div className="flex items-center gap-2">
            {data && (
              <Button size="sm" variant="primary" onClick={handleDownload} disabled={downloading}>
                {downloading ? 'Đang tạo PDF...' : 'Tải PDF'}
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
              <p>Đang tải...</p>
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
              <div className="cert-doc" ref={certRef}>
                {/* Document Header */}
                <div className="cert-doc-header">
                  <div className="cert-doc-org">NỀN TẢNG KẾT NỐI HOẠT ĐỘNG SINH VIÊN</div>
                  <div className="cert-doc-platform">UNICONNECT</div>
                  <div className="cert-doc-line" />
                </div>

                {/* Title */}
                <h1 className="cert-doc-title">
                  {data.is_host ? 'GIẤY XÁC NHẬN TỔ CHỨC HOẠT ĐỘNG' : 'GIẤY XÁC NHẬN THAM GIA HOẠT ĐỘNG'}
                </h1>

                {/* Body */}
                <div className="cert-doc-body">
                  <table className="cert-doc-table">
                    <tbody>
                      <tr>
                        <td className="cert-doc-label">Họ và tên:</td>
                        <td className="cert-doc-value cert-doc-value--name">{data.participant_name}</td>
                      </tr>
                      {data.is_host && (
                        <tr>
                          <td className="cert-doc-label">Vai trò:</td>
                          <td className="cert-doc-value font-bold text-indigo-700">Trưởng ban tổ chức (Host)</td>
                        </tr>
                      )}
                      {data.participant_email && (
                        <tr>
                          <td className="cert-doc-label">Email:</td>
                          <td className="cert-doc-value">{data.participant_email}</td>
                        </tr>
                      )}
                      {data.participant_university && (
                        <tr>
                          <td className="cert-doc-label">Đơn vị:</td>
                          <td className="cert-doc-value">{data.participant_university}</td>
                        </tr>
                      )}
                      {data.custom_fields && data.custom_fields.length > 0 && data.custom_fields.map((field, idx) => (
                        <tr key={`cf_${idx}`}>
                          <td className="cert-doc-label">{field.label}:</td>
                          <td className="cert-doc-value">{field.value}</td>
                        </tr>
                      ))}
                      <tr>
                        <td className="cert-doc-label">Hoạt động:</td>
                        <td className="cert-doc-value cert-doc-value--activity">{data.activity_title}</td>
                      </tr>
                      <tr>
                        <td className="cert-doc-label">Ngày tổ chức:</td>
                        <td className="cert-doc-value">{data.activity_date}</td>
                      </tr>
                      {(data.meeting_location || data.location_name) && (
                        <tr>
                          <td className="cert-doc-label">Địa điểm:</td>
                          <td className="cert-doc-value">{data.meeting_location || data.location_name}</td>
                        </tr>
                      )}
                      {data.group_name && (
                        <tr>
                          <td className="cert-doc-label">Đơn vị tổ chức:</td>
                          <td className="cert-doc-value">{data.group_name}</td>
                        </tr>
                      )}
                      {!data.is_host && (
                        <tr>
                          <td className="cert-doc-label">Người tổ chức:</td>
                          <td className="cert-doc-value">{data.host_name}</td>
                        </tr>
                      )}
                      {data.social_work_days !== null && data.social_work_days !== undefined && data.social_work_days > 0 && (
                        <tr>
                          <td className="cert-doc-label">Số ngày CTXH:</td>
                          <td className="cert-doc-value cert-doc-value--highlight">{formatCtxh(data.social_work_days)} ngày</td>
                        </tr>
                      )}
                      {data.trophy_name && (
                        <tr>
                          <td className="cert-doc-label">Danh hiệu:</td>
                          <td className="cert-doc-value">{data.trophy_icon || '🏆'} {data.trophy_name} (+{data.trophy_points} điểm)</td>
                        </tr>
                      )}
                    </tbody>
                  </table>

                  <p className="cert-doc-confirm">
                    {data.is_host
                      ? 'Xác nhận sinh viên nêu trên là người tổ chức và đã hoàn thành hoạt động trên nền tảng UniConnect.'
                      : 'Xác nhận sinh viên nêu trên đã tham gia và hoàn thành hoạt động trên nền tảng UniConnect.'}
                  </p>
                </div>

                {/* Footer */}
                <div className="cert-doc-footer">
                  <div className="cert-doc-qr-section">
                    <img
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(verifyUrl)}`}
                      alt="QR"
                      className="cert-doc-qr"
                      crossOrigin="anonymous"
                    />
                    <div className="cert-doc-code-info">
                      <span className="cert-doc-code-label">Mã xác minh</span>
                      <strong className="cert-doc-code-val">{data.certificate_code}</strong>
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
