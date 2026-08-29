import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ProtectedRoute, RoleGate } from './components/ProtectedRoute';

import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
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
import { Unauthorized } from './pages/Unauthorized';
import { NotFound } from './pages/NotFound';
import { AICopilot } from './components/ai/AICopilot';

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
        <Router>
          <div className="flex flex-col min-h-screen bg-slate-50">
            <Navbar />
            <main className="flex-grow">
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/schemes" element={<Schemes />} />
                <Route path="/schemes/:schemeId" element={<SchemeDetail />} />
                <Route path="/recommendations" element={<Recommendations />} />
                <Route path="/calculator" element={<CalculatorPage />} />
                <Route path="/unauthorized" element={<Unauthorized />} />

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
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
