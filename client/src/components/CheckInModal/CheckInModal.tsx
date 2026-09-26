import React, { useState, useEffect, useCallback } from 'react';
import {
  MapPin,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  X,
  Trophy,
  Navigation,
  Radio,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { activitiesApi } from '../../api/activities';
import type { CheckInState } from '../../types/activity-states';
import Button from '../Button/Button';
import './CheckInModal.css';

interface CheckInModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  activityId: string;
  activityTitle: string;
  checkInRadius: number;
  trophyName?: string;
  trophyPoints?: number;
}

export const CheckInModal: React.FC<CheckInModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  activityId,
  activityTitle,
  checkInRadius,
  trophyName,
  trophyPoints,
}) => {
  const [state, setState] = useState<CheckInState>('idle');
  const [code, setCode] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [accuracyMeasured, setAccuracyMeasured] = useState<number | null>(null);
  const [distanceMeasured, setDistanceMeasured] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      setState('idle');
      setCode('');
      setErrorMessage(null);
      setAccuracyMeasured(null);
      setDistanceMeasured(null);
    }
  }, [isOpen]);

  const handleStartCheckIn = useCallback(
    async (codeToSubmit?: string) => {
      const activeCode = (codeToSubmit ?? code).trim().toUpperCase();
      if (!activeCode) {
        setErrorMessage('Vui lòng nhập mã điểm danh.');
        return;
      }

      setErrorMessage(null);

      if (!navigator.geolocation) {
        setState('location_unavailable');
        setErrorMessage('Trình duyệt của bạn không hỗ trợ định vị vị trí GPS.');
        return;
      }

      setState('requesting_location');

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          setAccuracyMeasured(Math.round(accuracy));

          // Guardrail: Client-side accuracy validation threshold (100m)
          if (accuracy > 100) {
            setState('gps_accuracy_low');
            setErrorMessage(
              `Độ chính xác GPS hiện tại quá thấp (sai số ~${Math.round(accuracy)}m > 100m). Vui lòng di chuyển ra nơi thoáng đãng hoặc bật định vị chính xác cao.`
            );
            return;
          }

          // Transition to validating
          setState('validating');

          try {
            const res = await activitiesApi.checkIn(activityId, {
              code: activeCode,
              latitude,
              longitude,
              accuracy,
            });

            if (res.already_confirmed) {
              setState('already_confirmed');
              onSuccess();
              return;
            }

            setState('success');
            onSuccess();
          } catch (err: any) {
            const detail: string = err.response?.data?.detail || err.message || '';

            if (detail.includes('bán kính') || detail.includes('cách địa điểm')) {
              setState('outside_radius');
              const match = detail.match(/khoảng\s*(\d+)m/);
              if (match && match[1]) {
                setDistanceMeasured(parseInt(match[1], 10));
              }
              setErrorMessage(detail);
            } else if (detail.includes('100m') || detail.includes('độ chính xác')) {
              setState('gps_accuracy_low');
              setErrorMessage(detail);
            } else if (detail.includes('Phiên điểm danh')) {
              setState('session_closed');
              setErrorMessage(detail);
            } else if (detail.includes('đã được điểm danh')) {
              setState('already_confirmed');
              onSuccess();
            } else {
              setState('network_error');
              setErrorMessage(detail || 'Không thể kết nối máy chủ để xác thực điểm danh.');
            }
          }
        },
        (error) => {
          if (error.code === error.PERMISSION_DENIED) {
            setState('location_denied');
            setErrorMessage('Bạn đã từ chối quyền truy cập vị trí trên trình duyệt.');
          } else if (error.code === error.POSITION_UNAVAILABLE) {
            setState('location_unavailable');
            setErrorMessage('Không thể thu nhận tín hiệu GPS. Vui lòng bật định vị trên thiết bị.');
          } else {
            setState('gps_accuracy_low');
            setErrorMessage('Quá thời gian lấy vị trí GPS. Vui lòng thử lại ở nơi có tín hiệu tốt hơn.');
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 5000,
        }
      );
    },
    [activityId, code, onSuccess]
  );

  if (!isOpen) return null;

  return (
    <div
      className="checkin-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkin-modal-title"
    >
      <div className="checkin-modal-card">
        {/* Header */}
        <div className="checkin-modal-header">
          <h3 id="checkin-modal-title" className="checkin-modal-title">
            <Radio size={20} className="text-indigo-600" />
            Điểm danh sự kiện
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="checkin-modal-close"
            aria-label="Đóng hộp thoại điểm danh"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="checkin-modal-body">
          {/* STATE: IDLE */}
          {state === 'idle' && (
            <>
              <div className="text-xs text-[var(--color-text-secondary)]">
                Nhập mã 6 ký tự hiển thị trên màn hình Host và xác nhận vị trí trong bán kính{' '}
                <strong>{checkInRadius}m</strong>.
              </div>

              {errorMessage && (
                <div className="checkin-banner checkin-banner--error" role="alert">
                  <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                  <div>{errorMessage}</div>
                </div>
              )}

              <div className="checkin-code-input-group">
                <label htmlFor="checkin-code-input" className="checkin-code-input-label">
                  Mã điểm danh:
                </label>
                <input
                  id="checkin-code-input"
                  type="text"
                  className="checkin-code-input"
                  placeholder="VD: 8F2A1C"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  maxLength={10}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleStartCheckIn();
                    }
                  }}
                />
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Hủy
                </Button>
                <Button
                  variant="primary"
                  fullWidth
                  onClick={() => handleStartCheckIn()}
                  disabled={!code.trim()}
                >
                  <Navigation size={16} className="inline mr-1.5" />
                  Xác nhận có mặt
                </Button>
              </div>
            </>
          )}

          {/* STATE: REQUESTING_LOCATION */}
          {state === 'requesting_location' && (
            <div className="checkin-radar-box">
              <div className="checkin-radar-ripple" />
              <div className="checkin-radar-ripple" />
              <div className="checkin-radar-ripple" />
              <div className="checkin-radar-center">
                <Navigation size={30} />
              </div>
              <div className="checkin-radar-text">Đang thu nhận vị trí GPS vệ tinh...</div>
              <div className="checkin-radar-hint">
                Vui lòng nhấn "Cho phép" (Allow) nếu trình duyệt yêu cầu quyền truy cập vị trí.
              </div>
            </div>
          )}

          {/* STATE: VALIDATING */}
          {state === 'validating' && (
            <div className="checkin-radar-box">
              <div className="checkin-radar-center">
                <ShieldCheck size={32} />
              </div>
              <div className="checkin-radar-text">Máy chủ đang đối soát khoảng cách...</div>
              <div className="checkin-radar-hint">
                Xác thực Haversine trong bán kính {checkInRadius}m & kiểm tra mã bảo mật.
              </div>
            </div>
          )}

          {/* STATE: LOCATION_DENIED */}
          {state === 'location_denied' && (
            <>
              <div className="checkin-banner checkin-banner--error" role="alert">
                <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Quyền vị trí bị từ chối:</strong>
                  <p className="mt-1">
                    Trình duyệt chưa được cấp quyền định vị. Vui lòng bấm vào biểu tượng ổ khóa 🔒 trên thanh địa chỉ, bật quyền <strong>Vị trí (Location)</strong> và bấm Thử lại.
                  </p>
                </div>
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Đóng
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleStartCheckIn()}>
                  <RefreshCw size={16} className="inline mr-1.5" />
                  Thử lại
                </Button>
              </div>
            </>
          )}

          {/* STATE: LOCATION_UNAVAILABLE */}
          {state === 'location_unavailable' && (
            <>
              <div className="checkin-banner checkin-banner--warning" role="alert">
                <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Không bắt được tín hiệu GPS:</strong>
                  <p className="mt-1">{errorMessage || 'Vui lòng kiểm tra lại dịch vụ định vị trên thiết bị.'}</p>
                </div>
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Đóng
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleStartCheckIn()}>
                  <RefreshCw size={16} className="inline mr-1.5" />
                  Thử lại
                </Button>
              </div>
            </>
          )}

          {/* STATE: GPS_ACCURACY_LOW */}
          {state === 'gps_accuracy_low' && (
            <>
              <div className="checkin-banner checkin-banner--warning" role="alert">
                <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Độ chính xác GPS quá thấp:</strong>
                  <p className="mt-1">
                    {errorMessage ||
                      `Sai số đo lường (${accuracyMeasured ? `${accuracyMeasured}m` : 'lớn'} > 100m) không đủ tin cậy để xác nhận có mặt.`}
                  </p>
                  <p className="mt-1 text-xs opacity-90">
                    💡 <em>Gợi ý:</em> Di chuyển ra gần cửa sổ hoặc ngoài trời, bật Wi-Fi để hỗ trợ định vị chính xác hơn.
                  </p>
                </div>
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Đóng
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleStartCheckIn()}>
                  <RefreshCw size={16} className="inline mr-1.5" />
                  Đo lại vị trí
                </Button>
              </div>
            </>
          )}

          {/* STATE: OUTSIDE_RADIUS */}
          {state === 'outside_radius' && (
            <>
              <div className="checkin-banner checkin-banner--error" role="alert">
                <MapPin size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Bạn đang ở ngoài khu vực tổ chức:</strong>
                  <p className="mt-1">
                    Khoảng cách hiện tại {distanceMeasured ? `khoảng ${distanceMeasured}m` : 'xa'}, vượt quá bán kính cho phép{' '}
                    <strong>{checkInRadius}m</strong> của sự kiện "{activityTitle}".
                  </p>
                </div>
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Đóng
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleStartCheckIn()}>
                  <RefreshCw size={16} className="inline mr-1.5" />
                  Kiểm tra lại vị trí
                </Button>
              </div>
            </>
          )}

          {/* STATE: SESSION_CLOSED */}
          {state === 'session_closed' && (
            <>
              <div className="checkin-banner checkin-banner--warning" role="alert">
                <Clock size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Phiên điểm danh chưa mở hoặc đã kết thúc:</strong>
                  <p className="mt-1">{errorMessage}</p>
                </div>
              </div>

              <Button variant="secondary" fullWidth onClick={onClose}>
                Đóng
              </Button>
            </>
          )}

          {/* STATE: ALREADY_CONFIRMED */}
          {state === 'already_confirmed' && (
            <div className="checkin-success-box">
              <div className="checkin-success-icon">
                <CheckCircle2 size={36} />
              </div>
              <h4 className="checkin-success-title">Bạn đã được điểm danh!</h4>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Hệ thống xác nhận trạng thái có mặt của bạn đã được ghi nhận thành công từ trước.
              </p>
              <Button variant="primary" fullWidth onClick={onClose} className="mt-2">
                Hoàn tất
              </Button>
            </div>
          )}

          {/* STATE: NETWORK_ERROR */}
          {state === 'network_error' && (
            <>
              <div className="checkin-banner checkin-banner--error" role="alert">
                <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Lỗi xác thực:</strong>
                  <p className="mt-1">{errorMessage || 'Không thể kết nối máy chủ.'}</p>
                </div>
              </div>

              <div className="checkin-modal-actions">
                <Button variant="secondary" fullWidth onClick={onClose}>
                  Đóng
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleStartCheckIn()}>
                  <RefreshCw size={16} className="inline mr-1.5" />
                  Thử gửi lại
                </Button>
              </div>
            </>
          )}

          {/* STATE: SUCCESS */}
          {state === 'success' && (
            <div className="checkin-success-box">
              <div className="checkin-success-icon">
                <CheckCircle2 size={36} />
              </div>
              <h4 className="checkin-success-title">Điểm danh thành công!</h4>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Đã xác nhận sự hiện diện của bạn tại sự kiện.
              </p>
              {trophyName && (
                <div className="checkin-success-trophy">
                  <Trophy size={16} />
                  <span>
                    Đã nhận danh hiệu: <strong>{trophyName}</strong> (+{trophyPoints || 0} điểm)
                  </span>
                </div>
              )}
              <Button variant="primary" fullWidth onClick={onClose} className="mt-2">
                Xem minh chứng / Đóng
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
