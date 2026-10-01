import React, { useEffect, useRef, useState } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { X, Loader2, AlertTriangle } from 'lucide-react';
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

interface CertField {
  label: string;
  value: React.ReactNode;
  className?: string;
  isName?: boolean;
}

export const formatTrophyTitle = (rawName?: string | null): string => {
  if (!rawName) return '';
  return rawName
    .replace(/[🏆🥇🥈🥉🏅🎖️\u{1F300}-\u{1F9FF}]/gu, '')
    .replace(/\s*\([^)]*\)/g, '')
    .trim();
};

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
  const [pageView, setPageView] = useState<'all' | 1 | 2>('all');
  const certContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && activityId) {
      setLoading(true);
      setError(null);
      setPageView('all');
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
    if (!data || downloading) return;
    setDownloading(true);

    const prevView = pageView;
    setPageView('all');

    try {
      // Allow DOM to update in case 'all' view wasn't selected
      await new Promise((resolve) => setTimeout(resolve, 80));

      const pageElements = certContainerRef.current?.querySelectorAll<HTMLElement>('.cert-page');
      if (!pageElements || pageElements.length === 0) return;

      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      for (let i = 0; i < pageElements.length; i++) {
        if (i > 0) {
          pdf.addPage();
        }

        const canvas = await html2canvas(pageElements[i], {
          scale: 2,
          useCORS: true,
          backgroundColor: '#ffffff',
          logging: false,
        });

        const imgData = canvas.toDataURL('image/png');
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      }

      const safeTitle = data.activity_title.replace(/[/\\?%*:|"<>]/g, '-').trim();
      const fileName = `Giấy xác nhận tham gia hoạt động ${safeTitle}.pdf`;
      pdf.save(fileName);
    } catch (err) {
      console.error('Lỗi khi tải file PDF:', err);
    } finally {
      setPageView(prevView);
      setDownloading(false);
    }
  };

  const verifyUrl = data
    ? `${window.location.origin}/verify-certificate?code=${encodeURIComponent(data.certificate_code)}`
    : '';

  // Prepare fields
  const participantFields: CertField[] = data
    ? [
        { label: 'Họ và tên:', value: data.participant_name, isName: true },
        ...(data.is_host
          ? [{ label: 'Vai trò:', value: 'Trưởng ban tổ chức (Host)', className: 'font-bold text-indigo-700' }]
          : []),
        ...(data.participant_email ? [{ label: 'Email:', value: data.participant_email }] : []),
        ...(data.participant_university ? [{ label: 'Đơn vị:', value: data.participant_university }] : []),
        ...(data.custom_fields || []).map((field) => ({
          label: `${field.label}:`,
          value: field.value,
        })),
      ]
    : [];

  const cleanedTrophy = data?.trophy_name ? formatTrophyTitle(data.trophy_name) : '';

  const activityFields: CertField[] = data
    ? [
        { label: 'Hoạt động:', value: data.activity_title, className: 'cert-doc-value--activity' },
        { label: 'Ngày tổ chức:', value: data.activity_date },
        ...((data.meeting_location || data.location_name)
          ? [{ label: 'Địa điểm:', value: data.meeting_location || data.location_name }]
          : []),
        ...(data.group_name ? [{ label: 'Đơn vị tổ chức:', value: data.group_name }] : []),
        ...(!data.is_host ? [{ label: 'Người tổ chức:', value: data.host_name }] : []),
        ...(data.social_work_days !== null && data.social_work_days !== undefined && data.social_work_days > 0
          ? [
              {
                label: 'Số ngày CTXH:',
                value: `${formatCtxh(data.social_work_days)} ngày`,
                className: 'cert-doc-value--highlight',
              },
            ]
          : []),
        ...(cleanedTrophy
          ? [{ label: 'Danh hiệu:', value: cleanedTrophy, className: 'cert-doc-value--highlight' }]
          : []),
      ]
    : [];

  // Determine pagination: if custom fields >= 2 or total items > 9
  const isPaginated =
    Boolean(data) &&
    ((participantFields.length + activityFields.length > 9) ||
      Boolean(data?.custom_fields && data.custom_fields.length >= 2));
  const totalPages = isPaginated ? 2 : 1;

  const renderHeader = (isContinuation = false) => (
    <div className="cert-doc-header">
      <div className="cert-doc-org">NỀN TẢNG KẾT NỐI HOẠT ĐỘNG SINH VIÊN</div>
      <div className="cert-doc-platform">UNICONNECT</div>
      <div className="cert-doc-line" />
      <h1 className="cert-doc-title">
        {data?.is_host ? 'GIẤY XÁC NHẬN TỔ CHỨC HOẠT ĐỘNG' : 'GIẤY XÁC NHẬN THAM GIA HOẠT ĐỘNG'}
        {isContinuation && ' (TIẾP THEO)'}
      </h1>
    </div>
  );

  const renderFieldRows = (fields: CertField[]) => (
    <div className="cert-doc-fields">
      {fields.map((field, idx) => (
        <div key={idx} className="cert-doc-row">
          <span className="cert-doc-label">{field.label}</span>
          <span
            className={`cert-doc-value ${field.isName ? 'cert-doc-value--name' : ''} ${
              field.className || ''
            }`}
          >
            {field.value}
          </span>
        </div>
      ))}
    </div>
  );

  const renderConfirmText = () => (
    <p className="cert-doc-confirm">
      {data?.is_host
        ? 'Xác nhận sinh viên nêu trên là người tổ chức và đã hoàn thành hoạt động trên nền tảng UniConnect.'
        : 'Xác nhận sinh viên nêu trên đã tham gia và hoàn thành hoạt động trên nền tảng UniConnect.'}
    </p>
  );

  const renderQrFooter = () => (
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
          <strong className="cert-doc-code-val">{data?.certificate_code}</strong>
        </div>
      </div>
    </div>
  );

  return (
    <div className="certificate-modal-overlay animate-fade-in">
      <div className="certificate-modal-container">
        <div className="certificate-modal-header no-print">
          <div className="flex items-center gap-3">
            <h2 className="cert-modal-title">Giấy xác nhận tham gia hoạt động</h2>
            {totalPages > 1 && (
              <div className="cert-page-selector">
                <button
                  type="button"
                  className={`cert-page-tab-btn ${pageView === 'all' ? 'active' : ''}`}
                  onClick={() => setPageView('all')}
                  title="Hiển thị tất cả các trang"
                >
                  Tất cả ({totalPages} trang)
                </button>
                <button
                  type="button"
                  className={`cert-page-tab-btn ${pageView === 1 ? 'active' : ''}`}
                  onClick={() => setPageView(1)}
                  title="Xem trang 1"
                >
                  Trang 1
                </button>
                <button
                  type="button"
                  className={`cert-page-tab-btn ${pageView === 2 ? 'active' : ''}`}
                  onClick={() => setPageView(2)}
                  title="Xem trang 2"
                >
                  Trang 2
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {data && (
              <Button size="sm" variant="primary" onClick={handleDownload} disabled={downloading}>
                {downloading ? 'Đang tạo PDF...' : 'Tải PDF'}
              </Button>
            )}
            <button className="certificate-modal-close" onClick={onClose} aria-label="Đóng">
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="certificate-modal-body">
          {loading && (
            <div className="certificate-loading py-16 text-center text-[var(--color-text-secondary)]">
              <Loader2 size={28} className="animate-spin mb-2 mx-auto text-indigo-600" />
              <p>Đang tải...</p>
            </div>
          )}

          {error && (
            <div className="certificate-error py-12 text-center">
              <AlertTriangle size={36} className="mb-2 mx-auto text-amber-500" />
              <p className="text-red-500 font-medium mb-4">{error}</p>
              <Button variant="secondary" onClick={onClose}>
                Đóng
              </Button>
            </div>
          )}

          {data && !loading && !error && (
            <div className="certificate-printable-wrapper" ref={certContainerRef}>
              {!isPaginated ? (
                /* SINGLE PAGE CERTIFICATE */
                <div className="cert-page">
                  <div className="cert-page-top">
                    {renderHeader(false)}
                    <div className="cert-doc-body">
                      {renderFieldRows([...participantFields, ...activityFields])}
                      {renderConfirmText()}
                    </div>
                  </div>
                  <div className="cert-page-bottom">
                    {renderQrFooter()}
                    <div className="cert-page-number">Trang 1/1</div>
                  </div>
                </div>
              ) : (
                /* MULTI-PAGE CERTIFICATE */
                <div className="cert-pages-list">
                  {/* PAGE 1 */}
                  {(pageView === 'all' || pageView === 1) && (
                    <div className="cert-page">
                      <div className="cert-page-top">
                        {renderHeader(false)}
                        <div className="cert-section-header">
                          {data.is_host ? 'THÔNG TIN NGƯỜI TỔ CHỨC' : 'THÔNG TIN SINH VIÊN'}
                        </div>
                        <div className="cert-doc-body">
                          {renderFieldRows(participantFields)}
                        </div>
                      </div>
                      <div className="cert-page-bottom">
                        <div className="cert-page-number">Trang 1/2</div>
                      </div>
                    </div>
                  )}

                  {/* PAGE 2 */}
                  {(pageView === 'all' || pageView === 2) && (
                    <div className="cert-page">
                      <div className="cert-page-top">
                        {renderHeader(true)}
                        <div className="cert-section-header">THÔNG TIN HOẠT ĐỘNG</div>
                        <div className="cert-doc-body">
                          {renderFieldRows(activityFields)}
                          {renderConfirmText()}
                        </div>
                      </div>
                      <div className="cert-page-bottom">
                        {renderQrFooter()}
                        <div className="cert-page-number">Trang 2/2</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
