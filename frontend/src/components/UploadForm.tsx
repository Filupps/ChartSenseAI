import React, { useState, useRef, useCallback } from 'react';
import { predictDiagram, PredictionResponse } from '../api';

interface UploadFormProps {
  onPredictionComplete: (result: PredictionResponse, imageUrl: string) => void;
}

export const UploadForm: React.FC<UploadFormProps> = ({ onPredictionComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Пожалуйста, выберите изображение');
      return;
    }

    setIsLoading(true);
    setError(null);
    setFileName(file.name);

    try {
      const result = await predictDiagram(file);
      const imageUrl = URL.createObjectURL(file);
      onPredictionComplete(result, imageUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при обработке изображения');
    } finally {
      setIsLoading(false);
    }
  }, [onPredictionComplete]);

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
          accept="image/*"
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
              {fileName ? fileName : 'Перетащите изображение сюда'}
            </p>
            <p className="upload-hint">
              или нажмите для выбора файла
            </p>
            <p className="upload-hint" style={{ marginTop: '12px', fontSize: '0.8rem' }}>
              Поддерживаемые форматы: PNG, JPG, JPEG, BMP
            </p>
          </>
        )}
      </div>

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
