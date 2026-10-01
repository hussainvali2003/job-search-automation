import json
from pathlib import Path
from datetime import datetime, timezone
from collector.core.models import Source, iso_now

def generate_phase3_registry():
    sources = [
        # P0 Tier (Highest-value active companies with frequent postings)
        Source("greenhouse_elastic", "Elastic", "greenhouse", "elastic", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_airbnb", "Airbnb", "greenhouse", "airbnb", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_stripe", "Stripe", "greenhouse", "stripe", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_datadog", "Datadog", "greenhouse", "datadog", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_phonepe", "PhonePe", "greenhouse", "phonepe", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_razorpay", "Razorpay", "greenhouse", "razorpay", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_groww", "Groww", "greenhouse", "groww", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_meesho", "Meesho", "greenhouse", "meesho", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_freshworks", "Freshworks", "greenhouse", "freshworks", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("greenhouse_chargebee", "Chargebee", "greenhouse", "chargebee", "https://boards-api.greenhouse.io/v1/boards", "P0", 15),
        Source("lever_palantir", "Palantir", "lever", "palantir", "https://api.lever.co/v0/postings", "P0", 15),
        Source("lever_cloudflare", "Cloudflare", "lever", "cloudflare", "https://api.lever.co/v0/postings", "P0", 15),
        Source("lever_figma", "Figma", "lever", "figma", "https://api.lever.co/v0/postings", "P0", 15),
        Source("lever_atlassian", "Atlassian", "lever", "atlassian", "https://api.lever.co/v0/postings", "P0", 15),
        Source("lever_coinbase", "Coinbase", "lever", "coinbase", "https://api.lever.co/v0/postings", "P0", 15),
        Source("ashby_linear", "Linear", "ashby", "linear", "https://api.ashbyhq.com/posting-api/job-board", "P0", 15),
        Source("ashby_ramp", "Ramp", "ashby", "ramp", "https://api.ashbyhq.com/posting-api/job-board", "P0", 15),
        Source("ashby_sentry", "Sentry", "ashby", "sentry", "https://api.ashbyhq.com/posting-api/job-board", "P0", 15),
        Source("smartrecruiters_bosch", "Bosch", "smartrecruiters", "BoschGroup", "https://api.smartrecruiters.com/v1/companies", "P0", 15),
        Source("recruitee_bunq", "Bunq", "recruitee", "bunq", "https://bunq.recruitee.com/api/offers", "P0", 15),
        Source("workable_skroutz", "Skroutz", "workable", "skroutz", "https://apply.workable.com/api/v2/accounts", "P0", 15),

        # P1 Tier (Strong potential product/SaaS/Indian tech companies)
        Source("greenhouse_postman", "Postman", "greenhouse", "postman", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("greenhouse_browserstack", "BrowserStack", "greenhouse", "browserstack", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("greenhouse_hasura", "Hasura", "greenhouse", "hasura", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("greenhouse_rubrik", "Rubrik", "greenhouse", "rubrik", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("greenhouse_couchbase", "Couchbase", "greenhouse", "couchbase", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("greenhouse_confluent", "Confluent", "greenhouse", "confluent", "https://boards-api.greenhouse.io/v1/boards", "P1", 60),
        Source("lever_deliveroo", "Deliveroo", "lever", "deliveroo", "https://api.lever.co/v0/postings", "P1", 60),
        Source("lever_cleartax", "ClearTax", "lever", "cleartax", "https://api.lever.co/v0/postings", "P1", 60),
        Source("lever_slice", "Slice", "lever", "slice", "https://api.lever.co/v0/postings", "P1", 60),
        Source("ashby_replit", "Replit", "ashby", "replit", "https://api.ashbyhq.com/posting-api/job-board", "P1", 60),
        Source("ashby_vanta", "Vanta", "ashby", "vanta", "https://api.ashbyhq.com/posting-api/job-board", "P1", 60),

        # P2 Tier (Validated remaining companies)
        Source("greenhouse_infosys", "Infosys", "greenhouse", "infosys", "https://boards-api.greenhouse.io/v1/boards", "P2", 360),
        Source("bamboohr_company", "BambooHR Sample", "bamboohr", "company", "https://company.bamboohr.com/careers/list", "P2", 360),
        Source("workable_inmobi", "InMobi", "workable", "inmobi", "https://apply.workable.com/api/v2/accounts", "P2", 360),
        Source("smartrecruiters_visa", "Visa", "smartrecruiters", "Visa", "https://api.smartrecruiters.com/v1/companies", "P2", 360),

        # P3 Tier (Low-frequency / discovery / negative test controls)
        Source("greenhouse_invalid_9999", "InvalidCorp", "greenhouse", "nonexistent_token_9999", "https://boards-api.greenhouse.io/v1/boards", "P3", 10080),
    ]

    reg_path = Path("data/source_registry.json")
    reg_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": 2,
        "generated_at": iso_now(),
        "sources": [s.to_dict() for s in sources]
    }

    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Generated expanded source_registry.json with {len(sources)} validated companies across 7 ATS platforms!")

if __name__ == "__main__":
    generate_phase3_registry()
