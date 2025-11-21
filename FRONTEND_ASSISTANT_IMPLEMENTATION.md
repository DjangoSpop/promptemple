# Professional Frontend Implementation Guide for AI Assistants

## 1. Executive Summary
- Deliver a polished assistant experience that feels native to PromptCraft’s design system.
- Support real-time DeepSeek responses, Tavily RAG augmentation, and persistent threads.
- Provide a component blueprint that the frontend squad can drop into an existing React/TypeScript codebase.

## 2. User Experience Goals
- **Speed & Clarity:** Surface streaming tokens within 150 ms where possible, complimented by skeleton loaders and typing indicators.
- **Context Transparency:** Display Tavily-derived context cards, cite sources, and let users expand raw tool output.
- **Thread Continuity:** Persist conversations, show last-touch timestamps, and allow quick switching between assistants.
- **Professional Visual Design:** Adopt PromptCraft’s neutral palette, roomy spacing, accessible contrast (WCAG AA), and clear affordances for secondary actions.

## 3. High-Level Architecture
```
<AppShell>
  <Sidebar>
    <AssistantDirectory />
    <ThreadList />
  </Sidebar>
  <ConversationPane>
    <Header>
      <AssistantBadge />
      <ThreadMetadata />
    </Header>
    <MessageTimeline />
    <Composer>
      <PromptEditor />
      <ActionTray />
    </Composer>
  </ConversationPane>
  <InspectorDrawer>
    <ContextPanel />
    <UsageMetrics />
  </InspectorDrawer>
</AppShell>
```
- **State layer:** React Query (REST) + SWR/Cache for optimistic updates; Zustand or Redux Toolkit for UI state (drawer toggles, active thread).
- **Transport:** REST for listing assistants/threads; Channels WebSocket (`ws/assistant/<assistant_id>/<session_id>/`) for live replies; fallback to HTTP POST when WS unavailable.
- **Theming:** Styled-components, Tailwind, or CSS Modules—ensure tokenized spacing, typography scale, and dark-mode readiness.

## 4. Data Contracts & API Touchpoints
| Feature | Endpoint | Method | Notes |
|---------|----------|--------|-------|
| List assistants | `/api/v2/ai/assistant/` | GET | Requires auth cookie/JWT. Returns `assistants[]` + `default_assistant`. |
| Run message | `/api/v2/ai/assistant/run/` | POST | Body `{ assistant_id, message, thread_id?, metadata? }`. Returns assistant message + usage. |
| List threads | `/api/v2/ai/assistant/threads/` | GET | Filtered to authenticated user. |
| Thread detail | `/api/v2/ai/assistant/threads/<uuid>/` | GET | Includes ordered messages. |
| WebSocket stream | `ws://…/ws/assistant/<assistant_id>/<session_id>/` | WS | Payload `{ message, thread_id?, metadata? }`. Receives `assistant.message`, `assistant.error`. |

## 5. Core Components (React/TypeScript Sketch)
```tsx
function AssistantProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [sessionId] = useState(() => crypto.randomUUID());
  const [channels, setChannels] = useState<AssistantChannelMap>({});

  const openChannel = useCallback(async (assistantId: string) => {
    const socket = new WebSocket(`${WS_BASE}/ws/assistant/${assistantId}/${sessionId}/`);
    socket.addEventListener('message', (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'assistant.message') {
        queryClient.invalidateQueries(['thread', payload.data.thread_id]);
      }
    });
    setChannels((prev) => ({ ...prev, [assistantId]: socket }));
  }, [sessionId]);

  return (
    <AssistantContext.Provider value={{ sessionId, channels, openChannel }}>
      {children}
    </AssistantContext.Provider>
  );
}
```
- **AssistantDirectory:** use `useQuery(['assistants'], fetchAssistants)` to render cards. Attach tags (`general`, `code`, `tavily`) to filter.
- **ThreadList:** optimistic highlight for active thread; show unread counts via timestamp comparison.
- **MessageBubble:** differentiate roles. Tool outputs get expandable panels with copy button and “Pin to Context”.
- **PromptEditor:** rich textarea (auto-expand, slash commands for quick actions, attachments roadmap).
- **ContextPanel:** map Tavily response into cards: title, snippet, chips for reliability score (if future API). Allow toggling raw JSON for power users.

## 6. Interaction Flows
1. **Selecting an assistant**
   - Directory fetch -> highlight card -> open or create default thread -> focus composer.
2. **Sending a prompt (REST fallback)**
   - Compose -> `useMutation` POST -> optimistic user message -> await AI -> animate in assistant bubble.
3. **Real-time streaming**
   - Composer dispatch -> `channels[assistantId].send(JSON.stringify(payload))`.
   - `assistant.message` events append tokens; show streaming indicator; commit once `done` flag present.
4. **Context reveal**
   - When payload contains `context`, hydrate ContextPanel and show inline citation markers (e.g., `[1]`).
5. **Thread management**
   - Ellipsis menu: rename thread, duplicate, archive (future). Confirmation modals adopt destructive color token.

## 7. Visual & Interaction Guidelines
- **Typography:** Inter/Roboto 14–16 px body, 20–24 px headings, 12 px metadata.
- **Color:** Base `#101828`, accent `#6366F1`, neutrals `#F9FAFB` backgrounds, `#1D2939` borders. Provide dark theme tokens.
- **Feedback states:**
  - Loading: shimmer skeleton for message bubble & context cards.
  - Streaming: pulsing cursor + “Assistant is thinking…” microcopy.
  - Errors: inline toast with retry CTA; surface `assistant.error.detail` when safe.
- **Accessibility:** roving tab index in sidebar, aria-live on message timeline, ensure color contrast = 4.5:1.

## 8. State & Performance Considerations
- Cache threading data per assistant; purge on sign-out.
- Debounce composer keystrokes when hooking up future autocomplete.
- Use IntersectionObserver to lazy-load historical messages.
- Keep WebSocket connection per assistant/session; close on tab visibility change > 5 min.

## 9. Security & Compliance
- Send CSRF tokens for REST calls when using cookie auth.
- Mask secrets in logs; redact Tavily URLs if flagged private.
- Enforce rate limiting UI feedback (server already caps per settings but provide 429 handling).
- Honor GDPR: add “delete conversation” CTA that hits backend delete endpoint when implemented.

## 10. QA & Rollout Checklist
- **Unit Tests:** component tests via React Testing Library for MessageBubble, ContextPanel, Composer.
- **Integration Tests:** Cypress covering prompt send (REST + WS), context display, assistant switch.
- **Performance Budgets:** FCP < 1.5s on broadband, WebSocket connect < 500 ms.
- **Observability:** instrument `assistant_message_received` event with metadata (assistant_id, latency).
- **Feature Flags:** wrap in `FEATURE_ASSISTANT_UI` to stage rollout.

## 11. Future Enhancements
- Multi-modal uploads (images/audio) feeding new backend tooling.
- Collaborative threads with presence indicators.
- Offline draft preservation with IndexedDB.
- Plugin ecosystem (additional LangChain tools) surfaced via ActionTray chips.

---
**Appendix:** Quick Start Snippets
```bash
# Bootstrap client package
pnpm add @tanstack/react-query immer zustand

# Environment variables
cat <<EOF >> .env.local
VITE_API_BASE=/api/v2/ai
VITE_WS_BASE=ws://localhost:8000
EOF
```
```ts
// api/client.ts
export const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  withCredentials: true,
});
```
```ts
// hooks/useAssistants.ts
export function useAssistants() {
  return useQuery(['assistants'], async () => {
    const { data } = await client.get('/assistant/');
    return data;
  });
}
```
