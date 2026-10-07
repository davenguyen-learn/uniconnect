import './Badge.css';

export interface BadgeProps {
  /** The text displayed inside the badge */
  text: string;
  /** Background color (CSS color string or CSS variable) */
  bg?: string;
  /** Optional extra class name */
  className?: string;
  /** Optional hover tooltip */
  title?: string;
  /** Optional click handler */
  onClick?: () => void;
}

/**
 * Standard Unified Badge Component
 * Uniform padding, border-radius, font-size, line-height.
 * Always white text, no icons, configurable text & background color.
 */
export default function Badge({
  text,
  bg = 'var(--color-primary, #2563eb)',
  className = '',
  title,
  onClick,
}: BadgeProps) {
  return (
    <span
      className={`app-badge ${className}`}
      style={{ backgroundColor: bg }}
      title={title}
      onClick={onClick}
    >
      {text}
    </span>
  );
}
