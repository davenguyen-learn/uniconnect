import React from 'react';
import Input from '../Input/Input';
import './CollectionLayout.css';

export interface CollectionTab {
  id: string;
  label: string;
  count?: number;
}

export interface SortOption {
  label: string;
  value: string;
}

export interface CollectionLayoutProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;

  // Tabs
  tabs?: CollectionTab[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;

  // Search & Sort Controls
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (value: string) => void;

  sortOptions?: SortOption[];
  sortValue?: string;
  onSortChange?: (value: string) => void;

  extraFilters?: React.ReactNode;

  // Loading & Empty States
  loading?: boolean;
  loadingMessage?: string;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;

  children: React.ReactNode;
}

export default function CollectionLayout({
  title,
  subtitle,
  action,
  tabs,
  activeTab,
  onTabChange,
  searchPlaceholder = 'Tìm kiếm...',
  searchValue,
  onSearchChange,
  sortOptions,
  sortValue,
  onSortChange,
  extraFilters,
  loading = false,
  loadingMessage = 'Đang tải...',
  isEmpty = false,
  emptyTitle = 'Không tìm thấy dữ liệu',
  emptyMessage = 'Thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm.',
  emptyAction,
  children,
}: CollectionLayoutProps) {
  const showControls = Boolean(onSearchChange || sortOptions || extraFilters);

  return (
    <div className="container collection-page">
      {/* Header */}
      <div className="collection-header">
        <div className="collection-title-wrap">
          <h1 className="brutalist-highlight">{title}</h1>
          {subtitle && <p className="collection-subtitle">{subtitle}</p>}
        </div>
        {action && <div className="collection-action">{action}</div>}
      </div>

      {/* Navigation Tabs */}
      {tabs && tabs.length > 0 && (
        <div className="collection-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`collection-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange?.(tab.id)}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          ))}
        </div>
      )}

      {/* Search & Filter Controls */}
      {showControls && (
        <div className="collection-controls glass">
          {onSearchChange && (
            <div className="collection-search">
              <Input
                placeholder={searchPlaceholder}
                value={searchValue || ''}
                onChange={(e) => onSearchChange(e.target.value)}
              />
            </div>
          )}

          {extraFilters}

          {sortOptions && sortOptions.length > 0 && onSortChange && (
            <div className="collection-sort-group">
              <span className="collection-sort-label">Sắp xếp:</span>
              <select
                className="form-select"
                value={sortValue}
                onChange={(e) => onSortChange(e.target.value)}
              >
                {sortOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Grid / Content Area */}
      {loading ? (
        <div className="collection-loading">{loadingMessage}</div>
      ) : isEmpty ? (
        <div className="collection-empty glass">
          <h3>{emptyTitle}</h3>
          <p>{emptyMessage}</p>
          {emptyAction && <div className="collection-empty-action">{emptyAction}</div>}
        </div>
      ) : (
        <div className="collection-grid">{children}</div>
      )}
    </div>
  );
}
