export type SourceType = "pdf" | "web";

export type DocumentItem = {
  id: number;
  title: string;
  source_type: SourceType;
  source_path: string;
  status: string;
  created_at: string;
  chunk_count: number;
};

export type ChunkItem = {
  id: number;
  document_id: number;
  chunk_text: string;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
  metadata_json: string;
  created_at: string;
};

export type DocumentDetail = DocumentItem & {
  chunks: ChunkItem[];
};

export type Citation = {
  chunk_id: number;
  document_id: number;
  document_title: string;
  page_number: number | null;
  source_type: SourceType;
  source_path: string;
};

export type RetrievedChunk = {
  chunk_id: number;
  document_id: number;
  document_title: string;
  chunk_text: string;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
  score: number;
  source_type: SourceType;
  source_path: string;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  query_log_id: number;
  created_at: string;
};

export type EvalCase = {
  id: number;
  question: string;
  reference_answer: string;
  expected_document_id: number | null;
  expected_page_numbers: number[];
  notes: string | null;
  created_at: string;
};

export type EvalResult = {
  id: number;
  eval_case_id: number;
  question: string;
  reference_answer: string;
  expected_document_id: number | null;
  expected_page_numbers: number[];
  retrieved_chunk_ids: number[];
  answer_text: string;
  citation_json: Citation[];
  retrieval_hit: boolean;
  citation_correct: boolean;
  answer_score: number;
  created_at: string;
};

export type EvalRunResponse = {
  total_cases: number;
  results: EvalResult[];
};
