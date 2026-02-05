import React, { useState } from 'react';
import { UploadForm } from './components/UploadForm';
import { DiagramView } from './components/DiagramView';
import { AlgoView } from './components/AlgoView';
import { AlgoToDiagram } from './components/AlgoToDiagram';
import { PredictionResponse } from './api';
import './styles/main.css';

type Page = 'home' | 'algo-to-diagram';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');

  const handlePredictionComplete = (result: PredictionResponse, url: string) => {
    setPrediction(result);
    setImageUrl(url);
  };

  const handleAlgorithmUpdate = (algo: PredictionResponse['algorithm']) => {
    if (prediction) {
      setPrediction({
        ...prediction,
        algorithm: algo
      });
    }
  };

  const scrollToUpload = () => {
    const el = document.getElementById('upload-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToHero = () => {
    const el = document.getElementById('hero-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      return;
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const goHomeAndScrollToUpload = () => {
    if (currentPage !== 'home') {
      setCurrentPage('home');
      window.setTimeout(scrollToUpload, 0);
      return;
    }
    scrollToUpload();
  };

  const goHomeAndScrollToHero = () => {
    if (currentPage !== 'home') {
      setCurrentPage('home');
      window.setTimeout(scrollToHero, 0);
      return;
    }
    scrollToHero();
  };

  return (
    <div className="app">
      <div className="circle-decoration circle-1"></div>
      <div className="circle-decoration circle-2"></div>
      <div className="circle-decoration circle-3"></div>
      <div className="circle-decoration circle-4"></div>
      <div className="glow-decoration glow-1"></div>
      <div className="glow-decoration glow-2"></div>
      <div className="glow-decoration glow-3"></div>
      <div className="sparkle-grid"></div>
      
      <nav className="top-navbar">
        <div className="navbar-left clickable" onClick={goHomeAndScrollToHero} role="button" tabIndex={0}>
          <img src="/logo.svg" alt="logo" className="navbar-logo" />
          <span className="navbar-brand">ChartSenseAI</span>
        </div>
        <div className="navbar-links">
          <button 
            className="navbar-link"
            onClick={goHomeAndScrollToUpload}
          >
            Диаграмма → Алгоритм
          </button>
          <button 
            className={`navbar-link ${currentPage === 'algo-to-diagram' ? 'active' : ''}`}
            onClick={() => setCurrentPage('algo-to-diagram')}
          >
            Алгоритм → Диаграмма
          </button>
        </div>
      </nav>

      {currentPage === 'home' && (
        <>
          <section className="hero-section" id="hero-section">
            <div className="hero-content">
              <h1 className="hero-title">ChartSenseAI</h1>
              <p className="hero-subtitle">
                Сервис преобразования диаграмм<br />
                в алгоритмическое описание
              </p>
              <div className="hero-cta">
                <button className="cta-btn primary" onClick={scrollToUpload}>
                  <img src="/src/icons/chart.svg" alt="" />
                  Диаграмма → Алгоритм
                </button>
                <button className="cta-btn secondary" onClick={() => setCurrentPage('algo-to-diagram')}>
                  <img src="/src/icons/procedure.svg" alt="" />
                  Алгоритм → Диаграмма
                </button>
              </div>
            </div>
          </section>

          <section className="features-section">
            <div className="features-grid">
              <div className="feature-card glass-card fade-in delay-1">
                <div className="feature-icon">
                  <img src="/src/icons/search.svg" alt="detect" width="24" height="24" />
                </div>
                <h3>Детекция элементов</h3>
                <p>YOLO распознаёт блоки, стрелки и текстовые области</p>
              </div>
              <div className="feature-card glass-card fade-in delay-2">
                <div className="feature-icon">
                  <img src="/src/icons/chart.svg" alt="graph" width="24" height="24" />
                </div>
                <h3>Построение графа</h3>
                <p>Автоматическое связывание элементов в граф</p>
              </div>
              <div className="feature-card glass-card fade-in delay-3">
                <div className="feature-icon">
                  <img src="/src/icons/procedure.svg" alt="algo" width="24" height="24" />
                </div>
                <h3>Генерация алгоритма</h3>
                <p>Преобразование в текстовое описание</p>
              </div>
              <div className="feature-card glass-card fade-in delay-4">
                <div className="feature-icon">
                  <img src="/src/icons/edit.svg" alt="edit" width="24" height="24" />
                </div>
                <h3>Редактирование</h3>
                <p>Интерактивная корректировка алгоритма</p>
              </div>
            </div>
          </section>

          <section className="main-section" id="upload-section">
            <div className="section-header">
              <h2>Диаграмма → Алгоритм</h2>
              <p>Загрузите изображение диаграммы для автоматического анализа</p>
            </div>
            
            <UploadForm onPredictionComplete={handlePredictionComplete} />

            {prediction && imageUrl && (
              <div className="results-grid fade-in">
                <DiagramView 
                  imageUrl={imageUrl} 
                  prediction={prediction}
                />
                <AlgoView 
                  prediction={prediction} 
                  editable={true}
                  onAlgorithmUpdate={handleAlgorithmUpdate}
                />
              </div>
            )}
          </section>
        </>
      )}

      {currentPage === 'algo-to-diagram' && (
        <main className="app-main page-algo-to-diagram">
          <div className="page-header">
            <h2>Алгоритм → Диаграмма</h2>
            <p>Опишите алгоритм или загрузите файл для генерации диаграммы</p>
          </div>
          <AlgoToDiagram />
        </main>
      )}
    </div>
  );
}

export default App;
