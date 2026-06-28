import { recordPaperClick } from "../api/client";

export function recordPaperClickSafe(paperId: string): void {
  if (!paperId) return;
  recordPaperClick(paperId).catch(() => undefined);
}
