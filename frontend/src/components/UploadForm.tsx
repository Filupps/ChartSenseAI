import React, { useState, useRef, useCallback } from 'react';
import { predictDiagram, PredictionResponse } from '../api';

const ACCEPTED = 'image/png,image/jpeg,image/jpg,image/bmp,image/webp,application/pdf,image/svg+xml,.svg';

function isAllowed(file: File): boolean {
  return file.type.startsWith('image/') || file.type === 'application/pdf'
    || file.name.toLowerCase().endsWith('.svg');
}

function isPdf(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
}

interface UploadFormProps {
  onPredictionComplete: (result: PredictionResponse, imageUrl: string) => void;
}

export const UploadForm: React.FC<UploadFormProps> = ({ onPredictionComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPageCount, setPdfPageCount] = useState<number>(0);
  const [selectedPage, setSelectedPage] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processDiagram = useCallback(async (file: File, page?: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await predictDiagram(file, page);
      let imageUrl: string;
      if (result._page_preview_base64) {
        imageUrl = `data:image/png;base64,${result._page_preview_base64}`;
      } else {
        imageUrl = URL.createObjectURL(file);
      }
      onPredictionComplete(result, imageUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при обработке');
    } finally {
      setIsLoading(false);
    }
  }, [onPredictionComplete]);

  const handleFile = useCallback(async (file: File) => {
    if (!isAllowed(file)) {
      setError('Поддерживаемые форматы: PNG, JPG, BMP, WebP, SVG, PDF');
      return;
    }

    setFileName(file.name);
    setPdfFile(null);
    setPdfPageCount(0);
    setSelectedPage(0);

    if (isPdf(file)) {
      const buf = await file.arrayBuffer();
      let pages = 1;
      try {
        const arr = new Uint8Array(buf);
        const text = new TextDecoder('latin1').decode(arr);
        const matches = text.match(/\/Type\s*\/Page[^s]/g);
        if (matches) pages = matches.length;
      } catch { /* fallback */ }

      if (pages > 1) {
        setPdfFile(file);
        setPdfPageCount(pages);
        setSelectedPage(0);
        return;
      }
    }

    await processDiagram(file);
  }, [processDiagram]);

  const handlePdfPageSubmit = useCallback(async () => {
    if (!pdfFile) return;
    await processDiagram(pdfFile, selectedPage);
  }, [pdfFile, selectedPage, processDiagram]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <section className="upload-section glass-card">
      <h2 className="upload-title">Загрузка диаграммы</h2>

      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED}
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        {isLoading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Анализируем диаграмму...</span>
          </div>
        ) : (
          <>
            <div className="upload-icon">
              <img src="/src/icons/chart.svg" alt="chart" width="32" height="32" />
            </div>
            <p className="upload-text">
              {fileName ? fileName : 'Перетащите файл сюда'}
            </p>
            <p className="upload-hint">
              или нажмите для выбора файла
            </p>
            <p className="upload-hint" style={{ marginTop: '12px', fontSize: '0.8rem' }}>
              Поддерживаемые форматы: PNG, JPG, BMP, WebP, SVG, PDF
            </p>
          </>
        )}
      </div>

      {pdfFile && pdfPageCount > 1 && !isLoading && (
        <div style={{
          marginTop: '16px',
          padding: '16px',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap'
        }}>
          <span style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>
            PDF: {pdfPageCount} стр. Выберите страницу:
          </span>
          <select
            value={selectedPage}
            onChange={e => setSelectedPage(Number(e.target.value))}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              background: 'var(--bg-secondary, #1e1e2e)',
              color: 'var(--text-primary, #e0e0e0)',
              fontSize: '0.9rem'
            }}
          >
            {Array.from({ length: pdfPageCount }, (_, i) => (
              <option key={i} value={i}>Страница {i + 1}</option>
            ))}
          </select>
          <button
            onClick={(e) => { e.stopPropagation(); handlePdfPageSubmit(); }}
            style={{
              padding: '6px 18px',
              borderRadius: '6px',
              border: 'none',
              background: 'var(--accent, #6366f1)',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 500
            }}
          >
            Анализировать
          </button>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '8px',
          color: '#f87171',
          fontSize: '0.9rem'
        }}>
          {error}
        </div>
      )}
    </section>
  );
};
