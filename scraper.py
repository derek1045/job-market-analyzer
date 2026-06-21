from dataclasses import dataclass

from playwright.sync_api import APIRequestContext, sync_playwright

from database import get_session, init_db
from models import Job

GREENHOUSE_BOARDS = [
    {"token": "stripe", "company": "Stripe"},
    {"token": "figma", "company": "Figma"},
    {"token": "discord", "company": "Discord"},
    {"token": "airbnb", "company": "Airbnb"},
    {"token": "datadog", "company": "Datadog"},
]

LEVER_BOARDS = [
    {"token": "netflix", "company": "Netflix"},
    {"token": "spotify", "company": "Spotify"},
    {"token": "palantir", "company": "Palantir"},
]

SWE_KEYWORDS = [
    "software engineer",
    "software developer",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "sre",
    "site reliability",
    "devops",
    "platform engineer",
    "mobile engineer",
    "ios engineer",
    "android engineer",
    "staff engineer",
    "principal engineer",
    "engineering manager",
]


@dataclass
class JobRecord:
    title: str
    company: str
    location: str | None
    url: str


def is_software_engineering_role(title: str) -> bool:
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in SWE_KEYWORDS)


def fetch_greenhouse_jobs(
    request: APIRequestContext, token: str, company: str
) -> list[JobRecord]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    response = request.get(url)
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status} for {url}")

    payload = response.json()
    jobs: list[JobRecord] = []
    for job in payload.get("jobs", []):
        title = job.get("title", "")
        if not is_software_engineering_role(title):
            continue

        location_data = job.get("location") or {}
        jobs.append(
            JobRecord(
                title=title,
                company=company,
                location=location_data.get("name"),
                url=job.get("absolute_url", ""),
            )
        )
    return jobs


def fetch_lever_jobs(
    request: APIRequestContext, token: str, company: str
) -> list[JobRecord]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    response = request.get(url)
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status} for {url}")

    postings = response.json()
    jobs: list[JobRecord] = []
    for posting in postings:
        title = posting.get("text", "")
        if not is_software_engineering_role(title):
            continue

        categories = posting.get("categories") or {}
        job_url = posting.get("hostedUrl") or posting.get("applyUrl", "")
        jobs.append(
            JobRecord(
                title=title,
                company=company,
                location=categories.get("location"),
                url=job_url,
            )
        )
    return jobs


def scrape_all_boards() -> list[JobRecord]:
    all_jobs: list[JobRecord] = []

    with sync_playwright() as playwright:
        request = playwright.request.new_context()

        for board in GREENHOUSE_BOARDS:
            token = board["token"]
            company = board["company"]
            try:
                jobs = fetch_greenhouse_jobs(request, token, company)
                print(f"[Greenhouse] {company}: found {len(jobs)} software engineering jobs")
                all_jobs.extend(jobs)
            except Exception as exc:
                print(f"[Greenhouse] {company}: skipped ({exc})")

        for board in LEVER_BOARDS:
            token = board["token"]
            company = board["company"]
            try:
                jobs = fetch_lever_jobs(request, token, company)
                print(f"[Lever] {company}: found {len(jobs)} software engineering jobs")
                all_jobs.extend(jobs)
            except Exception as exc:
                print(f"[Lever] {company}: skipped ({exc})")

        request.dispose()

    return all_jobs


def save_jobs(jobs: list[JobRecord]) -> dict[str, int]:
    inserted = 0
    updated = 0
    skipped = 0

    with get_session() as session:
        for job in jobs:
            if not job.url:
                skipped += 1
                continue

            existing = session.query(Job).filter_by(url=job.url).one_or_none()
            if existing is None:
                session.add(
                    Job(
                        title=job.title,
                        company=job.company,
                        location=job.location,
                        url=job.url,
                    )
                )
                inserted += 1
            elif (
                existing.title != job.title
                or existing.company != job.company
                or existing.location != job.location
            ):
                existing.title = job.title
                existing.company = job.company
                existing.location = job.location
                updated += 1
            else:
                skipped += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def main():
    init_db()
    jobs = scrape_all_boards()
    print(f"\nTotal matching jobs scraped: {len(jobs)}")

    counts = save_jobs(jobs)
    print(
        f"Saved: {counts['inserted']} inserted, "
        f"{counts['updated']} updated, "
        f"{counts['skipped']} unchanged/skipped"
    )


if __name__ == "__main__":
    main()
