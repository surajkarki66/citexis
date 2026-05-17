from motor.motor_asyncio import AsyncIOMotorDatabase


class CitationGraphRecommender:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db["papers"]

  async def recommend(self, paper_id: str, min_overlap: int = 2, limit: int = 20) -> list[str]:
      """Papers sharing >= min_overlap citations with the seed paper."""
      from bson import ObjectId

      paper = await self._col.find_one({"_id": ObjectId(paper_id)})
      if not paper:
          return []
      citations = set(paper.get("citations", []))
      if not citations:
          return []

      pipeline = [
          {"$match": {"_id": {"$ne": ObjectId(paper_id)}, "citations": {"$in": list(citations)}}},
          {
              "$addFields": {
                  "overlap": {
                      "$size": {
                          "$setIntersection": ["$citations", list(citations)],
                      }
                  }
              }
          },
          {"$match": {"overlap": {"$gte": min_overlap}}},
          {"$sort": {"overlap": -1}},
          {"$limit": limit},
      ]
      cursor = self._col.aggregate(pipeline)
      rows = await cursor.to_list(length=limit)
      return [str(r["_id"]) for r in rows]
