from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

GRAPHQL_URL = f"{settings.github_api_url}/graphql"

CONTRIBUTIONS_QUERY = """
query($from: DateTime!, $to: DateTime!) {
  viewer {
    login
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
      pullRequestContributions(first: 20) {
        nodes {
          pullRequest {
            title
            url
            merged
            createdAt
            repository {
              nameWithOwner
              isPrivate
            }
          }
        }
      }
    }
  }
}
"""

async def fetch_contributions(days: int = 7, offset_days: int = 0) -> dict:
    """Fetch contributions for a window of `days`, ending `offset_days` ago."""
    to_date = datetime.now(timezone.utc) - timedelta(days=offset_days)
    from_date = to_date - timedelta(days=days)

    headers = {
        "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": CONTRIBUTIONS_QUERY,
        "variables": {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GRAPHQL_URL, json=payload, headers=headers)

    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")

    viewer = data["data"]["viewer"]
    prs = viewer["contributionsCollection"]["pullRequestContributions"]
    prs["nodes"] = [node for node in prs["nodes"] if node and node.get("pullRequest")]
    return viewer