import re
BLOCKED_PATTERNS = [r"自杀|自残|轻生", r"如何(购买|制作).{0,6}(毒品|枪支|炸药)",
    r"ignore (all )?(previous|above) instructions", r"你现在是.{0,10}(DAN|越狱)", r"system prompt"]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]
CRISIS_REPLY = ("检测到您的消息可能涉及心理危机。请立即联系专业帮助：\n"
    "全国心理援助热线 12356（24 小时）。如有紧急情况请拨打 120/110。\n"
    "本系统无法提供心理危机干预，建议尽快前往医院心理科就诊。")

def check_input(text: str) -> tuple[bool, str | None]:
    for pat in _COMPILED:
        if pat.search(text):
            if "自杀" in pat.pattern or "自残" in pat.pattern:
                return False, CRISIS_REPLY
            return False, "您的输入包含系统不支持的内容，请围绕病情与就医问题进行咨询。"
    return True, None
