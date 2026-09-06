from datetime import date, timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models import Department, DoctorProfile, KbDocument, Role, Schedule, Slot, User

DEPARTMENTS = [("全科门诊", "常见病、多发病的首诊科室"), ("呼吸内科", "咳嗽、哮喘、肺部感染等呼吸系统疾病"),
    ("消化内科", "胃肠、肝胆胰疾病"), ("心血管内科", "高血压、冠心病、心律失常"),
    ("神经内科", "头痛、眩晕、脑血管病"), ("骨科", "骨折、关节及脊柱疾病"),
    ("皮肤科", "皮炎、湿疹、痤疮等皮肤疾病"), ("儿科", "14 岁以下儿童疾病")]
STAFF = [("admin", "系统管理员", Role.admin), ("lab01", "检验师-钱五", Role.lab),
    ("cashier01", "收费员-孙六", Role.cashier), ("pharmacist01", "药师-周七", Role.pharmacist),
    ("patient01", "测试患者-张三", Role.patient)]
DOCTORS = [("doctor01", "李医生", "呼吸内科", "主任医师"), ("doctor02", "王医生", "消化内科", "主治医师"),
    ("doctor03", "赵医生", "心血管内科", "副主任医师"), ("doctor04", "陈医生", "全科门诊", "主治医师")]
KB_DOCS = [
    ("常见症状分诊指南", "# 常见症状分诊指南\n## 呼吸系统\n持续咳嗽、咳痰、胸闷气短、发热伴咳嗽，建议呼吸内科就诊。\n## 消化系统\n腹痛、腹泻、恶心呕吐、反酸烧心、便血黑便，建议消化内科。\n## 心血管\n胸痛胸闷、心悸、活动后气促、血压异常，建议心血管内科。\n## 神经系统\n反复头痛、眩晕、肢体麻木、短暂意识丧失，建议神经内科。\n## 骨科与皮肤\n外伤、关节疼痛、腰腿痛建议骨科；皮疹、瘙痒、痤疮、脱发建议皮肤科。\n## 儿科\n14 岁以下患儿原则上均建议儿科首诊。"),
    ("血常规指标解读", "# 血常规常用指标解读\n## 白细胞计数（WBC）\n参考范围 3.5-9.5×10^9/L。升高常见于细菌感染。\n## 血红蛋白（HGB）\n男 130-175 g/L，女 115-150 g/L。降低提示贫血。\n## 血小板计数（PLT）\n参考范围 125-350×10^9/L。降低有出血风险。\n## C 反应蛋白（CRP）\n参考范围 0-8 mg/L。急性炎症时明显升高。"),
    ("肝功能与血脂指标解读", "# 肝功能与血脂常用指标解读\n## 谷丙转氨酶（ALT）\n参考范围 9-50 U/L。升高提示肝细胞损伤。\n## 总胆固醇（TC）\n理想值 <5.2 mmol/L。升高为动脉粥样硬化危险因素。\n## 甘油三酯（TG）\n理想值 <1.7 mmol/L。显著升高需警惕急性胰腺炎。\n## 低密度脂蛋白胆固醇（LDL-C）\n一般人群 <3.4 mmol/L。心血管高危人群目标值更低。"),
]

async def seed() -> None:
    async with async_session_factory() as db:
        if await db.scalar(select(User.id).limit(1)): return
        depts = {name: Department(name=name, description=desc) for name, desc in DEPARTMENTS}
        db.add_all(depts.values()); pwd = hash_password("123456")
        for username, full_name, role in STAFF:
            db.add(User(username=username, password_hash=pwd, full_name=full_name, role=role))
        profiles = []
        for username, full_name, dept, title in DOCTORS:
            u = User(username=username, password_hash=pwd, full_name=full_name, role=Role.doctor); db.add(u); await db.flush()
            p = DoctorProfile(user_id=u.id, department_id=depts[dept].id, title=title, bio=f"{dept}{title}，从事临床工作十余年。")
            db.add(p); profiles.append(p)
        await db.flush()
        today = date.today()
        for p in profiles:
            for d in range(7):
                for slot in (Slot.am, Slot.pm):
                    db.add(Schedule(doctor_id=p.id, work_date=today + timedelta(days=d), slot=slot, capacity=20))
        for title, content in KB_DOCS:
            db.add(KbDocument(title=title, source="seed", content=content))
        await db.commit()
    try:
        from app.tasks.kb_tasks import ingest_document
        async with async_session_factory() as db:
            for doc_id in (await db.execute(select(KbDocument.id))).scalars():
                ingest_document.delay(doc_id)
    except Exception: pass
