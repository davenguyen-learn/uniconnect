import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './components/Toast/ToastContext'
import Layout from './components/Layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import AdminLayout from './components/AdminLayout/AdminLayout'
import ErrorBoundary from './components/Common/ErrorBoundary'
import PageShimmerLoading from './components/Common/PageShimmerLoading'
import './index.css'

// ── Route-Level Code Splitting (React.lazy) ──

// Public & Auth Pages
const Landing = lazy(() => import('./pages/Landing/Landing'))
const Login = lazy(() => import('./pages/Login/Login'))
const Register = lazy(() => import('./pages/Register/Register'))
const VerifyCertificate = lazy(() => import('./pages/VerifyCertificate/VerifyCertificate'))

// Core Campus Pages
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'))
const Profile = lazy(() => import('./pages/Profile/Profile'))
const Chat = lazy(() => import('./pages/Chat/Chat'))
const Calendar = lazy(() => import('./pages/Calendar/Calendar'))

// Activity Pages
const CreateActivity = lazy(() => import('./pages/CreateActivity/CreateActivity'))
const EditActivity = lazy(() => import('./pages/CreateActivity/EditActivity'))
const ActivityDetail = lazy(() => import('./pages/ActivityDetail/ActivityDetail'))
const MyActivities = lazy(() => import('./pages/MyActivities/MyActivities'))

// Group & Community Pages
const Groups = lazy(() => import('./pages/Groups/Groups'))
const CreateGroup = lazy(() => import('./pages/Groups/CreateGroup'))
const GroupDetail = lazy(() => import('./pages/Groups/GroupDetail'))

// Admin Control Plane Pages
const AdminDashboard = lazy(() => import('./pages/Admin/AdminDashboard'))
const AdminUsers = lazy(() => import('./pages/Admin/AdminUsers'))
const AdminReports = lazy(() => import('./pages/Admin/AdminReports'))
const AdminContent = lazy(() => import('./pages/Admin/AdminContent'))

// Fallback Page
const NotFound = lazy(() => import('./pages/NotFound/NotFound'))

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <ErrorBoundary fallbackTitle="Không thể tải ứng dụng">
            <Suspense fallback={<PageShimmerLoading />}>
              <Routes>
                {/* Public routes */}
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route element={<Layout />}>
                  <Route path="/verify-certificate" element={<VerifyCertificate />} />
                </Route>

                {/* Protected routes — wrapped in Layout with navigation AppShell */}
                <Route element={<ProtectedRoute />}>
                  <Route element={<Layout />}>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/profile/:id" element={<Profile />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/groups" element={<Groups />} />
                    <Route path="/groups/new" element={<CreateGroup />} />
                    <Route path="/groups/create" element={<CreateGroup />} />
                    <Route path="/groups/:id" element={<GroupDetail />} />
                    <Route path="/activities/new" element={<CreateActivity />} />
                    <Route path="/activities/create" element={<CreateActivity />} />
                    <Route path="/activities/:id/edit" element={<EditActivity />} />
                    <Route path="/activities/:id" element={<ActivityDetail />} />
                    <Route path="/my-activities" element={<MyActivities />} />
                    <Route path="/calendar" element={<Calendar />} />
                  </Route>
                </Route>

                {/* Admin routes — separate command layout */}
                <Route element={<AdminRoute />}>
                  <Route element={<AdminLayout />}>
                    <Route path="/admin" element={<AdminDashboard />} />
                    <Route path="/admin/users" element={<AdminUsers />} />
                    <Route path="/admin/reports" element={<AdminReports />} />
                    <Route path="/admin/content" element={<AdminContent />} />
                  </Route>
                </Route>

                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
