from careeros.ranking.schema import RankedShortlist, RankedItem

def test_ranked_shortlist_schema():
    s = RankedShortlist(run_id="1", profile_path="p.json", items=[RankedItem(job_path="j.json", score=50.0)])
    assert s.top_n == 3
    assert s.items[0].score == 50.0
