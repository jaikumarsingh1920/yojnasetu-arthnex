import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ProtectedRoute, RoleGate } from './components/ProtectedRoute';

import { Home } from './pages/Home';
import { About } from './pages/About';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Profile } from './pages/Profile';
import { Dashboard } from './pages/Dashboard';
import { Schemes } from './pages/Schemes';
import { SchemeDetail } from './pages/SchemeDetail';
import { Recommendations } from './pages/Recommendations';
import { CalculatorPage } from './pages/Calculator';
import { Applications } from './pages/Applications';
import { ApplicationDetail } from './pages/ApplicationDetail';
import { PartnerQueue } from './pages/PartnerQueue';
import { PartnerDetail } from './pages/PartnerDetail';
import { AdminDashboard } from './pages/AdminDashboard';
import { Notifications } from './pages/Notifications';
import { SavedSchemes } from './pages/SavedSchemes';
import { ChannelPartners } from './pages/ChannelPartners';
import { Unauthorized } from './pages/Unauthorized';
import { NotFound } from './pages/NotFound';
import { AICopilot } from './components/ai/AICopilot';
import Resources from './pages/Resources';
import { ComparisonProvider } from './context/ComparisonContext';
import { TextSizeProvider } from './context/TextSizeContext';
import { ComparisonTray } from './components/ComparisonTray';
import { Compare } from './pages/Compare';
import { ScrollToTop } from './components/ScrollToTop';
import { PageTitleManager } from './components/PageTitleManager';
import Faq from './pages/Faq';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TextSizeProvider>
          <ComparisonProvider>
            <Router>
              <ScrollToTop />
              <PageTitleManager />
              <div className="flex flex-col min-h-screen bg-[#fef9f3] w-full max-w-full">
                <Navbar />
                <main className="flex-grow w-full max-w-full min-w-0">
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<Home />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/auth/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/auth/register" element={<Register />} />
                  <Route path="/schemes" element={<Schemes />} />
                  <Route path="/schemes/:schemeId" element={<SchemeDetail />} />
                  <Route path="/compare" element={<Compare />} />
                  <Route path="/recommendations" element={<Recommendations />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/channel-partners" element={<ChannelPartners />} />
                  <Route path="/calculator" element={<CalculatorPage />} />
                  <Route path="/unauthorized" element={<Unauthorized />} />
                  <Route path="/resources" element={<Resources />} />
                  <Route path="/resources" element={<Resources />} />
<Route path="/faq" element={<Faq />} />

                {/* Authenticated Notifications Route */}
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <Notifications />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/saved-schemes"
                  element={
                    <ProtectedRoute>
                      <SavedSchemes />
                    </ProtectedRoute>
                  }
                />

                {/* Beneficiary Protected Routes */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['BENEFICIARY', 'SYSTEM_ADMIN']}>
                        <Dashboard />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/applications"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['BENEFICIARY', 'SYSTEM_ADMIN']}>
                        <Applications />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/applications/:id"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['BENEFICIARY', 'SYSTEM_ADMIN']}>
                        <ApplicationDetail />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />

                {/* Partner / Authority Protected Routes */}
                <Route
                  path="/partner"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['PARTNER_USER', 'PARTNER_ADMIN', 'SYSTEM_ADMIN']}>
                        <PartnerQueue />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/partner/applications/:id"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['PARTNER_USER', 'PARTNER_ADMIN', 'SYSTEM_ADMIN']}>
                        <PartnerDetail />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />

                {/* System Admin Protected Routes */}
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute>
                      <RoleGate allowedRoles={['SYSTEM_ADMIN']}>
                        <AdminDashboard />
                      </RoleGate>
                    </ProtectedRoute>
                  }
                />

                {/* Catch All */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </main>
            <Footer />
            <AICopilot />
            <ComparisonTray />
          </div>
        </Router>
      </ComparisonProvider>
    </TextSizeProvider>
  </AuthProvider>
</QueryClientProvider>
);
};

export default App;
