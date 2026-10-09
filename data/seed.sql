CREATE TABLE machines (id TEXT PRIMARY KEY, line TEXT, status TEXT, last_maintenance TEXT);
CREATE TABLE incidents (id INTEGER PRIMARY KEY, machine_id TEXT, opened TEXT, severity TEXT, summary TEXT);
INSERT INTO machines VALUES
 ('M-101','Line A','running','2026-08-14'),
 ('M-102','Line A','maintenance','2026-09-30'),
 ('M-201','Line B','running','2026-07-02'),
 ('M-202','Line B','stopped','2026-05-21');
INSERT INTO incidents (machine_id, opened, severity, summary) VALUES
 ('M-101','2026-09-02','low','Minor vibration increase on spindle'),
 ('M-202','2026-09-11','high','Conveyor belt intrusion detected, line stopped'),
 ('M-202','2026-09-18','medium','Bearing temperature above threshold'),
 ('M-201','2026-09-25','low','Sensor dropout for 3 minutes');
