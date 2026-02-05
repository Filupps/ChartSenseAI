import React, { useState, useRef } from 'react';
import { saveDiagramGeneration, getSessionId } from '../api';
import { config } from '../config';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const AlgoToDiagram: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [plantUmlCode, setPlantUmlCode] = useState('');
  const [diagramUrl, setDiagramUrl] = useState('');
  const [attachedFile, setAttachedFile] = useState<{ name: string; content: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const encodePlantUml = (code: string): string => {
    const bytes = new TextEncoder().encode(code);
    let hex = '';
    for (let i = 0; i < bytes.length; i++) {
      hex += bytes[i].toString(16).padStart(2, '0');
    }
    return '~h' + hex;
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setAttachedFile({ name: file.name, content });
    };
    reader.readAsText(file);
  };

  const removeAttachment = () => {
    setAttachedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const generateDiagram = async (userMessage: string) => {
    setIsLoading(true);
    const startTime = Date.now();
    
    let fullPrompt = userMessage;
    const currentAttachedFile = attachedFile;
    if (currentAttachedFile) {
      fullPrompt += `\n\nПрикреплённый файл "${currentAttachedFile.name}":\n\`\`\`\n${currentAttachedFile.content}\n\`\`\``;
    }

    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setInput('');

    const systemPrompt = `Ты эксперт по созданию PlantUML диаграмм. Генерируй ТОЛЬКО валидный PlantUML код.

СТРОГИЕ ПРАВИЛА СИНТАКСИСА:
1. Действия: :Текст действия;  (двоеточие в начале, точка с запятой в конце)
2. Условия: if (Условие?) then (да) ... else (нет) ... endif
3. start - начало БЕЗ текста
4. stop - конец БЕЗ текста
5. Если нужен текст перед концом: :Завершено; потом stop на новой строке
6. НИКОГДА не пиши stop "текст" - это ошибка!

Формат ответа - ТОЛЬКО код:
\`\`\`plantuml
@startuml
start
:Первое действие;
if (Проверка?) then (да)
  :Действие при да;
else (нет)
  :Действие при нет;
endif
:Финальное действие;
stop
@enduml
\`\`\``;

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
            { role: 'system', content: systemPrompt },
            ...newMessages.map(m => ({ role: m.role, content: m.content })),
            { role: 'user', content: fullPrompt }
          ]
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || `HTTP ${response.status}: ${JSON.stringify(data)}`);
      }
      
      const assistantMessage = data.choices?.[0]?.message?.content || 'Ошибка генерации: пустой ответ от API';
      
      setMessages([...newMessages, { role: 'assistant', content: assistantMessage }]);

      const plantUmlMatch = assistantMessage.match(/```plantuml\n([\s\S]*?)```/);
      if (plantUmlMatch) {
        const code = plantUmlMatch[1].trim();
        setPlantUmlCode(code);
        
        const encoded = encodePlantUml(code);
        const generatedUrl = `https://www.plantuml.com/plantuml/svg/${encoded}`;
        setDiagramUrl(generatedUrl);

        try {
          await saveDiagramGeneration({
            session_id: getSessionId(),
            input_type: currentAttachedFile ? 'file' : 'text',
            input_text: userMessage,
            input_file_name: currentAttachedFile?.name,
            input_file_content: currentAttachedFile?.content,
            plantuml_code: code,
            diagram_url: generatedUrl,
            llm_model: 'openrouter',
            generation_time_ms: Date.now() - startTime
          });
        } catch (dbError) {
          console.warn('Failed to save to database:', dbError);
        }
      }

      setAttachedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setMessages([...newMessages, { 
        role: 'assistant', 
        content: 'Ошибка при обращении к API: ' + (error as Error).message 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !attachedFile) return;
    generateDiagram(input.trim() || 'Сгенерируй диаграмму на основе прикреплённого файла');
  };

  const downloadDiagram = async (format: 'svg' | 'png') => {
    if (!plantUmlCode) return;
    
    const encoded = encodePlantUml(plantUmlCode);
    const url = `https://www.plantuml.com/plantuml/${format}/${encoded}`;
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagram.${format}`;
    a.click();
  };

  return (
    <div className="algo-to-diagram">
      <div className="chat-container glass-card">
        <div className="chat-header">
          <div className="chat-header-title">
            <div className="header-icon">
              <img src="/src/icons/ask.svg" alt="ask" width="24" height="24" />
            </div>
            <h3>Генерация диаграммы из алгоритма</h3>
          </div>
          <p>Опишите алгоритм или прикрепите JSON/Python файл</p>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-placeholder">
              <div className="placeholder-icon-wrapper">
                <img src="/src/icons/ask.svg" alt="ask" width="48" height="48" />
              </div>
              <p>Опишите алгоритм, который нужно визуализировать</p>
              <div className="placeholder-examples">
                <span>Примеры:</span>
                <button onClick={() => setInput('Алгоритм авторизации пользователя: проверка логина и пароля, если верно - вход в систему, иначе - ошибка')}>
                  Авторизация
                </button>
                <button onClick={() => setInput('Алгоритм сортировки пузырьком для массива чисел')}>
                  Сортировка
                </button>
              </div>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.role}`}>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <pre>{msg.content}</pre>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-message assistant">
              <div className="message-content loading">
                <div className="spinner-small"></div>
                <span>Генерация диаграммы...</span>
              </div>
            </div>
          )}
        </div>

        <form className="chat-input-form" onSubmit={handleSubmit}>
          {attachedFile && (
            <div className="attached-file">
              <span className="file-name">{attachedFile.name}</span>
              <button type="button" className="remove-file" onClick={removeAttachment}>×</button>
            </div>
          )}
          <div className="chat-input-row">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileAttach}
              accept=".json,.py,.txt"
              style={{ display: 'none' }}
            />
            <button 
              type="button" 
              className="attach-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Прикрепить файл"
            >
              <img src="/src/icons/clip.svg" alt="attach" width="20" height="20" />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Опишите алгоритм..."
              disabled={isLoading}
            />
            <button type="submit" className="send-btn" disabled={isLoading || (!input.trim() && !attachedFile)}>
              →
            </button>
          </div>
        </form>
      </div>

      <div className="diagram-result glass-card">
        <div className="diagram-header">
          <div className="diagram-header-title">
            <div className="header-icon">
              <img src="/src/icons/chart.svg" alt="chart" width="20" height="20" />
            </div>
            <h3>Результат</h3>
          </div>
          {diagramUrl && (
            <div className="diagram-actions">
              <button onClick={() => downloadDiagram('svg')}>SVG</button>
              <button onClick={() => downloadDiagram('png')}>PNG</button>
            </div>
          )}
        </div>

        <div className="diagram-preview">
          {diagramUrl ? (
            <img src={diagramUrl} alt="Generated diagram" />
          ) : (
            <div className="diagram-placeholder">
              <p>Здесь появится сгенерированная диаграмма</p>
            </div>
          )}
        </div>

        {plantUmlCode && (
          <div className="plantuml-code">
            <div className="code-header">
              <span>PlantUML код</span>
              <button onClick={() => navigator.clipboard.writeText(plantUmlCode)}>
                Копировать
              </button>
            </div>
            <pre>{plantUmlCode}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
