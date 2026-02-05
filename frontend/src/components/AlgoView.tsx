import React, { useState } from 'react';
import { PredictionResponse, Algorithm } from '../api';
import { config } from '../config';

interface AlgoViewProps {
  prediction: PredictionResponse;
  editable?: boolean;
  onAlgorithmUpdate?: (algo: Algorithm) => void;
}

export const AlgoView: React.FC<AlgoViewProps> = ({ prediction, editable = false, onAlgorithmUpdate }) => {
  const { algorithm, graph } = prediction;
  const [generatedCode, setGeneratedCode] = useState<string>('');
  const [codeType, setCodeType] = useState<'pseudocode' | 'python' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editText, setEditText] = useState('');

  const handleDownloadJson = () => {
    const data = {
      steps: algorithm.steps,
      structured: algorithm.structured
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'algorithm.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const generateWithLLM = async (type: 'pseudocode' | 'python') => {
    setIsLoading(true);
    setCodeType(type);
    
    const algoJson = JSON.stringify({
      steps: algorithm.steps,
      structured: algorithm.structured
    }, null, 2);

    const prompt = type === 'pseudocode' 
      ? `Преобразуй следующий JSON алгоритма в чистый псевдокод на русском языке. 
Используй стандартные конструкции: НАЧАЛО, КОНЕЦ, ЕСЛИ-ТО-ИНАЧЕ, ПОКА, ДЛЯ.
Выведи только псевдокод без пояснений.

JSON алгоритма:
${algoJson}`
      : `Преобразуй следующий JSON алгоритма в работающий Python код.
Создай функцию process_algorithm() которая реализует логику алгоритма.
Добавь комментарии на русском языке. Выведи только код без пояснений.

JSON алгоритма:
${algoJson}`;

    try {
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.OPENROUTER_API_KEY}`,
        },
        body: JSON.stringify({
          model: 'openai/gpt-4o-mini',
          messages: [
            { role: 'user', content: prompt }
          ]
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || `HTTP ${response.status}: ${JSON.stringify(data)}`);
      }
      
      const content = data.choices?.[0]?.message?.content || 'Ошибка генерации: пустой ответ от API';
      setGeneratedCode(content);
    } catch (error) {
      setGeneratedCode('Ошибка при обращении к API: ' + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedCode);
  };

  const handleStepEdit = (index: number) => {
    if (!editable) return;
    setEditingIndex(index);
    setEditText(algorithm.steps[index]);
  };

  const handleStepSave = () => {
    if (editingIndex === null || !onAlgorithmUpdate) return;
    
    const newSteps = [...algorithm.steps];
    newSteps[editingIndex] = editText;
    
    onAlgorithmUpdate({
      ...algorithm,
      steps: newSteps
    });
    
    setEditingIndex(null);
    setEditText('');
  };

  const handleStepCancel = () => {
    setEditingIndex(null);
    setEditText('');
  };

  const handleAddStep = (afterIndex: number) => {
    if (!onAlgorithmUpdate) return;
    
    const newSteps = [...algorithm.steps];
    newSteps.splice(afterIndex + 1, 0, 'Новый шаг');
    
    onAlgorithmUpdate({
      ...algorithm,
      steps: newSteps
    });
  };

  const handleDeleteStep = (index: number) => {
    if (!onAlgorithmUpdate) return;
    
    const newSteps = algorithm.steps.filter((_, i) => i !== index);
    
    onAlgorithmUpdate({
      ...algorithm,
      steps: newSteps
    });
  };

  if (!algorithm || !algorithm.steps || algorithm.steps.length === 0) {
    return (
      <div className="result-card glass-card">
        <h3 className="result-card-title">
          <span className="icon">
            <img src="/src/icons/procedure.svg" alt="algo" width="20" height="20" />
          </span>
          Алгоритм
        </h3>
        <div className="empty-state">
          <p>Алгоритм не удалось извлечь</p>
        </div>
      </div>
    );
  }

  const renderStep = (step: string, index: number) => {
    const isDecision = step.startsWith('ЕСЛИ ') || step.includes('[Да]') || step.includes('[Нет]');
    const isEnd = step.startsWith('КОНЕЦ') || step.startsWith('КОНЕЦ_ЕСЛИ');
    const isStart = step.startsWith('НАЧАЛО');
    const isBranch = step.trim().startsWith('[');
    
    const indent = step.match(/^(\s*)/)?.[1].length || 0;
    const indentLevel = Math.floor(indent / 2);
    
    const cleanText = step.trim();
    
    let stepClass = 'algo-step';
    let label = `Шаг ${index + 1}`;
    
    if (isDecision && cleanText.startsWith('ЕСЛИ')) {
      stepClass = 'algo-step decision';
      label = 'Условие';
    } else if (isStart) {
      label = 'Старт';
    } else if (isEnd && !cleanText.includes('КОНЕЦ_ЕСЛИ')) {
      label = 'Финал';
    } else if (cleanText === 'КОНЕЦ_ЕСЛИ') {
      return null;
    } else if (isBranch) {
      stepClass = 'algo-step branch';
      label = 'Ветка';
    }

    const isEditing = editingIndex === index;
    
    return (
      <div 
        key={index} 
        className={`${stepClass} ${editable ? 'editable' : ''} ${isEditing ? 'editing' : ''}`}
        style={{ marginLeft: `${indentLevel * 16}px` }}
      >
        {isEditing ? (
          <div className="step-edit-form">
            <input 
              type="text"
              value={editText}
              onChange={e => setEditText(e.target.value)}
              autoFocus
            />
            <div className="step-edit-actions">
              <button className="step-btn save" onClick={handleStepSave}>
                <img src="/src/icons/check.svg" alt="save" width="14" height="14" />
              </button>
              <button className="step-btn cancel" onClick={handleStepCancel}>
                <img src="/src/icons/close.svg" alt="cancel" width="14" height="14" />
              </button>
            </div>
          </div>
        ) : (
          <>
        <div className="algo-step-number">{label}</div>
            <div className="algo-step-text" onClick={() => handleStepEdit(index)}>
              {cleanText}
            </div>
            {editable && (
              <div className="step-actions">
                <button 
                  className="step-btn edit" 
                  onClick={() => handleStepEdit(index)}
                  title="Редактировать"
                >
                  <img src="/src/icons/edit.svg" alt="edit" width="14" height="14" />
                </button>
                <button 
                  className="step-btn add" 
                  onClick={() => handleAddStep(index)}
                  title="Добавить шаг"
                >
                  +
                </button>
                <button 
                  className="step-btn delete" 
                  onClick={() => handleDeleteStep(index)}
                  title="Удалить"
                >
                  ×
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <div className="result-card glass-card">
      <div className="result-card-header">
        <h3 className="result-card-title">
          <span className="icon">
            <img src="/src/icons/procedure.svg" alt="algo" width="20" height="20" />
          </span>
          {editable ? 'Редактор алгоритма' : 'Извлечённый алгоритм'}
        </h3>
        <button className="download-btn" onClick={handleDownloadJson}>
          Скачать JSON
        </button>
      </div>

      {editable && (
        <div className="editor-hint algo-hint">
          Кликните по шагу для редактирования
        </div>
      )}
      
      <div className="algo-container">
        {algorithm.steps.map((step, index) => renderStep(step, index))}
      </div>

      <div className="generate-section">
        <div className="generate-title">Генерация кода</div>
        <div className="generate-buttons">
          <button 
            className={`generate-btn ${codeType === 'pseudocode' ? 'active' : ''}`}
            onClick={() => generateWithLLM('pseudocode')}
            disabled={isLoading}
          >
            Псевдокод
          </button>
          <button 
            className={`generate-btn ${codeType === 'python' ? 'active' : ''}`}
            onClick={() => generateWithLLM('python')}
            disabled={isLoading}
          >
            Python
          </button>
        </div>

        {isLoading && (
          <div className="generate-loading">
            <div className="spinner-small"></div>
            <span>Генерация...</span>
          </div>
        )}

        {generatedCode && !isLoading && (
          <div className="generated-code-block">
            <div className="generated-code-header">
              <span>{codeType === 'pseudocode' ? 'Псевдокод' : 'Python'}</span>
              <button className="copy-btn" onClick={copyToClipboard}>
                Копировать
              </button>
            </div>
            <pre className="generated-code">{generatedCode}</pre>
          </div>
        )}
      </div>

      {graph && graph.nodes && (
        <div className="graph-stats">
          <div className="graph-stats-title">Статистика графа</div>
          <div className="graph-stats-items">
            <span className="stat-item">{graph.nodes.length} узлов</span>
            <span className="stat-item">{graph.edges?.length || 0} связей</span>
            {graph.decisions && graph.decisions.length > 0 && (
              <span className="stat-item highlight">{graph.decisions.length} условий</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
