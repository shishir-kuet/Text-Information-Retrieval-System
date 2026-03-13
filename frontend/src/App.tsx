import { BrowserRouter, Routes, Route } from 'react-router'
import Home from './pages/Home'
import Results from './pages/Results'
import PageView from './pages/PageView'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="/page/:pageId" element={<PageView />} />
      </Routes>
    </BrowserRouter>
  )
}
