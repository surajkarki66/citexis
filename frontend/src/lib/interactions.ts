import { recordInteraction } from "../api/client";
import { getUserId } from "./userId";

export function recordPaperClick(paperId: string): void {
  if (!paperId) return;
  recordInteraction({
    user_id: getUserId(),
    paper_id: paperId,
    interaction_type: "click",
  }).catch(() => undefined);
}
