-- Demo catalog only; no clinical thresholds or real patients.
INSERT INTO role(code) VALUES ('doctor'),('pharmacist'),('admin');
INSERT INTO observation_type VALUES ('ef','ef','number','%',0,100);
INSERT INTO observation_type VALUES ('potassium','potassium','number','mmol/L',0,NULL);
INSERT INTO observation_type VALUES ('egfr','egfr','number','mL/min/1.73m2',0,NULL);
INSERT INTO observation_type VALUES ('creatinine','creatinine','number','umol/L',0,NULL);
INSERT INTO observation_type VALUES ('bnp','bnp','number','pg/mL',0,NULL);
INSERT INTO observation_type VALUES ('nt_probnp','nt_probnp','number','pg/mL',0,NULL);
INSERT INTO observation_type VALUES ('systolic_bp','systolic_bp','number','mmHg',0,NULL);
INSERT INTO observation_type VALUES ('heart_rate','heart_rate','number','bpm',0,NULL);
INSERT INTO observation_type VALUES ('dyspnea','dyspnea','boolean',NULL,NULL,NULL);
INSERT INTO observation_type VALUES ('frailty','frailty','text',NULL,NULL,NULL);
INSERT INTO observation_type VALUES ('comorbidity','comorbidity','text',NULL,NULL,NULL);
INSERT INTO ingredient VALUES ('synthetic_drug_a','Hoạt chất giả lập A');
