import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { App as AntApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import MainLayout from './layouts/MainLayout'
import PatientList from './pages/PatientList'
import TaskCreate from './pages/TaskCreate'
import TaskMonitor from './pages/TaskMonitor'
import Report from './pages/Report'
import Appointment from './pages/Appointment'

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Navigate to="/patients" replace />} />
              <Route path="patients" element={<PatientList />} />
              <Route path="tasks/create" element={<TaskCreate />} />
              <Route path="tasks/monitor" element={<TaskMonitor />} />
              <Route path="report" element={<Report />} />
              <Route path="appointments" element={<Appointment />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  )
}
