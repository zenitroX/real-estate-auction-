import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
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
import CompareView from './views/CompareView';
import { supabase } from './lib/supabaseClient';

const AdminView = React.lazy(() => import('./views/AdminView'));
const AdminLoginView = React.lazy(() => import('./views/AdminLoginView'));

import { INITIAL_PROPERTIES } from './data/propertiesData';
import {
  INITIAL_USER,
  INITIAL_WISHLIST,
  INITIAL_NOTIFICATIONS,
} from './data/initialUserData';
import {
  fetchLiveAuctions,
  submitLeadApi,
  verifyPropertyApi,
  updateLeadStatusApi,
  fetchAdminLeadsApi,
  triggerScrapeApi,
  flushOfflineLeads,
} from './data/api';
import { isSubdomainAdmin } from './utils/domain';

const ENABLE_DEMO_DATA = import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEMO_DATA === 'true';

const PAGE_TO_PATH = {
  home: '/',
  properties: '/auctions',
  auctions: '/auctions',
  services: '/services',
  about: '/about',
  dashboard: '/saved',
  saved: '/saved',
};

function getActivePageFromPath(pathname) {
  if (pathname === '/') return 'home';
  if (pathname.startsWith('/auctions') || pathname.startsWith('/properties/')) return 'properties';
  if (pathname.startsWith('/services')) return 'services';
  if (pathname.startsWith('/about')) return 'about';
  if (pathname.startsWith('/saved') || pathname.startsWith('/dashboard')) return 'dashboard';
  return 'home';
}

