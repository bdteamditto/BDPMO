# BD PMO UX update

The hosted app now opens at Home / My Projects after login. It lists only projects where the signed-in user has membership and derives Current / Next from TOR delivery milestones.

TOR columns keep stable internal keys while allowing OWNER and EDITOR users to rename display headers. Header changes are stored as audit events and do not alter existing row values.

System Admin accounts are managed through the hosted admin endpoint. Passwords are stored as PBKDF2 hashes; provisioning values are supplied through Sites secrets and are removed after provisioning.

Deployment: https://bd-pmo-workspace.bdteam1.chatgpt.site
