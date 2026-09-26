import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { LeftSidebar } from './LeftSidebar';
import { BottomNav } from './BottomNav';
import { TopBar } from './TopBar';
import './AppShell.css';

export const AppShell: React.FC = () => {
  // Check responsive breakpoints
  const [windowWidth, setWindowWidth] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth : 1280
  );

  // Read saved sidebar collapse preference
  const [userCollapsedPref, setUserCollapsedPref] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('unic_sidebar_collapsed') === 'true';
    }
    return false;
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isMobile = windowWidth < 768;
  const isTablet = windowWidth >= 768 && windowWidth < 1280;

  // If on tablet, automatically collapse to rail; on desktop respect user preference
  const isSidebarCollapsed = isTablet || userCollapsedPref;

  const handleToggleCollapse = () => {
    const nextVal = !isSidebarCollapsed;
    setUserCollapsedPref(nextVal);
    localStorage.setItem('unic_sidebar_collapsed', String(nextVal));
  };

  return (
    <div className="app-shell">
      {/* Left Sidebar on Desktop & Tablet */}
      {!isMobile && (
        <LeftSidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={handleToggleCollapse}
        />
      )}

      {/* Main App Container */}
      <div className="app-shell__body">
        <TopBar isMobile={isMobile} />
        <main className="app-shell__main" id="main-content">
          <Outlet />
        </main>
      </div>

      {/* Bottom Nav on Mobile (< 768px) */}
      {isMobile && <BottomNav />}
    </div>
  );
};

export default AppShell;
