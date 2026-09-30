# ตัวอย่างโครงการ: Customer Platform · Phase 2

ข้อมูลตัวอย่างสำหรับแสดง Project Delivery Plan และการติดตามงวดงานตามสัญญา วันเริ่มนับเป็นวันถัดจากวันลงนามสัญญา

| งวดงาน / งวดเงิน | งวดตามสัญญา | สิ่งส่งมอบ | ขอบเขตของงาน | ข้อในสัญญา | กำหนดส่งมอบ | วัน |
|---|---|---|---|---|---|---:|
| 1 | งวดที่ 1 ข้อ 4.1 · ลำดับ 1 ข้อ 4.1.1 | **Project Preparation**<br>1. แผนการดำเนินงาน ข้อ 5.1.1<br>2. Project Plan ข้อ 5.1.2<br>3. ประชุมเริ่มโครงการ<br>4. Information Technology Security Requirements ข้อ 5.10.1 | จัดทำแผนการดำเนินงานโครงการตามกรอบเวลา ข้อ 5.1.1–5.1.2 | 1.1.1 · 1.1.2 · 1.10.1 | ภายใน 15 วันนับถัดจากวันลงนามสัญญา | 15 |
| 2 (1:20%) | งวดที่ 1 ข้อ 4.1 · ลำดับ 2 ข้อ 4.1.2 | **Requirement Gathering**<br>1. Requirement Specification<br>2. System Analysis and Design | ศึกษาและวิเคราะห์ระบบ ข้อ 5.2.1–5.2.4 | 1.2.1–1.2.4 | ภายใน 30 วันนับถัดจากวันลงนามสัญญา | 30 |
| 3 | งวดที่ 2 ข้อ 4.2 · ลำดับ 1 ข้อ 4.2.1 | **Design**<br>1. Enterprise Architecture<br>2. Functional Specification Document (FSD)<br>3. Software Design ข้อ 5.2.6<br>4. Data Structure และ Data Dictionary<br>5. User Interface | วิเคราะห์และออกแบบระบบ ข้อ 5.2.5–5.2.7 | 1.2.5–1.2.7 | ภายใน 60 วันนับถัดจากวันลงนามสัญญา | 60 |
| 4 (2:40%) | งวดที่ 2 ข้อ 4.2 · ลำดับ 2 ข้อ 4.2.2 | **Development and System Integration Test (SIT)**<br>1. Detailed Specification Document<br>2. Unit และ SIT Test Report<br>3. ติดตั้งบน UAT ของ ธ.ก.ส.<br>4. Source Code Scan Report | การทดสอบระบบ ข้อ 5.9 | 1.9 | ภายใน 120 วันนับถัดจากวันลงนามสัญญา | 120 |
| 5 (3:40%) | งวดที่ 3 ข้อ 4.3 | **Production Deployment Readiness and Go-live**<br>1. Go-live Checklist<br>2. คู่มือการใช้งานและดูแลระบบ<br>3. Security Baseline and Hardening<br>4. Vulnerability Impact / Remediation Assessment<br>5. แผนการดูแลรักษาและกำลังคน<br>6. Authorization and Job Role Mapping<br>7. ขั้นตอนติดตั้งระบบ<br>8. รายงานสรุปผลการดำเนินงาน | Go-live, Go-live Support และ Corrective Maintenance ข้อ 5.10.2, 5.12 | 1.10.2 · 1.12 | ภายใน 180 วันนับถัดจากวันลงนามสัญญา | 180 |

## สถานะตัวอย่างใน Project Control

- Current phase: **Delivery**
- Project health: **Blocked** — รอ Customer Security ยืนยันก่อนตรวจรับ
- งานถัดไป: แก้ API issue #23 → ส่ง UAT result รอบสุดท้าย → ขอ Customer Acceptance
- Handover: UAT ผ่าน 18/20 cases; เอกสารและหลักฐานอยู่ในรายการงาน
- Milestone ถัดไป: UAT Sign-off, Day 180 เป็นกรอบ Go-live ตามสัญญา
