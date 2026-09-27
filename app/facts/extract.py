from pydantic import BaseModel

COUNT_FIELDS = {
    "totalCommitContributions": "commits",
    "totalPullRequestContributions": "pull requests",
    "totalPullRequestReviewContributions": "code reviews",
    "totalIssueContributions": "issues",
}


class Fact(BaseModel):
    id: str
    kind: str  # "count", "change", or "highlight"
    statement: str  # human-readable fact the LLM can use
    value: int | None = None
    sources: list[str] = []  # PR/commit URLs (the receipts)


def extract_facts(current: dict, previous: dict, days: int) -> list[Fact]:
    cur = current["contributionsCollection"]
    prev = previous["contributionsCollection"]
    facts: list[Fact] = []

    # Totals and period-over-period changes
    for field, label in COUNT_FIELDS.items():
        now, before = cur[field], prev[field]

        if now > 0:
            facts.append(
                Fact(
                    id=f"count_{field}",
                    kind="count",
                    statement=f"{plural(now, label)} in the last {days} days",
                    value=now,
                )
            )

        if now != before:
            diff = now - before
            direction = "more" if diff > 0 else "fewer"
            facts.append(
                Fact(
                    id=f"change_{field}",
                    kind="change",
                    statement=(
                        f"{abs(diff)} {direction} {label if abs(diff) != 1 else label[:-1]} "
                        f"than the previous {days} days ({before} to {now})"
                    ),
                    value=diff,
                )
            )

    # Public PR highlights (private repos are never exposed)
    nodes = cur["pullRequestContributions"]["nodes"]
    for node in cur["pullRequestContributions"]["nodes"]:
        pr = node["pullRequest"]
        repo = pr["repository"]
        if repo["isPrivate"]:
            continue
        status = "Merged" if pr["merged"] else "Opened"
        pr_number = pr["url"].rstrip("/").rsplit("/", 1)[-1]
        facts.append(
            Fact(
                id=f"pr_{repo['nameWithOwner']}_{pr_number}",
                kind="highlight",
                statement=f"{status} PR '{pr['title']}' in {repo['nameWithOwner']}",
                sources=[pr["url"]],
            )
        )

    public_prs = sum(
        1 for node in nodes if not node["pullRequest"]["repository"]["isPrivate"]
    )
    total_prs = cur["totalPullRequestContributions"]
    private_prs = total_prs - public_prs
    if private_prs > 0:
        facts.append(
            Fact(
                id="split_private_prs",
                kind="context",
                statement=(
                    f"{private_prs} of the {total_prs} pull requests were in "
                    f"private repositories (details not shared)"
                ),
                value=private_prs,
            )
        )

    return facts


def plural(count: int, word: str) -> str:
    """Return '1 commit' or '5 commits'."""
    if count == 1 and word.endswith("s"):
        word = word[:-1]
    return f"{count} {word}"
