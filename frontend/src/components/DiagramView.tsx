import React, { useRef, useEffect, useState } from 'react';
import { PredictionResponse } from '../api';

interface DiagramViewProps {
  imageUrl: string;
  prediction: PredictionResponse;
}

export const DiagramView: React.FC<DiagramViewProps> = ({ imageUrl, prediction }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

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
      
      // Рисуем shapes
      if (boxes.shapes) {
        boxes.shapes.forEach((shape) => {
          const [x1, y1, x2, y2] = shape.bbox;
          ctx.strokeStyle = '#4f6cff';
          ctx.lineWidth = 2;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
          
          // Label
          ctx.fillStyle = 'rgba(79, 108, 255, 0.9)';
          ctx.font = 'bold 12px Unbounded, sans-serif';
          const label = `${shape.class_name} (${(shape.confidence * 100).toFixed(0)}%)`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillRect(x1, y1 - 20, textWidth + 8, 18);
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x1 + 4, y1 - 6);
        });
      }

      // Рисуем arrows
      if (boxes.arrows) {
        boxes.arrows.forEach((arrow) => {
          const [x1, y1, x2, y2] = arrow.bbox;
          ctx.strokeStyle = '#ec4899';
          ctx.lineWidth = 2;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        });
      }

      setImageLoaded(true);
    };
    img.src = imageUrl;
  }, [imageUrl, prediction]);

  const stats = {
    shapes: prediction.bounding_boxes.shapes?.length || 0,
    arrows: prediction.bounding_boxes.arrows?.length || 0,
    texts: prediction.bounding_boxes.text_regions?.length || 0
  };

  return (
    <div className="result-card glass-card">
      <h3 className="result-card-title">
        <span className="icon">
          <img src="/src/icons/search.svg" alt="search" width="20" height="20" />
        </span>
        Детекция элементов
      </h3>
      
      <div className="diagram-container">
        <canvas ref={canvasRef} style={{ width: '100%', height: 'auto' }} />
      </div>

      <div style={{
        display: 'flex',
        gap: '16px',
        marginTop: '16px',
        flexWrap: 'wrap'
      }}>
        <div style={{
          padding: '8px 16px',
          background: 'rgba(79, 108, 255, 0.1)',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#4f6cff'
        }}>
          <strong>{stats.shapes}</strong> элементов
        </div>
        <div style={{
          padding: '8px 16px',
          background: 'rgba(236, 72, 153, 0.1)',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#ec4899'
        }}>
          <strong>{stats.arrows}</strong> стрелок
        </div>
        <div style={{
          padding: '8px 16px',
          background: 'rgba(124, 58, 237, 0.1)',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#7c3aed'
        }}>
          <strong>{stats.texts}</strong> текстовых блоков
        </div>
      </div>
    </div>
  );
};
