import React from 'react';
import './PageShimmerLoading.css';

interface PageShimmerLoadingProps {
  title?: string;
  cardCount?: number;
}

export const PageShimmerLoading: React.FC<PageShimmerLoadingProps> = ({
  title,
  cardCount = 3,
}) => {
  return (
    <div className="page-shimmer-container" role="status" aria-label="Đang tải trang...">
      {/* Top Banner / Header Shimmer */}
      <div className="shimmer-header">
        <div className="shimmer-block shimmer-title" />
        <div className="shimmer-block shimmer-subtitle" />
      </div>

      {title && <span className="sr-only">{title}</span>}

      {/* Grid of Content Card Shimmers */}
      <div className="shimmer-grid">
        {Array.from({ length: cardCount }).map((_, idx) => (
          <div key={idx} className="shimmer-card">
            <div className="shimmer-block shimmer-card-media" />
            <div className="shimmer-card-body">
              <div className="shimmer-block shimmer-line shimmer-line-lg" />
              <div className="shimmer-block shimmer-line shimmer-line-md" />
              <div className="shimmer-block shimmer-line shimmer-line-sm" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PageShimmerLoading;
