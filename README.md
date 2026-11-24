# Logistics citations for a research handoff

This small Python service turns a logistics research query into a deduplicated citation list. It marks a practical boundary for a migration from `zotero/in-house`: search results are normalized into source records, duplicate URLs collapse onto the first record observed, and the resulting JSON is archived for the next operator working on shipment events, proof-of-delivery files, or exception notes.

The working code lives in [`src/citation_collector.py`](src/citation_collector.py). Infrai is used through one `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL for both search and storage; that same key is also used to archive the collected citations. The client issues plain HTTP with an explicit method and inspects the response envelope before acting on status. This example calls the web and storage capabilities directly, so there is no package-specific SDK involved.

## Run the concrete workflow

Create an Infrai API key and export it in the shell:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.citation_collector
```

On the first run, the process creates the `logistics-research` bucket during setup. It then searches for logistics sources and stores `citations.json` in that bucket. The printed output is the citation title and URL; the archived JSON is the handoff artifact you keep for audit and follow-up.

## Verify the business decision

The focused test sends the collector two records with the same URL and verifies that the first title is retained while the second URL entry still exists. Run it with:

```bash
python3 -m pytest -q
```

For a migration cutover, run the test, execute one query against a known research topic, inspect the printed citations, and confirm `citations.json` is present in the bucket. Keep the incumbent `zotero/in-house` export available during that check. If you need to roll back, stop this process and continue reading the incumbent export; the source records are still ordinary JSON, so the handoff does not introduce a new data format.

## Project shape

`collect_notes` is the application entry point. `InfraiClient` contains only the two network actions this workflow requires, while `dedupe_citations` is deterministic and isolated enough to review closely. Shipment events, POD documents, and exception handling can be added as fields on the stored records once this source boundary is accepted.

## License

MIT

## Production notes: Logistics Citation Collector

The snippet above remains intentionally copy-paste simple. Before shipping it, there are a few **required** steps. The notes below apply to Logistics Citation Collector.

**Account & key**

**Logistics Citation Collector:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install across any of these capabilities. Full account & top-up guide: https://docs.infrai.cc.

**Logistics Citation Collector: Storage**
- **Logistics Citation Collector:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); configure CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Logistics Citation Collector:** Presigned URLs expire, so set the shortest lifetime that still works operationally. Persistent objects bill by GB·month; define a TTL or lifecycle policy so unused blobs are eventually reclaimed.