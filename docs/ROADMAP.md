# PMO 3.0 → Project Operations Workspace

สถานะ: roadmap ต้นฉบับ — ดูรายการที่พัฒนาแล้วและข้อจำกัด ณ 30 กันยายน 2026 ใน [REQUIREMENTS_REVIEW.md](REQUIREMENTS_REVIEW.md)

เป้าหมาย: ทีมที่อยู่คนละที่เปิดระบบแล้วรู้สถานะ สิ่งที่ติดขัด งานถัดไป และผู้รับผิดชอบ พร้อมรับช่วงงานได้จากข้อมูลในระบบ

## 1. Project Status และ Guided Next Actions

- Project Home แสดง phase, operational status, owner, milestone ถัดไป, due date, blockers และเวลาที่อัปเดตล่าสุด
- Lifecycle ที่เสนอ: Contract → Procurement → Planning → Delivery → Acceptance → Billing → Closure ปรับตามประเภทโครงการได้
- แยกสถานะ phase ออกจากสุขภาพโครงการและ Health Score; สถานะภาพรวมใช้ On Track / At Risk / Blocked / Overdue / Completed พร้อมเหตุผลและลิงก์ไปยังรายการต้นเหตุ
- กำหนดลำดับความสำคัญเมื่อมีหลายเหตุผลให้ชัดก่อนพัฒนา; Completed ต้องผ่านเงื่อนไข Closure และไม่มี required action ค้าง
- Next Actions แสดงสิ่งที่ต้องทำ ผู้รับผิดชอบ กำหนดส่ง สิ่งที่ต้องรอ และหลักฐาน แยก Required กับ Recommended
- ตัวอย่าง: Customer Acceptance สำเร็จ → แนะนำแนบหลักฐาน เตรียม invoice และปรับ forecast; ไม่สร้างหรือส่ง invoice อัตโนมัติจากคำแนะนำ
- เกณฑ์รับงาน: ผู้ใช้เปิด Project Home แล้วระบุสถานะ งานถัดไป ผู้รับผิดชอบ และ blocker ได้ภายใน 10 วินาทีในการทดสอบกับผู้ใช้

## 2. Task, Handover และ My Work

- Task มี owner, backup owner, due date, priority, dependency, next action, evidence และ last update
- สถานะ: TODO / IN_PROGRESS / WAITING / BLOCKED / REVIEW / DONE; WAITING ต้องระบุรอใครหรืออะไร และ BLOCKED ต้องระบุเหตุผล
- ตรวจ dependency cycle และการปิดงานที่ยังติด required dependency ทาง backend
- Handover มีสถานการณ์ล่าสุด สิ่งที่ทำแล้ว สิ่งที่เหลือ ขั้นตอนถัดไป ผู้รับช่วง สิ่งที่รอ และเอกสารอ้างอิง พร้อมประวัติ
- My Work รวมงานวันนี้ งานเกินกำหนด งานรอคนอื่น และงานรอตรวจจากโครงการที่ผู้ใช้มีสิทธิ์
- เกณฑ์รับงาน: สมาชิกอีกคนรับช่วงงานจากข้อมูลในระบบได้; การมอบหมาย task ไม่เพิ่มสิทธิ์ project โดยอัตโนมัติ

## 3. Activity Timeline, Comments และ Notifications

- Timeline รวมการเปลี่ยนสถานะ เจ้าของงาน deadline เอกสาร milestone และ risk พร้อมผู้กระทำ เวลา และเหตุผลเมื่อจำเป็น
- Comments ผูกกับ task / milestone / risk / document; mentions เลือกได้เฉพาะผู้ที่เข้าถึงรายการนั้น
- Inbox แสดง assignments, mentions, due reminders, review requests และ blockers พร้อม read/unread และลิงก์กลับต้นทาง
- ป้องกัน notification ซ้ำจาก retry; ตรวจสิทธิ์ก่อนแสดงเนื้อหาและหลังถอนสมาชิก
- แยก Activity Timeline สำหรับทำงานออกจาก Audit Log ที่ต้องรักษาความครบถ้วนและตรวจสอบย้อนหลัง
- เกณฑ์รับงาน: ไม่รั่วข้อมูลข้ามโครงการผ่าน feed, search, mentions หรือ notifications

## Permission model ที่ต้องเทียบกับ source ก่อนย้าย

รักษาพฤติกรรมที่มีจริงและการทดสอบเดิมก่อน เปรียบเทียบกับข้อกำหนดจากบทสนทนาต่อไปนี้ และบันทึกช่องว่างอย่างชัดเจน:

| Role | ข้อกำหนดจากบทสนทนา |
| --- | --- |
| OWNER | จัดการโครงการและเพิ่ม OWNER / EDITOR / VIEWER |
| EDITOR | แก้ข้อมูลงาน; เพิ่ม EDITOR / VIEWER เมื่อ allowEditorInvites=true; ห้ามเพิ่ม OWNER หรือลบ/ลดสิทธิ์ OWNER |
| VIEWER | ดูอย่างเดียว ไม่เพิ่มสมาชิกหรือแก้งาน |

- เก็บ addedBy / grantedBy และ audit events สำหรับเพิ่ม เปลี่ยน และถอนสิทธิ์
- ตรวจสิทธิ์ทาง backend ทุกจุด; UI ไม่ใช่กลไกบังคับสิทธิ์เพียงอย่างเดียว
- ทดสอบ allowEditorInvites ทั้งสองค่า การยกระดับสิทธิ์ การเข้าถึงข้ามโครงการ และการถอนสิทธิ์
- PMO เป็นบริบทการทำงานใน roadmap นี้ ไม่ถือว่าเป็น role ใหม่จนกว่าจะตรวจ schema และตกลงข้อกำหนด
- ข้อเสนอจำกัดข้อมูลการเงินเพิ่มเติมเป็นงานอนาคต ไม่เปลี่ยน permission model ระหว่างการย้าย

## ลำดับส่งมอบ

1. ย้าย source ที่ตรวจสอบเวอร์ชันได้ พร้อม docs, tests, lockfiles, migrations และ permission model ปัจจุบัน
2. Project Home และ Guided Next Actions ที่เชื่อมข้อมูลเดิม
3. Task + Handover + My Work
4. Activity Timeline + Comments/Mentions + Notifications
5. Decision Log, Daily/Weekly Updates, Workload และ Escalation ตาม feedback การใช้งาน

ทุกระยะต้องมีเกณฑ์รับงานและ regression tests ที่เหมาะสม; roadmap นี้ไม่อ้างว่าฟีเจอร์ถูก implement หรือผ่าน tests แล้ว
