from app.services.rag.chunker import split_text
from app.services.llm.moderation import check_input
from app.services.triage import parse_result, rule_based_triage

def test_chunker_headers_and_overlap():
    text = "# 标题A\n" + "内容甲" * 300 + "\n# 标题B\n短内容"
    chunks = split_text(text)
    assert len(chunks) >= 3 and any("标题B" in c for c in chunks)

def test_moderation_blocks_crisis():
    ok, msg = check_input("我最近想自杀")
    assert not ok and "12356" in msg
    assert check_input("我肚子疼两天了")[0]

def test_parse_triage_result():
    r = parse_result('好的。<TRIAGE_RESULT>{"department": "消化内科", "urgency": "medium", "advice": "建议就诊"}</TRIAGE_RESULT>')
    assert r and r.department == "消化内科" and parse_result("还没有结论") is None

def test_rule_fallback():
    assert rule_based_triage("我一直咳嗽", ["呼吸内科", "全科门诊"]).department == "呼吸内科"
    assert rule_based_triage("说不清楚哪里不舒服", ["呼吸内科", "全科门诊"]).department == "全科门诊"
