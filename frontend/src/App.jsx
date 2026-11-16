import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import SearchOverlay from './components/SearchOverlay';
import ToastContainer from './components/Toast';
import ContactModal from './components/Modals/ContactModal';
import AuthModal from './components/Modals/AuthModal';
import SiteVisitModal from './components/Modals/SiteVisitModal';
import ShareModal from './components/Modals/ShareModal';

import HomeView from './views/HomeView';
import PropertiesView from './views/PropertiesView';
import PropertyDetailsView from './views/PropertyDetailsView';
import AuctionsView from './views/AuctionsView';
import ServicesView from './views/ServicesView';
import AboutView from './views/AboutView';
import DashboardView from './views/DashboardView';

const AdminView = React.lazy(() => import('./views/AdminView'));
const AdminLoginView = React.lazy(() => import('./views/AdminLoginView'));

import { INITIAL_PROPERTIES, formatPriceShort } from './data/propertiesData';
import {
  INITIAL_USER,
  INITIAL_BIDS,
  INITIAL_WISHLIST,
  INITIAL_NOTIFICATIONS,
  INITIAL_LEADS,
} from './data/initialUserData';
import {
  fetchLiveAuctions,
  submitLeadApi,
  verifyPropertyApi,
  triggerScrapeApi,
  flushOfflineLeads,
} from './data/api';
import { isSubdomainAdmin, isLocalDev } from './utils/domain';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [selectedPropertyId, setSelectedPropertyId] = useState('p1');
  const [dashTab, setDashTab] = useState('overview');
  const [adminActiveTab, setAdminActiveTab] = useState('verification');

  // Subdomain & Portal Mode Detection
  // e.g. admin.skandx.com, admin.localhost, ?portal=admin, or #admin
  const [isSubdomainMode, setIsSubdomainMode] = useState(() => isSubdomainAdmin());
  const [viewMode, setViewMode] = useState(() => (isSubdomainAdmin() ? 'admin' : 'customer'));

  // Admin Session Guard (persisted in sessionStorage)
  const [adminSession, setAdminSession] = useState(() => {
    try {
      const saved = sessionStorage.getItem('skandx_admin_session');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Properties data & live ingestion
  const [properties, setProperties] = useState(INITIAL_PROPERTIES);
  const [apiSource, setApiSource] = useState('INITIAL');

  // Buyer inquiries (Leads) captured via "Contact" button
  const [leads, setLeads] = useState(INITIAL_LEADS);

  // User state
  const [user, setUser] = useState(INITIAL_USER);
  const [myBids, setMyBids] = useState(INITIAL_BIDS);
  const [wishlist, setWishlist] = useState(INITIAL_WISHLIST);
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);

  // Filters for listings page
  const [filters, setFilters] = useState({
    location: '',
    types: ['residential', 'commercial', 'land', 'industrial'],
    minBudget: 0,
    maxBudget: 100000000, // 10 Cr
    banks: ['Canara Bank', 'SBI', 'ICICI Bank', 'Others'],
    sort: 'ending',
  });

  // Modals state
  const [searchOpen, setSearchOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState(null); // null | 'login' | 'register'
  const [contactTarget, setContactTarget] = useState(null);
  const [contactInitialType, setContactInitialType] = useState('Site Inspection');
  const [siteVisitTarget, setSiteVisitTarget] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);

  // Toast stack
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((title, message = '', type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Sync with live Supabase / local auctions server
  useEffect(() => {
    fetchLiveAuctions().then((res) => {
      if (res && res.properties) {
        setProperties(res.properties);
        setApiSource(res.source);
        if (res.source === 'SUPABASE_LIVE' || res.source === 'BACKEND_LIVE') {
          addToast('Connected to Live Auction Database', `Loaded ${res.properties.length} active bank listings.`, 'success');
        }
      }
    });
  }, [addToast]);

  // Listen for network reconnect & tab focus to flush offline leads
  useEffect(() => {
    const handleSync = () => {
      flushOfflineLeads();
    };
    window.addEventListener('online', handleSync);
    window.addEventListener('focus', handleSync);
    return () => {
      window.removeEventListener('online', handleSync);
      window.removeEventListener('focus', handleSync);
    };
  }, []);

  // Hash route & subdomain listener
  useEffect(() => {
    const handleUrlChange = () => {
      const isSubAdmin = isSubdomainAdmin();
      setIsSubdomainMode(isSubAdmin);
      if (isSubAdmin) {
        setViewMode('admin');
      }

      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('property/')) {
        const id = hash.split('/')[1];
        if (id) {
          setSelectedPropertyId(id);
          setActivePage('property');
        }
      } else if (['home', 'properties', 'auctions', 'services', 'about', 'dashboard'].includes(hash)) {
        setActivePage(hash);
      }
    };

    handleUrlChange();
    window.addEventListener('hashchange', handleUrlChange);
    window.addEventListener('popstate', handleUrlChange);
    return () => {
      window.removeEventListener('hashchange', handleUrlChange);
      window.removeEventListener('popstate', handleUrlChange);
    };
  }, []);

  // Update hash when active page changes
  const navigateTo = (page, propId = null) => {
    if (page === 'property' && propId) {
      setSelectedPropertyId(propId);
      window.location.hash = `property/${propId}`;
    } else {
      window.location.hash = page;
    }
    setActivePage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // View property details
  const handleViewProperty = (id) => {
    setSelectedPropertyId(id);
    navigateTo('property', id);
  };

  // Contact modal triggers
  const handleOpenContact = (property, inquiryType = 'Site Inspection') => {
    setContactTarget(property);
    setContactInitialType(inquiryType);
  };

  const handleSubmitContact = async (leadData) => {
    const newLead = {
      ...leadData,
      id: `lead-${Date.now()}`,
      time: 'Just now',
      status: 'NEW',
    };

    setLeads((prev) => [newLead, ...prev]);
    await submitLeadApi(leadData);

    addToast(
      'Inquiry Dispatched to Bank Desk!',
      `Our liaison officer will contact you regarding ${leadData.propertyTitle} within 15 minutes.`,
      'success'
    );
  };

  // Admin Actions
  const handleVerifyProperty = async (id, updatedFields = {}) => {
    const previousProperties = properties;
    setProperties((prev) =>
      prev.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            ...updatedFields,
            verified: true,
            status: 'PUBLISHED',
            verifiedDate: 'Just now',
          };
        }
        return p;
      })
    );

    try {
      await verifyPropertyApi(id, 'PUBLISHED', updatedFields);
      addToast(
        'Listing Verified & Published!',
        'Asset is now visible to customers on the public marketplace with the green Verified badge.',
        'success'
      );
    } catch (err) {
      setProperties(previousProperties);
      addToast(
        'Verification Failed',
        err.status === 401
          ? 'Admin session expired or unauthorized. Please log in again.'
          : (err.message || 'Failed to verify property on server.'),
        'error'
      );
      if (err.status === 401) {
        handleAdminLogout();
      }
    }
  };

  const handleRejectProperty = async (id) => {
    const previousProperties = properties;
    setProperties((prev) =>
      prev.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            verified: false,
            status: 'REJECTED',
          };
        }
        return p;
      })
    );

    try {
      await verifyPropertyApi(id, 'REJECTED');
      addToast(
        'Listing Rejected',
        'The property notice has been removed from the public pipeline.',
        'info'
      );
    } catch (err) {
      setProperties(previousProperties);
      addToast(
        'Rejection Failed',
        err.status === 401
          ? 'Admin session expired or unauthorized. Please log in again.'
          : (err.message || 'Failed to reject property on server.'),
        'error'
      );
      if (err.status === 401) {
        handleAdminLogout();
      }
    }
  };

  const handleTriggerScrape = async () => {
    addToast(
      'Scraper Pipeline Triggered',
      'Bank portal crawlers and Gemini 2.5 Flash OCR are processing raw notices.',
      'info'
    );
    await triggerScrapeApi();
  };

  const handleUpdateLeadStatus = (leadId, newStatus) => {
    setLeads((prev) =>
      prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l))
    );
    addToast('Lead Status Updated', `Inquiry status changed to ${newStatus}.`, 'info');
  };

  const handleAdminLogout = () => {
    sessionStorage.removeItem('skandx_admin_session');
    setAdminSession(null);
    addToast('Admin Logged Out', 'Your back-office session has been safely closed.', 'info');
  };

  // Wishlist toggle
  const handleToggleWishlist = (id) => {
    setWishlist((prev) => {
      const isSaved = prev.includes(id);
      const target = properties.find((p) => p.id === id);
      const name = target ? target.title : 'Property';

      if (isSaved) {
        addToast('Removed from Watchlist', `${name} removed from your tracked auctions.`, 'info');
        return prev.filter((item) => item !== id);
      } else {
        addToast('Added to Watchlist', `${name} added to your tracked auctions.`, 'success');
        return [...prev, id];
      }
    });
  };

  // Global search execution
  const handleGlobalSearch = (query) => {
    setFilters((prev) => ({ ...prev, location: query }));
    setViewMode('customer');
    navigateTo('properties');
  };

  // Quick search from hero panel
  const handleApplyQuickSearch = ({ locality, type, budget }) => {
    let minBudget = 0;
    let maxBudget = 100000000;
    if (budget === 'under50') {
      minBudget = 0;
      maxBudget = 5000000;
    } else if (budget === '50to1cr') {
      minBudget = 5000000;
      maxBudget = 10000000;
    } else if (budget === '1crto2cr') {
      minBudget = 10000000;
      maxBudget = 20000000;
    } else if (budget === 'above2cr') {
      minBudget = 20000000;
      maxBudget = 1000000000;
    }

    setFilters((prev) => ({
      ...prev,
      location: locality,
      types: type === 'all' ? ['residential', 'commercial', 'land', 'industrial'] : [type],
      minBudget,
      maxBudget,
    }));
  };

  const handleDownloadBrochure = (property) => {
    handleOpenContact(property, 'Download Notice');
  };

  const handleViewDocuments = (property) => {
    handleOpenContact(property, 'Legal Title Search Report');
  };

  const handleScheduleSiteVisit = (property) => {
    handleOpenContact(property, 'Site Inspection');
  };

  const currentProperty =
    properties.find((p) => p.id === selectedPropertyId) || properties[0];

  const pendingCount = properties.filter((p) => p.status === 'PENDING_REVIEW' || !p.verified).length;

  const isAdminPortal = isSubdomainMode || viewMode === 'admin';

  // If in Admin Subdomain/View and not authenticated, render the Admin Login Gateway
  if (isAdminPortal && !adminSession) {
    return (
      <div className="app-root">
        <React.Suspense
          fallback={
            <div
              className="view-loading"
              style={{
                minHeight: '60vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#94A3B8',
              }}
            >
              Loading Admin Desk...
            </div>
          }
        >
          <AdminLoginView
            onLoginSuccess={(tokenOrSession, maybeUser) => {
              const session =
                typeof tokenOrSession === 'string'
                  ? {
                      token: tokenOrSession,
                      name: maybeUser?.name || 'Chief Auction Officer',
                      email: maybeUser?.email || 'admin@skandx.com',
                      role: maybeUser?.role || 'SUPER_ADMIN',
                      loginTime: Date.now(),
                    }
                  : tokenOrSession;
              sessionStorage.setItem('skandx_admin_session', JSON.stringify(session));
              setAdminSession(session);
              addToast('Admin Authenticated', `Welcome back, ${session.name || 'Admin'}.`, 'success');
            }}
            onReturnToCustomer={() => {
              setViewMode('customer');
              setIsSubdomainMode(false);
              window.location.hash = '';
            }}
          />
        </React.Suspense>
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </div>
    );
  }

  return (
    <div className="app-root">
      {/* Global Header (Adapts dynamically between Customer and Admin domains) */}
      <Header
        activePage={activePage}
        setActivePage={(page) => navigateTo(page)}
        onOpenSearch={() => setSearchOpen(true)}
        user={user}
        onOpenAuth={(mode) => setAuthModalMode(mode)}
        notifications={notifications}
        onMarkAllRead={() => {
          setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
          addToast('Notifications Updated', 'All alerts marked as read.', 'info');
        }}
        viewMode={viewMode}
        onSetViewMode={(mode) => {
          setViewMode(mode);
          if (mode === 'admin') window.location.hash = 'admin';
          else if (window.location.hash === '#admin') window.location.hash = '';
        }}
        pendingCount={pendingCount}
        isAdminPortal={isAdminPortal}
        adminSession={adminSession}
        onAdminLogout={handleAdminLogout}
        showDevSwitcher={isLocalDev()}
        adminActiveTab={adminActiveTab}
        onSetAdminTab={setAdminActiveTab}
      />

      {/* Main View Router */}
      <main id="main">
        {isAdminPortal ? (
          <React.Suspense
            fallback={
              <div
                className="view-loading"
                style={{
                  minHeight: '60vh',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#94A3B8',
                }}
              >
                Loading Admin Desk...
              </div>
            }
          >
            <AdminView
              properties={properties}
              leads={leads}
              onVerifyProperty={handleVerifyProperty}
              onRejectProperty={handleRejectProperty}
              onTriggerScrape={handleTriggerScrape}
              onViewProperty={(id) => {
                setViewMode('customer');
                setIsSubdomainMode(false);
                handleViewProperty(id);
              }}
              onUpdateLeadStatus={handleUpdateLeadStatus}
              adminSession={adminSession}
              onAdminLogout={handleAdminLogout}
              onSwitchToCustomer={() => {
                setViewMode('customer');
                setIsSubdomainMode(false);
                window.location.hash = '';
              }}
              activeTab={adminActiveTab}
              setActiveTab={setAdminActiveTab}
            />
          </React.Suspense>
        ) : (
          <>
            {activePage === 'home' && (
              <HomeView
                properties={properties}
                onNavigate={(p) => navigateTo(p)}
                onViewProperty={handleViewProperty}
                onContact={handleOpenContact}
                wishlist={wishlist}
                onToggleWishlist={handleToggleWishlist}
                onApplySearchFilters={handleApplyQuickSearch}
              />
            )}

            {activePage === 'properties' && (
              <PropertiesView
                properties={properties}
                onViewProperty={handleViewProperty}
                onContact={handleOpenContact}
                wishlist={wishlist}
                onToggleWishlist={handleToggleWishlist}
                filters={filters}
                setFilters={setFilters}
              />
            )}

            {activePage === 'property' && (
              <PropertyDetailsView
                property={currentProperty}
                allProperties={properties}
                onNavigate={(p) => navigateTo(p)}
                onViewProperty={handleViewProperty}
                onContact={handleOpenContact}
                wishlist={wishlist}
                onToggleWishlist={handleToggleWishlist}
                onOpenShare={(p) => setShareTarget(p)}
                onOpenSiteVisit={(p) => handleOpenContact(p, 'Site Inspection')}
                onDownloadBrochure={handleDownloadBrochure}
                onViewDocuments={handleViewDocuments}
              />
            )}

            {activePage === 'auctions' && (
              <AuctionsView
                properties={properties}
                onNavigate={(p) => navigateTo(p)}
                onViewProperty={handleViewProperty}
                onContact={handleOpenContact}
                wishlist={wishlist}
                onToggleWishlist={handleToggleWishlist}
              />
            )}

            {activePage === 'services' && (
              <ServicesView
                onOpenAuth={(mode) => setAuthModalMode(mode)}
                onNavigate={(p) => navigateTo(p)}
              />
            )}

            {activePage === 'about' && (
              <AboutView onNavigate={(p) => navigateTo(p)} />
            )}

            {activePage === 'dashboard' && (
              <DashboardView
                user={user}
                myBids={myBids}
                wishlist={wishlist}
                notifications={notifications}
                properties={properties}
                onNavigate={(p) => navigateTo(p)}
                onViewProperty={handleViewProperty}
                onContact={handleOpenContact}
                onToggleWishlist={handleToggleWishlist}
                onMarkAllNotificationsRead={() => {
                  setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
                  addToast('Notifications Updated', 'All alerts marked as read.', 'info');
                }}
                onUpdateProfile={(updated) => {
                  setUser((prev) => ({ ...prev, ...updated }));
                  addToast('Profile Updated', 'Your bidder contact profile has been saved.', 'success');
                }}
                onUploadKyc={() => {
                  addToast('KYC Document Submitted', 'Bank verification proof submitted for compliance approval.', 'success');
                }}
                onLogout={() => {
                  setUser((prev) => ({ ...prev, isLoggedIn: false }));
                  addToast('Logged Out', 'You have been safely logged out.', 'info');
                  navigateTo('home');
                }}
                activeTab={dashTab}
                setActiveTab={setDashTab}
              />
            )}
          </>
        )}
      </main>

      {/* Global Footer (Rendered only on Customer portal) */}
      {!isAdminPortal && <Footer setActivePage={(page) => navigateTo(page)} />}

      {/* Modals & Overlays */}
      <SearchOverlay
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSearch={handleGlobalSearch}
      />

      {/* Contact Property Desk Modal (replaces direct bidding) */}
      <ContactModal
        isOpen={Boolean(contactTarget)}
        onClose={() => setContactTarget(null)}
        property={contactTarget}
        currentUser={user}
        initialInquiryType={contactInitialType}
        onSubmitContact={handleSubmitContact}
      />

      <AuthModal
        isOpen={Boolean(authModalMode)}
        initialMode={authModalMode || 'login'}
        onClose={() => setAuthModalMode(null)}
        onLogin={(loggedInUser) => {
          setUser(loggedInUser);
          addToast('Welcome Back!', `Logged in as ${loggedInUser.name}.`, 'success');
        }}
      />

      <SiteVisitModal
        isOpen={Boolean(siteVisitTarget)}
        onClose={() => setSiteVisitTarget(null)}
        property={siteVisitTarget}
        onSubmitVisit={handleScheduleSiteVisit}
      />

      <ShareModal
        isOpen={Boolean(shareTarget)}
        onClose={() => setShareTarget(null)}
        property={shareTarget}
        onCopyLink={() => addToast('Link Copied', 'Property auction URL copied to clipboard.', 'success')}
      />

      {/* Floating Toast Notification Stack */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
