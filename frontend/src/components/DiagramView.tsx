import React, { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { PredictionResponse } from '../api';

interface DiagramViewProps {
  imageUrl: string;
  prediction: PredictionResponse;
}

export const DiagramView: React.FC<DiagramViewProps> = ({ imageUrl, prediction }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      const boxes = prediction.bounding_boxes;
      
      const colors: Record<string, string> = {
        rectangle: '#4f6cff',
        diamond: '#f59e0b',
        circle: '#10b981',
        arrow: '#ec4899',
        text_region: '#8b5cf6'
      };
      
      const allDetections = boxes.all || [];
      
      allDetections.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const className = det.class_name.toLowerCase();
        const color = colors[className] || '#6b7280';
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        ctx.fillStyle = color;
        ctx.font = 'bold 11px sans-serif';
        const label = `${det.class_name} (${(det.confidence * 100).toFixed(0)}%)`;
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x1, y1 - 18, textWidth + 6, 16);
        ctx.fillStyle = '#fff';
        ctx.fillText(label, x1 + 3, y1 - 5);
      });

    };
    img.src = imageUrl;
  }, [imageUrl, prediction]);

  const allDetections = prediction.bounding_boxes.all || [];
  const stats = {
    rectangles: allDetections.filter(d => d.class_name.toLowerCase() === 'rectangle').length,
    diamonds: allDetections.filter(d => d.class_name.toLowerCase() === 'diamond').length,
    circles: allDetections.filter(d => d.class_name.toLowerCase() === 'circle').length,
    arrows: allDetections.filter(d => d.class_name.toLowerCase() === 'arrow').length,
    texts: allDetections.filter(d => d.class_name.toLowerCase() === 'text_region').length
  };

  return (
    <div className="result-card glass-card">
      <h3 className="result-card-title">
        <span className="icon">
          <img src="/src/icons/search.svg" alt="search" width="20" height="20" />
        </span>
        Детекция элементов
      </h3>
      
      <div className="diagram-container" onClick={() => setShowModal(true)} style={{ cursor: 'pointer' }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: 'auto' }} />
      </div>

      {showModal && createPortal(
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000,
          padding: '20px'
        }} onClick={(e) => {
          if (e.target === e.currentTarget) setShowModal(false);
        }}>
          <div style={{ position: 'relative', maxWidth: '95vw', maxHeight: '95vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={(e) => e.stopPropagation()}>
            <canvas 
              ref={(modalCanvas) => {
                if (modalCanvas && canvasRef.current) {
                  const ctx = modalCanvas.getContext('2d');
                  if (ctx) {
                    modalCanvas.width = canvasRef.current.width;
                    modalCanvas.height = canvasRef.current.height;
                    ctx.drawImage(canvasRef.current, 0, 0);
                  }
                }
              }}
              style={{ maxWidth: '100%', maxHeight: '95vh', objectFit: 'contain', borderRadius: '8px' }}
            />
            <button 
              onClick={() => setShowModal(false)}
              style={{
                position: 'absolute',
                top: '-20px',
                right: '-20px',
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                backgroundColor: '#fff',
                border: 'none',
                fontSize: '28px',
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                color: '#333'
              }}
            >×</button>
          </div>
        </div>,
        document.body
      )}

      <div style={{
        display: 'flex',
        gap: '10px',
        marginTop: '16px',
        flexWrap: 'wrap'
      }}>
        <div style={{ padding: '6px 12px', background: 'rgba(79, 108, 255, 0.15)', borderRadius: '6px', fontSize: '0.8rem', color: '#4f6cff' }}>
          <strong>{stats.rectangles}</strong> rectangle
        </div>
        <div style={{ padding: '6px 12px', background: 'rgba(245, 158, 11, 0.15)', borderRadius: '6px', fontSize: '0.8rem', color: '#f59e0b' }}>
          <strong>{stats.diamonds}</strong> diamond
        </div>
        <div style={{ padding: '6px 12px', background: 'rgba(16, 185, 129, 0.15)', borderRadius: '6px', fontSize: '0.8rem', color: '#10b981' }}>
          <strong>{stats.circles}</strong> circle
        </div>
        <div style={{ padding: '6px 12px', background: 'rgba(236, 72, 153, 0.15)', borderRadius: '6px', fontSize: '0.8rem', color: '#ec4899' }}>
          <strong>{stats.arrows}</strong> arrow
        </div>
        <div style={{ padding: '6px 12px', background: 'rgba(139, 92, 246, 0.15)', borderRadius: '6px', fontSize: '0.8rem', color: '#8b5cf6' }}>
          <strong>{stats.texts}</strong> text
        </div>
      </div>
    </div>
  );
};
