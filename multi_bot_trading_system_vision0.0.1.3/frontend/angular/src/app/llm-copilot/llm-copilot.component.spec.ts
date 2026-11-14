import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ApiService } from '../shared/services/api.service';
import { RagAnalysis, RagStatusResponse } from '../shared/models/api.models';
import { LlmCopilotComponent } from './llm-copilot.component';

const readyStatus: RagStatusResponse = {
  success: true,
  status: 'ready',
  system_info: {
    is_built: true,
    source_files: [{ source_file: 'coins.json', record_count: 1 }],
    num_chunks: 1,
    chat_configured: true,
    embedding_model: 'local-hash-ngram-v1',
    keyword_stats: { num_documents: 1 },
    vector_stats: { num_documents: 1 },
  },
};

const analysis: RagAnalysis = {
  request_id: 'request-1',
  query: 'Was ist Bitcoin?',
  search_query: 'Was ist Bitcoin?',
  retrieval_parameters: {
    top_k: 5,
    keyword_weight: 0.5,
    vector_weight: 0.5,
    embedding_model: 'local-hash-ngram-v1',
  },
  keyword_results: [],
  vector_results: [],
  combined_results: [],
  context_documents: [],
  context_characters: 40,
  retrieval_ms: 2,
  claude_ms: 10,
  response: {
    answer: 'Bitcoin wird in der Quelle beschrieben.',
    status: 'grounded',
    sources: [
      { source_file: 'coins.json', record_id: 'btc', citation_id: 'coins.json#btc' },
    ],
    insufficient_information: false,
  },
};

const apiServiceMock = {
  getRagStatus: () => of(readyStatus),
  syncRagSources: () => of({ success: true, status: 'success', message: 'updated' }),
  sendRagChat: () =>
    of({
      success: true,
      request_id: 'request-1',
      answer: 'Bitcoin wird in der Quelle beschrieben.',
      status: 'grounded' as const,
      sources: [
        { source_file: 'coins.json', record_id: 'btc', citation_id: 'coins.json#btc' },
      ],
      insufficient_information: false,
    }),
  getRagAnalysis: () => of({ success: true, analysis }),
};

describe('LlmCopilotComponent', () => {
  beforeEach(async () => {
    apiServiceMock.getRagStatus = () => of(readyStatus);
    apiServiceMock.sendRagChat = () =>
      of({
        success: true,
        request_id: 'request-1',
        answer: 'Bitcoin wird in der Quelle beschrieben.',
        status: 'grounded',
        sources: [
          { source_file: 'coins.json', record_id: 'btc', citation_id: 'coins.json#btc' },
        ],
        insufficient_information: false,
      });
    apiServiceMock.getRagAnalysis = () => of({ success: true, analysis });

    await TestBed.configureTestingModule({
      imports: [LlmCopilotComponent],
      providers: [{ provide: ApiService, useValue: apiServiceMock }],
    }).compileComponents();
  });

  it('shows index, source, and Claude status', () => {
    const fixture = TestBed.createComponent(LlmCopilotComponent);
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Index bereit');
    expect(text).toContain('Claude verbunden');
    expect(text).toContain('coins.json');
  });

  it('sends a question and displays citations and request analysis', () => {
    const fixture = TestBed.createComponent(LlmCopilotComponent);
    fixture.detectChanges();
    fixture.componentInstance.draft = 'Was ist Bitcoin?';
    fixture.componentInstance.send();
    fixture.detectChanges();

    expect(fixture.componentInstance.messages.length).toBe(2);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Was ist Bitcoin?');
    expect(text).toContain('Bitcoin wird in der Quelle beschrieben.');
    expect(text).toContain('coins.json');
    expect(text).toContain('Retrieval-Analyse');
    expect(text).toContain('local-hash-ngram-v1');
  });

  it('surfaces missing Claude configuration without inventing an answer', () => {
    apiServiceMock.sendRagChat = () =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 503,
            error: { error: 'ANTHROPIC_API_KEY fehlt.' },
          }),
      );
      const fixture = TestBed.createComponent(LlmCopilotComponent);
      fixture.detectChanges();
      fixture.componentInstance.draft = 'Was ist Bitcoin?';
      fixture.componentInstance.send();
      fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('ANTHROPIC_API_KEY fehlt.');
    expect(text).toContain('starte das Backend neu');
  });
});
