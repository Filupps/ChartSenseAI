import axios from 'axios';
import { config } from './config';

const API_BASE_URL = config.API_BASE_URL;

// Создаём axios instance с базовыми заголовками
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    ...(config.API_KEY && { 'X-API-Key': config.API_KEY }),
  },
});

const getSessionId = (): string => {
  let sessionId = localStorage.getItem('chartSenseSessionId');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('chartSenseSessionId', sessionId);
  }
  return sessionId;
};

export interface BoundingBox {
  bbox: [number, number, number, number];
  class: number;
  confidence: number;
  class_name: string;
}

export interface TextRegion {
  text: string;
  bbox: [number, number, number, number];
  class_name: string;
  confidence: number;
}

export interface GraphNode {
  id: string;
  type: string;
  text: string;
  bbox: [number, number, number, number];
  center: [number, number];
  y_position: number;
  x_position: number;
  class_name: string;
  confidence: number;
}

export interface GraphEdge {
  from: string;
  to: string;
  arrow_bbox: [number, number, number, number];
  direction: string;
  confidence: number;
  decision_branch?: string;
  branch_label?: string;
  is_loop?: boolean;
}

export interface DecisionBranch {
  to: string;
  label: string;
  direction: string;
}

export interface DecisionInfo {
  node_id: string;
  question: string;
  branches: Record<string, DecisionBranch>;
  branch_count: number;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  flow_direction: string;
  decisions: DecisionInfo[];
}

export interface StructuredStep {
  type: string;
  id: string;
  text?: string;
  condition?: string;
  then?: {
    label: string;
    steps: StructuredStep[];
  };
  else?: {
    label: string;
    steps: StructuredStep[];
  };
  after_merge?: StructuredStep[];
  merge_point?: string;
}

export interface Algorithm {
  steps: string[];
  structured: StructuredStep[];
  decisions: DecisionInfo[];
  structure: {
    total_nodes: number;
    total_edges: number;
    decision_count: number;
    visited_nodes: number;
  };
}

export interface PredictionResponse {
  bounding_boxes: {
    all: BoundingBox[];
    shapes: BoundingBox[];
    arrows: BoundingBox[];
    text_regions: BoundingBox[];
  };
  shape_texts: Record<string, TextRegion>;
  text_regions: Record<string, TextRegion>;
  graph: Graph;
  algorithm: Algorithm;
  processing_id?: number;
  session_id?: string;
  processing_time_ms?: number;
  _page_preview_base64?: string;
  pdf_pages?: number;
}

export const predictDiagram = async (file: File, page?: number): Promise<PredictionResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const params: Record<string, string> = {};
  if (page !== undefined) {
    params.page = String(page);
  }

  const response = await apiClient.post<PredictionResponse>(
    '/predict',
    formData,
    {
      params,
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-Session-Id': getSessionId(),
      },
    }
  );

  return response.data;
};

export interface DiagramGenerationData {
  session_id: string;
  input_type: string;
  input_text: string;
  input_file_name?: string;
  input_file_content?: string;
  plantuml_code: string;
  diagram_url: string;
  llm_model: string;
  generation_time_ms: number;
}

export const saveDiagramGeneration = async (data: DiagramGenerationData): Promise<void> => {
  await apiClient.post('/diagram-generation', {
    ...data,
    session_id: getSessionId()
  });
};

export interface CodeGenerationData {
  processing_id: number;
  code_type: string;
  generated_code: string;
  llm_model: string;
  generation_time_ms: number;
}

export const saveCodeGeneration = async (data: CodeGenerationData): Promise<void> => {
  await apiClient.post('/code-generation', data);
};

export const getSessionHistory = async () => {
  const response = await apiClient.get(`/session/${getSessionId()}/history`);
  return response.data;
};

export { getSessionId };