function PropertyDetailRoute({ properties, ...props }) {
  const { idOrSlug } = useParams();
  const property = properties.find((p) => String(p.id) === idOrSlug || (p.slug && p.slug === idOrSlug));

  if (!property) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem', textAlign: 'center' }}>
        <h2>Property Listing Not Found</h2>
        <p style={{ color: '#64748B', margin: '0.75rem 0 1.5rem' }}>
          This auction listing may have expired, been removed, or is awaiting verification.
        </p>
        <button className="btn btn-primary" onClick={() => props.onNavigate('auctions')}>
          Browse Active Auctions
        </button>
      </div>
    );
  }

  return <PropertyDetailsView property={property} allProperties={properties} {...props} />;
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const activePage = getActivePageFromPath(location.pathname);

  const [dashTab, setDashTab] = useState('overview');
  const [adminActiveTab, setAdminActiveTab] = useState('verification');

  const [isSubdomainMode, setIsSubdomainMode] = useState(() => isSubdomainAdmin());
  const [viewMode, setViewMode] = useState(() => (isSubdomainAdmin() ? 'admin' : 'customer'));

  const [adminSession, setAdminSession] = useState(() => {
    try {
      const saved = sessionStorage.getItem('skandx_admin_session');
      if (!saved) return null;
      const parsed = JSON.parse(saved);
      if (parsed?.token && parsed.token.startsWith('skandx-adm-')) {
        return parsed;
      }
      sessionStorage.removeItem('skandx_admin_session');
      return null;
    } catch {
      return null;
    }
  });

  const [properties, setProperties] = useState(() => (ENABLE_DEMO_DATA ? INITIAL_PROPERTIES : []));
  const [apiSource, setApiSource] = useState('LOADING');
  const [apiError, setApiError] = useState(null);
  const [leads, setLeads] = useState([]);

  const [user, setUser] = useState(INITIAL_USER);
  const [wishlist, setWishlist] = useState(INITIAL_WISHLIST);
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);

  const [filters, setFilters] = useState({
    location: '',
    types: ['residential', 'commercial', 'land', 'industrial'],
    minBudget: 0,
    maxBudget: 100000000,
    banks: ['Canara Bank', 'SBI', 'ICICI Bank', 'Others'],
    sort: 'ending',
  });

  const [searchOpen, setSearchOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState(null);
  const [contactTarget, setContactTarget] = useState(null);
  const [contactInitialType, setContactInitialType] = useState('Site Inspection');
  const [siteVisitTarget, setSiteVisitTarget] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((title, message = '', type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev.slice(-1), { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2500);
  }, []);

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadAuctions = useCallback(async () => {
    setApiError(null);
    const res = await fetchLiveAuctions();
    if (res.error) {
      setApiSource('ERROR');
      setApiError(res.error);
      setProperties([]);
      return;
    }
    setProperties(res.properties || []);
    setApiSource(res.source);
  }, []);

  useEffect(() => {
    loadAuctions();
  }, [loadAuctions]);

  // Sync Supabase customer session and saved_properties
  useEffect(() => {
    if (!supabase) return undefined;

    const syncUser = async (sbUser) => {
      if (!sbUser) {
        setUser({ ...INITIAL_USER, isLoggedIn: false });
        return;
      }
      const fullName = sbUser.user_metadata?.full_name || sbUser.email || 'SKANDX Buyer';
      setUser({
        id: sbUser.id,
        name: fullName,
        email: sbUser.email || '',
        phone: sbUser.user_metadata?.phone || '',
        initials: fullName.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase(),
        isLoggedIn: true,
      });
      const { data: savedRows } = await supabase
        .from('saved_properties')
        .select('property_id')
        .eq('user_id', sbUser.id);
      if (Array.isArray(savedRows)) {
        setWishlist(savedRows.map((r) => r.property_id));
      }
    };

    supabase.auth.getSession().then(({ data }) => syncUser(data?.session?.user || null));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      syncUser(session?.user || null);
    });
    return () => listener?.subscription?.unsubscribe();
  }, []);

  useEffect(() => {
    if (!adminSession?.token) return;
    fetchAdminLeadsApi()
      .then((res) => {
        if (res && Array.isArray(res.leads)) setLeads(res.leads);
      })
      .catch((err) => {
        if (err?.status === 401) {
          sessionStorage.removeItem('skandx_admin_session');
          setAdminSession(null);
        }
      });
  }, [adminSession]);

  useEffect(() => {
    const handleSync = () => flushOfflineLeads();
    window.addEventListener('online', handleSync);
    window.addEventListener('focus', handleSync);
    return () => {
      window.removeEventListener('online', handleSync);
      window.removeEventListener('focus', handleSync);
    };
  }, []);

  // Legacy hash URL redirect (#property/:id -> /properties/:id, #admin -> admin mode)
  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    if (hash.startsWith('property/')) {
      const id = hash.split('/')[1];
      if (id) navigate(`/properties/${encodeURIComponent(id)}`, { replace: true });
    } else if (hash === 'admin') {
      setViewMode('admin');
    } else if (['properties', 'auctions', 'services', 'about', 'dashboard'].includes(hash)) {
      navigate(PAGE_TO_PATH[hash] || '/', { replace: true });
    }
  }, [navigate]);

  const navigateTo = useCallback(
    (page, propId = null) => {
      if (page === 'property' && propId) {
        navigate(`/properties/${encodeURIComponent(propId)}`);
      } else {
        navigate(PAGE_TO_PATH[page] || '/');
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [navigate]
  );

  const handleViewProperty = useCallback(
    (id) => {
      if (supabase && user?.isLoggedIn && user?.id) {
        supabase
          .from('recently_viewed')
          .upsert({ user_id: user.id, property_id: String(id), viewed_at: new Date().toISOString() }, { onConflict: 'user_id,property_id' })
          .then(() => {});
      }
      navigate(`/properties/${encodeURIComponent(id)}`);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [navigate, user]
  );

  const handleOpenContact = (property, inquiryType = 'Site Inspection') => {
    setContactTarget(property);
    setContactInitialType(inquiryType);
  };

  const handleSubmitContact = async (leadData) => {
    const result = await submitLeadApi(leadData);
    const newLead = {
      ...leadData,
      id: result?.leadId || `lead-${Date.now()}`,
      leadCode: result?.leadCode || null,
      time: 'Just now',
      status: result?.leadStatus || 'REQUEST_RECEIVED',
    };
    setLeads((prev) => [newLead, ...prev]);
    addToast(
      'Request Received!',
      `Advisor request recorded for ${leadData.propertyTitle}.`,
      'success'
    );
    return result;
  };

  const handleAdminAuthError = (err) => {
    if (err?.status === 401) {
      sessionStorage.removeItem('skandx_admin_session');
      setAdminSession(null);
      addToast('Session Expired', 'Please sign in again to continue.', 'error');
      return true;
    }
    return false;
  };

  const handleVerifyProperty = async (id, updatedFields = {}) => {
    const previousProperties = properties;
    setProperties((prev) =>
      prev.map((p) =>
        p.id === id
          ? { ...p, ...updatedFields, verified: true, status: 'PUBLISHED', verifiedDate: 'Just now' }
          : p
      )
    );

    try {
      await verifyPropertyApi(id, 'PUBLISHED', updatedFields);
      addToast(
        'Listing Verified & Published!',
        'Asset is now visible to customers on the public marketplace.',
        'success'
      );
    } catch (err) {
      setProperties(previousProperties);
      if (!handleAdminAuthError(err)) {
        addToast('Update Failed', err.message || 'Could not publish property.', 'error');
      }
    }
  };

  const handleRejectProperty = async (id) => {
    const previousProperties = properties;
    setProperties((prev) =>
      prev.map((p) => (p.id === id ? { ...p, verified: false, status: 'REJECTED' } : p))
    );

    try {
      await verifyPropertyApi(id, 'REJECTED');
      addToast('Listing Rejected', 'The property notice has been removed from public view.', 'info');
    } catch (err) {
      setProperties(previousProperties);
      if (!handleAdminAuthError(err)) {
        addToast('Update Failed', err.message || 'Could not reject property.', 'error');
      }
    }
  };

  const handleTriggerScrape = async () => {
    try {
      await triggerScrapeApi();
      addToast(
        'Scraper Pipeline Triggered',
        'Bank portal crawlers and Gemini 2.5 Flash OCR are processing raw notices.',
        'info'
      );
    } catch (err) {
      if (!handleAdminAuthError(err)) {
        addToast('Scraper Error', err.message || 'Could not trigger scraper.', 'error');
      }
    }
  };

  const handleUpdateLeadStatus = async (leadId, newStatus) => {
    const previousLeads = leads;
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
    try {
      await updateLeadStatusApi(leadId, newStatus);
      addToast('Lead Status Updated', `Inquiry status changed to ${newStatus}.`, 'info');
    } catch (err) {
      setLeads(previousLeads);
      if (!handleAdminAuthError(err)) {
        addToast('Lead Update Failed', err.message || 'Could not update lead status.', 'error');
      }
    }
  };

  const handleAdminLogout = () => {
    sessionStorage.removeItem('skandx_admin_session');
    setAdminSession(null);
    addToast('Admin Logged Out', 'Your back-office session has been safely closed.', 'info');
  };

  const handleToggleWishlist = async (id) => {
    const isSaved = wishlist.includes(id);
    const target = properties.find((p) => p.id === id);
    const name = target ? target.title : 'Property';

    setWishlist((prev) => (isSaved ? prev.filter((item) => item !== id) : [...prev, id]));

    if (supabase && user?.isLoggedIn && user?.id) {
      if (isSaved) {
        await supabase.from('saved_properties').delete().eq('user_id', user.id).eq('property_id', String(id));
      } else {
        await supabase.from('saved_properties').upsert({ user_id: user.id, property_id: String(id) }, { onConflict: 'user_id,property_id' });
      }
    }

    if (isSaved) {
      addToast('Removed from Watchlist', `${name} removed from your tracked auctions.`, 'info');
    } else {
      addToast('Added to Watchlist', `${name} added to your tracked auctions.`, 'success');
    }
  };

  const handleGlobalSearch = (query) => {
    setFilters((prev) => ({ ...prev, location: query }));
    setViewMode('customer');
    navigateTo('auctions');
  };

  const handleApplyQuickSearch = ({ locality, type, budget }) => {
    let minBudget = 0;
    let maxBudget = 100000000;
    if (budget === 'under50') {
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

  const pendingCount = properties.filter(
    (p) => p.status === 'PENDING_REVIEW' || p.status === 'NEEDS_MANUAL_REVIEW' || !p.verified
  ).length;
  const isAdminPortal = isSubdomainMode || viewMode === 'admin';

  if (isAdminPortal && !adminSession) {
    return (
      <div className="app-root">
        <React.Suspense
          fallback={
            <div className="view-loading" style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8' }}>
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
              navigate('/');
            }}
          />
        </React.Suspense>
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </div>
    );
  }

  return (
    <div className="app-root">
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
        onSetViewMode={(mode) => setViewMode(mode)}
        pendingCount={pendingCount}
        isAdminPortal={isAdminPortal}
        adminSession={adminSession}
        onAdminLogout={handleAdminLogout}
        showDevSwitcher={import.meta.env.DEV}
        adminActiveTab={adminActiveTab}
        onSetAdminTab={setAdminActiveTab}
      />

      <main id="main">
        {apiError && !isAdminPortal && (
          <div style={{ background: '#FEF2F2', color: '#991B1B', padding: '0.75rem 1.5rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', fontSize: '0.9rem' }}>
            <span>Unable to load live auction listings ({apiError}).</span>
            <button className="btn btn-sm" onClick={loadAuctions} style={{ textDecoration: 'underline', background: 'transparent', border: 'none', color: '#991B1B', cursor: 'pointer' }}>
              Retry
            </button>
          </div>
        )}

        {isAdminPortal ? (
          <React.Suspense
            fallback={
              <div className="view-loading" style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8' }}>
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
                navigate('/');
              }}
              activeTab={adminActiveTab}
              setActiveTab={setAdminActiveTab}
            />
          </React.Suspense>
        ) : (
          <Routes>
            <Route
              path="/"
              element={
                <HomeView
                  properties={properties}
                  onNavigate={navigateTo}
                  onViewProperty={handleViewProperty}
                  onContact={handleOpenContact}
                  wishlist={wishlist}
                  onToggleWishlist={handleToggleWishlist}
                  onApplySearchFilters={handleApplyQuickSearch}
                />
              }
            />
            <Route
              path="/auctions"
              element={
                <PropertiesView
                  properties={properties}
                  onViewProperty={handleViewProperty}
                  onContact={handleOpenContact}
                  wishlist={wishlist}
                  onToggleWishlist={handleToggleWishlist}
                  filters={filters}
                  setFilters={setFilters}
                />
              }
            />
            <Route path="/properties" element={<Navigate to="/auctions" replace />} />
            <Route
              path="/properties/:idOrSlug"
              element={
                <PropertyDetailRoute
                  properties={properties}
                  onNavigate={navigateTo}
                  onViewProperty={handleViewProperty}
                  onContact={handleOpenContact}
                  wishlist={wishlist}
                  onToggleWishlist={handleToggleWishlist}
                  onOpenShare={(p) => setShareTarget(p)}
                  onOpenSiteVisit={(p) => handleOpenContact(p, 'Site Inspection')}
                  onDownloadBrochure={(p) => handleOpenContact(p, 'Download Notice')}
                  onViewDocuments={(p) => handleOpenContact(p, 'Legal Title Search Report')}
                />
              }
            />
            <Route
              path="/compare"
              element={
                <CompareView
                  properties={properties}
                  onNavigate={navigateTo}
                  onViewProperty={handleViewProperty}
                  onContact={handleOpenContact}
                />
              }
            />
            <Route
              path="/services"
              element={<ServicesView onOpenAuth={(mode) => setAuthModalMode(mode)} onNavigate={navigateTo} />}
            />
            <Route path="/about" element={<AboutView onNavigate={navigateTo} />} />
            <Route
              path="/saved"
              element={
                <DashboardView
                  user={user}
                  wishlist={wishlist}
                  notifications={notifications}
                  properties={properties}
                  onNavigate={navigateTo}
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
                  onLogout={async () => {
                    if (supabase) await supabase.auth.signOut();
                    setUser((prev) => ({ ...prev, isLoggedIn: false }));
                    addToast('Logged Out', 'You have been safely logged out.', 'info');
                    navigateTo('home');
                  }}
                  activeTab={dashTab}
                  setActiveTab={setDashTab}
                />
              }
            />
            <Route path="/dashboard" element={<Navigate to="/saved" replace />} />
            <Route
              path="*"
              element={
                <div className="container" style={{ padding: '5rem 1.5rem', textAlign: 'center' }}>
                  <h1>404 — Page Not Found</h1>
                  <p style={{ color: '#64748B', margin: '0.75rem 0 1.5rem' }}>
                    The requested auction page does not exist.
                  </p>
                  <button className="btn btn-primary" onClick={() => navigateTo('home')}>
                    Return Home
                  </button>
                </div>
              }
            />
          </Routes>
        )}
      </main>

      {!isAdminPortal && <Footer setActivePage={navigateTo} />}

      <SearchOverlay isOpen={searchOpen} onClose={() => setSearchOpen(false)} onSearch={handleGlobalSearch} />

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
        onSubmitVisit={(p) => handleOpenContact(p, 'Site Inspection')}
      />

      <ShareModal
        isOpen={Boolean(shareTarget)}
        onClose={() => setShareTarget(null)}
        property={shareTarget}
        onCopyLink={() => addToast('Link Copied', 'Property auction URL copied to clipboard.', 'success')}
      />

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
