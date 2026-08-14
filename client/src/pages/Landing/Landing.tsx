import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/Button/Button';
import './Landing.css';

const FEATURES = [
  {
    icon: '📍',
    title: 'Khám phá xung quanh',
    description:
      'Tìm kiếm các hoạt động đang diễn ra xung quanh bạn trên bản đồ theo thời gian thực. Lọc theo danh mục, khoảng cách và thời gian.',
  },
  {
    icon: '⚡',
    title: 'Tạo hoạt động nhanh chóng',
    description:
      'Tổ chức các buổi học nhóm, trận đấu thể thao, hoặc giao lưu chỉ trong vài giây. Thiết lập địa điểm, thời gian và số lượng người chỉ với vài thao tác.',
  },
  {
    icon: '🤝',
    title: 'Kết nối & Tham gia',
    description:
      'Yêu cầu tham gia các hoạt động mà bạn quan tâm. Người tổ chức sẽ duyệt người tham gia để tạo nhóm phù hợp nhất.',
  },
];

export default function Landing() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="landing">
      {/* Navigation */}
      <nav className={`landing-nav ${scrolled ? 'scrolled' : ''}`}>
        <Link to="/" className="landing-logo">
          <span className="landing-logo-icon">U</span>
          UniConnect
        </Link>
        <div className="landing-nav-links">
          <Link to="/login">
            <Button variant="ghost" size="sm">Đăng nhập</Button>
          </Link>
          <Link to="/register">
            <Button variant="primary" size="sm">Bắt đầu</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-badge">
          <span className="landing-badge-dot" />
          Dành riêng cho cộng đồng sinh viên
        </div>
        <h1>
          Khám phá những điều thú vị{' '}
          <span className="brutalist-highlight">xung quanh trường học</span>
        </h1>
        <p className="landing-hero-sub">
          Tìm và tham gia các nhóm học tập, trận thể thao, và sự kiện xã hội gần bạn.
          Tạo hoạt động riêng và xây dựng mạng lưới quan hệ trong trường.
        </p>
        <div className="landing-hero-actions">
          <Link to="/register">
            <Button variant="primary" size="lg">
              Bắt đầu khám phá
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" size="lg">
              Tôi đã có tài khoản
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="landing-features">
        <div className="landing-features-header">
          <h2>Mọi thứ bạn cần để kết nối</h2>
          <p>
            Đơn giản, nhanh chóng, và được thiết kế cho cuộc sống sinh viên.
          </p>
        </div>
        <div className="landing-features-grid">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="landing-feature-card">
              <div className="landing-feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="landing-cta">
        <div className="landing-cta-inner">
          <h2>Bạn đã sẵn sàng kết nối?</h2>
          <p>Tham gia cộng đồng sinh viên trong chưa đầy một phút.</p>
          <Link to="/register">
            <Button variant="primary" size="lg">
              Tạo tài khoản
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© {new Date().getFullYear()} UniConnect. Một dự án sinh viên nhằm khám phá cộng đồng qua mạng lưới vị trí.</p>
      </footer>
    </div>
  );
}
