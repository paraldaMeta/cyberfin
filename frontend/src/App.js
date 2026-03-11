import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import MarketPage from "./pages/MarketPage";
import StockDetailPage from "./pages/StockDetailPage";
import AIPredictionPage from "./pages/AIPredictionPage";
import DivinationPage from "./pages/DivinationPage";
import WatchlistPage from "./pages/WatchlistPage";
import HistoryPage from "./pages/HistoryPage";
import { Toaster } from "./components/ui/sonner";
import { LanguageProvider } from "./i18n";

function App() {
  return (
    <LanguageProvider>
      <div className="App min-h-screen bg-[#0a0e17]">
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/market/:type" element={<MarketPage />} />
              <Route path="/stock/:symbol" element={<StockDetailPage />} />
              <Route path="/predict/ai" element={<AIPredictionPage />} />
              <Route path="/predict/divination" element={<DivinationPage />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
              <Route path="/history" element={<HistoryPage />} />
            </Routes>
          </Layout>
        </BrowserRouter>
        <Toaster position="top-right" />
      </div>
    </LanguageProvider>
  );
}

export default App;
