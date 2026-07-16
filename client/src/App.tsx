import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './components/Toast/ToastContext'
import Layout from './components/Layout/Layout'
import Landing from './pages/Landing/Landing'
import Login from './pages/Login/Login'
import Register from './pages/Register/Register'
import Dashboard from './pages/Dashboard/Dashboard'
import Profile from './pages/Profile/Profile'
import CreateActivity from './pages/CreateActivity/CreateActivity'
import EditActivity from './pages/CreateActivity/EditActivity'
import ActivityDetail from './pages/ActivityDetail/ActivityDetail'
import MyActivities from './pages/MyActivities/MyActivities'
import Documents from './pages/Documents/Documents'
import DocumentDetail from './pages/DocumentDetail/DocumentDetail'
import UploadDocument from './pages/UploadDocument/UploadDocument'
import NotFound from './pages/NotFound/NotFound'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import Chat from './pages/Chat/Chat'
import Groups from './pages/Groups/Groups'
import CreateGroup from './pages/Groups/CreateGroup'
import GroupDetail from './pages/Groups/GroupDetail'
import AdminLayout from './components/AdminLayout/AdminLayout'
import AdminDashboard from './pages/Admin/AdminDashboard'
import AdminUsers from './pages/Admin/AdminUsers'
import AdminReports from './pages/Admin/AdminReports'
import AdminContent from './pages/Admin/AdminContent'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes — wrapped in Layout with navbar */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/profile/:id" element={<Profile />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/groups" element={<Groups />} />
                <Route path="/groups/new" element={<CreateGroup />} />
                <Route path="/groups/:id" element={<GroupDetail />} />
                <Route path="/activities/new" element={<CreateActivity />} />
                <Route path="/activities/:id/edit" element={<EditActivity />} />
                <Route path="/activities/:id" element={<ActivityDetail />} />
                <Route path="/my-activities" element={<MyActivities />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/documents/upload" element={<UploadDocument />} />
                <Route path="/documents/:id" element={<DocumentDetail />} />
              </Route>
            </Route>

            {/* Admin routes — separate layout */}
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
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

