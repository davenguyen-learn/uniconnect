import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/Button/Button';
import './Landing.css';

const FEATURES = [
  {
    icon: '📍',
    title: 'Discover Nearby',
    description:
      'Find activities happening around you with real-time map discovery. Filter by category, distance, and availability.',
  },
  {
    icon: '⚡',
    title: 'Create Instantly',
    description:
      'Organize study sessions, sports matches, or social meetups in seconds. Set location, time, and capacity with a tap.',
  },
  {
    icon: '🤝',
    title: 'Connect & Join',
    description:
      'Request to join activities that interest you. Hosts approve participants to build the right group for every occasion.',
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
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link to="/register">
            <Button variant="primary" size="sm">Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-badge">
          <span className="landing-badge-dot" />
          Built for university communities
        </div>
        <h1>
          Discover what's happening{' '}
          <span className="gradient-text">around campus</span>
        </h1>
        <p className="landing-hero-sub">
          Find and join study groups, sports matches, and social events near you.
          Create your own activities and build your campus network.
        </p>
        <div className="landing-hero-actions">
          <Link to="/register">
            <Button variant="primary" size="lg">
              Start Exploring
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" size="lg">
              I have an account
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="landing-features">
        <div className="landing-features-header">
          <h2>Everything you need to connect</h2>
          <p>
            Simple, fast, and designed for campus life.
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
          <h2>Ready to connect?</h2>
          <p>Join your campus community in under a minute.</p>
          <Link to="/register">
            <Button variant="primary" size="lg">
              Create your account
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© {new Date().getFullYear()} UniConnect. A student project exploring location-aware social discovery.</p>
      </footer>
    </div>
  );
}
