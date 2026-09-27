from app.facts.extract import extract_facts


def make_data(commits=0, prs=0, reviews=0, issues=0, pr_nodes=None):
    """Build a fake GitHub response in the same shape the connector returns."""
    return {
        "contributionsCollection": {
            "totalCommitContributions": commits,
            "totalPullRequestContributions": prs,
            "totalPullRequestReviewContributions": reviews,
            "totalIssueContributions": issues,
            "restrictedContributionsCount": 0,
            "pullRequestContributions": {"nodes": pr_nodes or []},
        }
    }


def make_pr(title, number, private=False, merged=True):
    return {
        "pullRequest": {
            "title": title,
            "url": f"https://github.com/me/repo/pull/{number}",
            "merged": merged,
            "createdAt": "2026-09-20T10:00:00Z",
            "repository": {"nameWithOwner": "me/repo", "isPrivate": private},
        }
    }


def facts_by_id(facts):
    return {f.id: f for f in facts}


def test_singular_and_plural():
    facts = facts_by_id(extract_facts(make_data(commits=1, prs=5), make_data(), 7))
    assert (
        facts["count_totalCommitContributions"].statement
        == "1 commit in the last 7 days"
    )
    assert (
        facts["count_totalPullRequestContributions"].statement
        == "5 pull requests in the last 7 days"
    )


def test_change_wording():
    facts = facts_by_id(extract_facts(make_data(prs=30), make_data(prs=12), 7))
    assert facts["change_totalPullRequestContributions"].statement == (
        "18 more pull requests than the previous 7 days (12 to 30)"
    )


def test_no_change_fact_when_equal():
    facts = facts_by_id(extract_facts(make_data(commits=3), make_data(commits=3), 7))
    assert "change_totalCommitContributions" not in facts


def test_private_pr_details_never_exposed():
    nodes = [make_pr("Secret company feature", 1, private=True)]
    facts = extract_facts(make_data(prs=1, pr_nodes=nodes), make_data(), 7)
    all_text = " ".join(f.statement for f in facts)
    assert "Secret company feature" not in all_text


def test_private_split_fact():
    nodes = [make_pr("Public work", 1)]
    facts = facts_by_id(
        extract_facts(make_data(prs=30, pr_nodes=nodes), make_data(), 7)
    )
    assert facts["split_private_prs"].statement == (
        "29 of the 30 pull requests were in private repositories (details not shared)"
    )


def test_public_pr_highlight_has_source():
    nodes = [make_pr("Add connector", 1)]
    facts = facts_by_id(extract_facts(make_data(prs=1, pr_nodes=nodes), make_data(), 7))
    highlight = facts["pr_me/repo_1"]
    assert highlight.sources == ["https://github.com/me/repo/pull/1"]
