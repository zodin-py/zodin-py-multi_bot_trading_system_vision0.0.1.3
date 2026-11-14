import { HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  inject,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { interval, Subscription } from 'rxjs';

import {
  RagAnalysis,
  RagChatTurn,
  RagCitation,
  RagSource,
  RagStatusResponse,
} from '../shared/models/api.models';
import { ApiService } from '../shared/services/api.service';

interface ChatMessage extends RagChatTurn {
  id: number;
  status?: 'grounded' | 'insufficient_information' | 'error';
  sources?: RagCitation[];
  analysis?: RagAnalysis;
  analysisLoading?: boolean;
}

@Component({
  selector: 'app-llm-copilot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './llm-copilot.component.html',
  styleUrl: './llm-copilot.component.css',
})
export class LlmCopilotComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private syncTimer?: Subscription;

  messages: ChatMessage[] = [];
  sources: RagSource[] = [];
  status: RagStatusResponse | null = null;
  draft = '';
  loading = false;
  syncing = false;
  error: string | null = null;

  ngOnInit(): void {
    this.refreshStatus();
    this.syncTimer = interval(60_000).subscribe(() => this.syncSources(true));
  }

  ngOnDestroy(): void {
    this.syncTimer?.unsubscribe();
  }

  syncSources(silent = false): void {
    if (this.syncing) return;
    this.syncing = true;
    if (!silent) this.error = null;
    this.api.syncRagSources().subscribe({
      next: () => {
        this.syncing = false;
        this.refreshStatus();
      },
      error: (error: unknown) => {
        this.syncing = false;
        const errorMessage = this.getErrorMessage(
          error,
          'Wissensquellen konnten nicht synchronisiert werden.',
        );
        if (silent) {
          if (!(error instanceof HttpErrorResponse) || error.error?.status !== 'no_data') {
            console.error('Automatic RAG source synchronization failed:', error);
            this.error = errorMessage;
          }
        } else {
          this.error = errorMessage;
        }
        this.refreshStatus(false);
      },
    });
  }

  send(): void {
    const question = this.draft.trim();
    if (!question || this.loading) return;

    const history: RagChatTurn[] = this.messages
      .filter((message) => message.status !== 'error')
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));
    this.messages = [
      ...this.messages,
      { id: Date.now(), role: 'user', content: question },
    ];
    this.draft = '';
    this.loading = true;
    this.error = null;

    this.api.sendRagChat(question, history).subscribe({
      next: (response) => {
        this.loading = false;
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.answer,
          status: response.status,
          sources: response.sources,
          analysisLoading: Boolean(response.request_id),
        };
        this.messages = [...this.messages, assistantMessage];
        this.changeDetector.markForCheck();
        this.refreshStatus();
        if (response.request_id) {
          this.loadAnalysis(assistantMessage, response.request_id);
        }
      },
      error: (error: unknown) => {
        this.loading = false;
        const requestId = this.getRequestId(error);
        const errorMessage: ChatMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: this.getErrorMessage(
            error,
            'Die Anfrage konnte nicht beantwortet werden.',
          ),
          status: 'error',
          analysisLoading: Boolean(requestId),
        };
        this.messages = [...this.messages, errorMessage];
        this.changeDetector.markForCheck();
        if (requestId) this.loadAnalysis(errorMessage, requestId);
      },
    });
  }

  useSuggestion(question: string): void {
    this.draft = question;
    this.send();
  }

  onEnter(event: Event): void {
    if (!(event instanceof KeyboardEvent) || event.shiftKey) return;
    event.preventDefault();
    this.send();
  }

  clearChat(): void {
    if (!this.loading) this.messages = [];
  }

  trackMessage(_index: number, message: ChatMessage): number {
    return message.id;
  }

  private loadAnalysis(message: ChatMessage, requestId: string): void {
    this.api.getRagAnalysis(requestId).subscribe({
      next: (response) => {
        this.messages = this.messages.map((item) =>
          item.id === message.id
            ? { ...item, analysis: response.analysis, analysisLoading: false }
            : item,
        );
        this.changeDetector.markForCheck();
      },
      error: () => {
        this.messages = this.messages.map((item) =>
          item.id === message.id ? { ...item, analysisLoading: false } : item,
        );
        this.changeDetector.markForCheck();
      },
    });
  }

  private refreshStatus(clearError = true): void {
    this.api.getRagStatus().subscribe({
      next: (status) => {
        this.status = status;
        this.sources = status.system_info.source_files ?? [];
        if (clearError) this.error = null;
        this.changeDetector.markForCheck();
      },
      error: (error: unknown) => {
        if (clearError) {
          this.error = this.getErrorMessage(
            error,
            'RAG-Status konnte nicht geladen werden.',
          );
        }
        this.changeDetector.markForCheck();
      },
    });
  }

  private getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const message = error.error?.error ?? error.error?.message;
      return typeof message === 'string' ? message : fallback;
    }
    return fallback;
  }

  private getRequestId(error: unknown): string | null {
    if (error instanceof HttpErrorResponse) {
      const requestId = error.error?.request_id;
      return typeof requestId === 'string' ? requestId : null;
    }
    return null;
  }
}
