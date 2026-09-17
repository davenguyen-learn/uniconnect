import { Component, ErrorInfo, ReactNode } from 'react';
import './ErrorBoundary.css';

// Standalone inline SVG icons to ensure ErrorBoundary has ZERO external dependencies
const AlertTriangleIcon = ({ size = 32 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const RefreshCwIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
    <path d="M21 3v5h-5" />
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
    <path d="M8 16H3v5" />
  </svg>
);

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  private handleReload = () => {
    // If chunk failed to load (e.g. after a deployment), reload clears cached script hashes
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      const isChunkError =
        this.state.error?.message?.includes('dynamically imported module') ||
        this.state.error?.message?.includes('Loading chunk') ||
        this.state.error?.name === 'ChunkLoadError';

      return (
        <div className="error-boundary-container" role="alert">
          <div className="error-boundary-card">
            <div className="error-icon-box">
              <AlertTriangleIcon size={32} />
            </div>
            <h2 className="error-boundary-title">
              {this.props.fallbackTitle || (isChunkError ? 'Đang cập nhật phiên bản mới' : 'Đã xảy ra sự cố')}
            </h2>
            <p className="error-boundary-desc">
              {isChunkError
                ? 'Hệ thống vừa cập nhật phiên bản mã nguồn mới. Vui lòng tải lại trang để áp dụng thay đổi.'
                : (this.state.error?.message || 'Có lỗi xảy ra khi hiển thị giao diện.')}
            </p>
            <div className="error-boundary-actions">
              <button
                type="button"
                className="btn-error-reload"
                onClick={this.handleReload}
              >
                <RefreshCwIcon size={16} />
                <span>Tải lại trang</span>
              </button>
              {!isChunkError && (
                <button
                  type="button"
                  className="btn-error-retry"
                  onClick={this.handleReset}
                >
                  Thử lại
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
