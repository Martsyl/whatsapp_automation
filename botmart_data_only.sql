--
-- PostgreSQL database dump
--

\restrict X6FWe5THTpOcXyo4ebfrUc5Wk86VziBvRUHzD2OQJCTBGvm3L6vcyQZRJmdbDVc

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.auth_group DISABLE TRIGGER ALL;

COPY public.auth_group (id, name) FROM stdin;
\.


ALTER TABLE public.auth_group ENABLE TRIGGER ALL;

--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_content_type DISABLE TRIGGER ALL;

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	group
3	auth	permission
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	core	client
8	core	product
9	core	businesshours
10	core	subscriptionplan
11	core	autoreplyrule
12	core	broadcast
13	core	campaignlog
14	core	contact
15	core	emailcampaign
16	core	messagelog
17	core	messagetemplate
18	core	passwordresettoken
19	django_celery_beat	clockedschedule
20	django_celery_beat	crontabschedule
21	django_celery_beat	intervalschedule
22	django_celery_beat	periodictask
23	django_celery_beat	periodictasks
24	django_celery_beat	solarschedule
25	django_celery_results	chordcounter
26	django_celery_results	groupresult
27	django_celery_results	taskresult
28	core	paymentlog
29	core	errorlog
\.


ALTER TABLE public.django_content_type ENABLE TRIGGER ALL;

--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auth_permission DISABLE TRIGGER ALL;

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	3	add_permission
6	Can change permission	3	change_permission
7	Can delete permission	3	delete_permission
8	Can view permission	3	view_permission
9	Can add group	2	add_group
10	Can change group	2	change_group
11	Can delete group	2	delete_group
12	Can view group	2	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add client	7	add_client
26	Can change client	7	change_client
27	Can delete client	7	delete_client
28	Can view client	7	view_client
29	Can add subscription plan	10	add_subscriptionplan
30	Can change subscription plan	10	change_subscriptionplan
31	Can delete subscription plan	10	delete_subscriptionplan
32	Can view subscription plan	10	view_subscriptionplan
33	Can add Business Hour	9	add_businesshours
34	Can change Business Hour	9	change_businesshours
35	Can delete Business Hour	9	delete_businesshours
36	Can view Business Hour	9	view_businesshours
37	Can add broadcast	12	add_broadcast
38	Can change broadcast	12	change_broadcast
39	Can delete broadcast	12	delete_broadcast
40	Can view broadcast	12	view_broadcast
41	Can add auto reply rule	11	add_autoreplyrule
42	Can change auto reply rule	11	change_autoreplyrule
43	Can delete auto reply rule	11	delete_autoreplyrule
44	Can view auto reply rule	11	view_autoreplyrule
45	Can add contact	14	add_contact
46	Can change contact	14	change_contact
47	Can delete contact	14	delete_contact
48	Can view contact	14	view_contact
49	Can add email campaign	15	add_emailcampaign
50	Can change email campaign	15	change_emailcampaign
51	Can delete email campaign	15	delete_emailcampaign
52	Can view email campaign	15	view_emailcampaign
53	Can add message log	16	add_messagelog
54	Can change message log	16	change_messagelog
55	Can delete message log	16	delete_messagelog
56	Can view message log	16	view_messagelog
57	Can add message template	17	add_messagetemplate
58	Can change message template	17	change_messagetemplate
59	Can delete message template	17	delete_messagetemplate
60	Can view message template	17	view_messagetemplate
61	Can add password reset token	18	add_passwordresettoken
62	Can change password reset token	18	change_passwordresettoken
63	Can delete password reset token	18	delete_passwordresettoken
64	Can view password reset token	18	view_passwordresettoken
65	Can add product	8	add_product
66	Can change product	8	change_product
67	Can delete product	8	delete_product
68	Can view product	8	view_product
69	Can add campaign log	13	add_campaignlog
70	Can change campaign log	13	change_campaignlog
71	Can delete campaign log	13	delete_campaignlog
72	Can view campaign log	13	view_campaignlog
73	Can add crontab	20	add_crontabschedule
74	Can change crontab	20	change_crontabschedule
75	Can delete crontab	20	delete_crontabschedule
76	Can view crontab	20	view_crontabschedule
77	Can add interval	21	add_intervalschedule
78	Can change interval	21	change_intervalschedule
79	Can delete interval	21	delete_intervalschedule
80	Can view interval	21	view_intervalschedule
81	Can add periodic task	22	add_periodictask
82	Can change periodic task	22	change_periodictask
83	Can delete periodic task	22	delete_periodictask
84	Can view periodic task	22	view_periodictask
85	Can add periodic task track	23	add_periodictasks
86	Can change periodic task track	23	change_periodictasks
87	Can delete periodic task track	23	delete_periodictasks
88	Can view periodic task track	23	view_periodictasks
89	Can add solar event	24	add_solarschedule
90	Can change solar event	24	change_solarschedule
91	Can delete solar event	24	delete_solarschedule
92	Can view solar event	24	view_solarschedule
93	Can add clocked	19	add_clockedschedule
94	Can change clocked	19	change_clockedschedule
95	Can delete clocked	19	delete_clockedschedule
96	Can view clocked	19	view_clockedschedule
97	Can add task result	27	add_taskresult
98	Can change task result	27	change_taskresult
99	Can delete task result	27	delete_taskresult
100	Can view task result	27	view_taskresult
101	Can add chord counter	25	add_chordcounter
102	Can change chord counter	25	change_chordcounter
103	Can delete chord counter	25	delete_chordcounter
104	Can view chord counter	25	view_chordcounter
105	Can add group result	26	add_groupresult
106	Can change group result	26	change_groupresult
107	Can delete group result	26	delete_groupresult
108	Can view group result	26	view_groupresult
109	Can add payment log	28	add_paymentlog
110	Can change payment log	28	change_paymentlog
111	Can delete payment log	28	delete_paymentlog
112	Can view payment log	28	view_paymentlog
113	Can add error log	29	add_errorlog
114	Can change error log	29	change_errorlog
115	Can delete error log	29	delete_errorlog
116	Can view error log	29	view_errorlog
\.


ALTER TABLE public.auth_permission ENABLE TRIGGER ALL;

--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auth_group_permissions DISABLE TRIGGER ALL;

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


ALTER TABLE public.auth_group_permissions ENABLE TRIGGER ALL;

--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auth_user DISABLE TRIGGER ALL;

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$1200000$a5Ubca2WEvny28RnnFTyUu$tfpM35jskPQXLvp91LjqKxHl7skjwKuI5KoXfIq0Ktg=	2026-03-07 01:37:21.658392+01	t	martsyl_automation			msnonuorah3964@gmail.com	t	t	2026-02-19 10:47:23.417268+01
\.


ALTER TABLE public.auth_user ENABLE TRIGGER ALL;

--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auth_user_groups DISABLE TRIGGER ALL;

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


ALTER TABLE public.auth_user_groups ENABLE TRIGGER ALL;

--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auth_user_user_permissions DISABLE TRIGGER ALL;

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


ALTER TABLE public.auth_user_user_permissions ENABLE TRIGGER ALL;

--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.clients DISABLE TRIGGER ALL;

COPY public.clients (id, business_name, email, hashed_password, phone_number_id, whatsapp_number, access_token, is_active, created_at, token_valid, plan, payment_status, payment_reference, waba_id, subscription_start, subscription_end, grace_period_end, reminder_7_sent, reminder_3_sent, ai_replies_used, ai_replies_reset_date, subscription_months, business_description) FROM stdin;
6	Klassic Hairs	msnonuorah3964@gmail.com	$2b$12$2jY2Vq8tJ9TTw159Fz0fruvb8syKO3AKJUCXgk5oGsz7XhNFdCFOG	1028026527054528	+2348103491026	EAAUJzVYGvkgBQ3ZBddfDHwlYU7ansczwVoUgp6BeMmE2ga1vKpFdHMfa1uS5VhWHOBwN3WTgonV4ZClrZB5M8MjhYlo4Q22BShz44g1fG0hEOah1ErZBeEbR16PzAU8ZCvzTwWIF3mpwZBQZBjFlIxdMwt9DMjBKYSjIsAaVKmS9WT6yLmxAXsQhDTTKSFX31cxf7qNZACoUHxQ1GvXJ1MdwoXkg9pmG95i9vB8k	t	2026-03-07 01:40:17.146631	t	pro	paid	rkggo79utq	918538821086247	2026-03-11	2029-05-05	2029-05-12	f	f	1	2026-03-12	1	\N
\.


ALTER TABLE public.clients ENABLE TRIGGER ALL;

--
-- Data for Name: auto_reply_rules; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.auto_reply_rules DISABLE TRIGGER ALL;

COPY public.auto_reply_rules (id, client_id, trigger_keyword, response_text, is_active, created_at) FROM stdin;
3	6	location	We are located at number 46 Thinkers Estate	t	2026-03-10 14:52:03.810829
4	6	courses	1.Full-stack web development 2. Data Analytics 3. Data Science	t	2026-03-10 14:52:14.621803
5	6	organization	We are government owned company	t	2026-03-11 15:19:34.372305
\.


ALTER TABLE public.auto_reply_rules ENABLE TRIGGER ALL;

--
-- Data for Name: broadcasts; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.broadcasts DISABLE TRIGGER ALL;

COPY public.broadcasts (id, client_id, title, message, template_name, status, total, sent, failed, created_at) FROM stdin;
\.


ALTER TABLE public.broadcasts ENABLE TRIGGER ALL;

--
-- Data for Name: business_hours; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.business_hours DISABLE TRIGGER ALL;

COPY public.business_hours (id, client_id, day_of_week, open_time, close_time, is_open) FROM stdin;
1	6	0	00:00	23:59	t
2	6	1	09:00	18:00	t
3	6	2	09:00	18:00	t
4	6	3	09:00	18:00	t
5	6	4	09:00	18:00	t
6	6	5	09:00	18:00	f
7	6	6	09:00	18:00	f
\.


ALTER TABLE public.business_hours ENABLE TRIGGER ALL;

--
-- Data for Name: email_campaigns; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.email_campaigns DISABLE TRIGGER ALL;

COPY public.email_campaigns (id, subject, body, recipient_type, target_plan, scheduled_at, status, total_recipients, sent_count, failed_count, created_at, updated_at) FROM stdin;
\.


ALTER TABLE public.email_campaigns ENABLE TRIGGER ALL;

--
-- Data for Name: campaign_logs; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.campaign_logs DISABLE TRIGGER ALL;

COPY public.campaign_logs (id, campaign_id, client_id, email, status, sent_at, opened_at, error_msg) FROM stdin;
\.


ALTER TABLE public.campaign_logs ENABLE TRIGGER ALL;

--
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.contacts DISABLE TRIGGER ALL;

COPY public.contacts (id, client_id, name, phone_number, created_at, opted_out) FROM stdin;
2	6	klassic_hairs_client_1	2348103491026	2026-03-10 13:13:57.24531	f
3	6	klassic_hairs_client_2	2348141998390	2026-03-12 09:02:21.353979	f
\.


ALTER TABLE public.contacts ENABLE TRIGGER ALL;

--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_admin_log DISABLE TRIGGER ALL;

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2026-02-19 20:28:49.795255+01	3	Klassic Hairs	2	[{"added": {"name": "business hours", "object": "Klassic Hairs - Monday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Tuesday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Wednesday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Thursday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Friday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Saturday"}}, {"added": {"name": "business hours", "object": "Klassic Hairs - Sunday"}}]	7	1
2	2026-02-26 12:16:21.625827+01	7	Klassic Hairs	2	[{"changed": {"fields": ["Is active"]}}]	7	1
3	2026-03-03 11:11:44.777639+01	1	Starter — ₦9,000	2	[{"changed": {"fields": ["Price naira"]}}]	10	1
4	2026-03-03 14:50:22.801433+01	2	Growth — ₦20,000	2	[{"changed": {"fields": ["Price naira"]}}]	10	1
5	2026-03-03 14:50:35.348615+01	3	Pro — ₦35,000	2	[{"changed": {"fields": ["Is active"]}}]	10	1
6	2026-03-03 14:50:35.353436+01	2	Growth — ₦20,000	2	[{"changed": {"fields": ["Is active"]}}]	10	1
7	2026-03-03 14:50:35.356372+01	1	Starter — ₦9,000	2	[{"changed": {"fields": ["Is active"]}}]	10	1
8	2026-03-04 00:35:44.268897+01	1	Hello — draft	1	[{"added": {}}]	15	1
9	2026-03-04 00:37:08.090444+01	1	Hello — draft	2	[]	15	1
10	2026-03-04 01:23:13.688269+01	1	Hello — queued	3		15	1
11	2026-03-04 01:23:59.621069+01	2	🎉 New Feature Alert! — draft	1	[{"added": {}}]	15	1
12	2026-03-04 01:48:45.70927+01	3	Testing the Design — draft	1	[{"added": {}}]	15	1
13	2026-03-04 02:06:22.700907+01	4	Another Day — draft	1	[{"added": {}}]	15	1
14	2026-03-04 02:17:30.352599+01	5	Checking Design — draft	1	[{"added": {}}]	15	1
15	2026-03-04 02:24:06.439126+01	6	Till we get it right — draft	1	[{"added": {}}]	15	1
16	2026-03-04 02:34:49.491591+01	7	Let's see what we achieved — draft	1	[{"added": {}}]	15	1
17	2026-03-05 00:53:57.219925+01	1	Klassic Hairs	3		7	1
18	2026-03-06 08:23:13.539223+01	2	Klassic Hairs	2	[{"changed": {"fields": ["Is active"]}}]	7	1
19	2026-03-06 08:57:14.840221+01	2	Klassic Hairs	3		7	1
20	2026-03-06 18:33:36.179034+01	3	Bella Naija Hairs	3		7	1
21	2026-03-06 18:46:25.989475+01	4	Klassic Hairs	3		7	1
22	2026-03-06 18:49:44.646367+01	5	Klassic Hairs	2	[{"changed": {"fields": ["Is active"]}}]	7	1
23	2026-03-07 00:40:49.110095+01	5	Klassic Hairs	2	[{"changed": {"fields": ["Is active"]}}]	7	1
\.


ALTER TABLE public.django_admin_log ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_clockedschedule; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_clockedschedule DISABLE TRIGGER ALL;

COPY public.django_celery_beat_clockedschedule (id, clocked_time) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_clockedschedule ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_crontabschedule; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_crontabschedule DISABLE TRIGGER ALL;

COPY public.django_celery_beat_crontabschedule (id, minute, hour, day_of_week, day_of_month, month_of_year, timezone) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_crontabschedule ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_intervalschedule; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_intervalschedule DISABLE TRIGGER ALL;

COPY public.django_celery_beat_intervalschedule (id, every, period) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_intervalschedule ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_solarschedule; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_solarschedule DISABLE TRIGGER ALL;

COPY public.django_celery_beat_solarschedule (id, event, latitude, longitude) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_solarschedule ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_periodictask; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_periodictask DISABLE TRIGGER ALL;

COPY public.django_celery_beat_periodictask (id, name, task, args, kwargs, queue, exchange, routing_key, expires, enabled, last_run_at, total_run_count, date_changed, description, crontab_id, interval_id, solar_id, one_off, start_time, priority, headers, clocked_id, expire_seconds) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_periodictask ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_beat_periodictasks; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_periodictasks DISABLE TRIGGER ALL;

COPY public.django_celery_beat_periodictasks (ident, last_update) FROM stdin;
\.


ALTER TABLE public.django_celery_beat_periodictasks ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_results_chordcounter; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_results_chordcounter DISABLE TRIGGER ALL;

COPY public.django_celery_results_chordcounter (id, group_id, sub_tasks, count) FROM stdin;
\.


ALTER TABLE public.django_celery_results_chordcounter ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_results_groupresult; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_results_groupresult DISABLE TRIGGER ALL;

COPY public.django_celery_results_groupresult (id, group_id, date_created, date_done, content_type, content_encoding, result) FROM stdin;
\.


ALTER TABLE public.django_celery_results_groupresult ENABLE TRIGGER ALL;

--
-- Data for Name: django_celery_results_taskresult; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_results_taskresult DISABLE TRIGGER ALL;

COPY public.django_celery_results_taskresult (id, task_id, status, content_type, content_encoding, result, date_done, traceback, meta, task_args, task_kwargs, task_name, worker, date_created, periodic_task_name, date_started) FROM stdin;
\.


ALTER TABLE public.django_celery_results_taskresult ENABLE TRIGGER ALL;

--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_migrations DISABLE TRIGGER ALL;

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2026-02-19 10:37:48.828129+01
2	auth	0001_initial	2026-02-19 10:37:48.906168+01
3	admin	0001_initial	2026-02-19 10:37:48.923845+01
4	admin	0002_logentry_remove_auto_add	2026-02-19 10:37:48.932283+01
5	admin	0003_logentry_add_action_flag_choices	2026-02-19 10:37:48.940022+01
6	contenttypes	0002_remove_content_type_name	2026-02-19 10:37:48.957306+01
7	auth	0002_alter_permission_name_max_length	2026-02-19 10:37:48.965539+01
8	auth	0003_alter_user_email_max_length	2026-02-19 10:37:48.979373+01
9	auth	0004_alter_user_username_opts	2026-02-19 10:37:48.987233+01
10	auth	0005_alter_user_last_login_null	2026-02-19 10:37:48.994645+01
11	auth	0006_require_contenttypes_0002	2026-02-19 10:37:48.996225+01
12	auth	0007_alter_validators_add_error_messages	2026-02-19 10:37:49.002622+01
13	auth	0008_alter_user_username_max_length	2026-02-19 10:37:49.015838+01
14	auth	0009_alter_user_last_name_max_length	2026-02-19 10:37:49.024598+01
15	auth	0010_alter_group_name_max_length	2026-02-19 10:37:49.032941+01
16	auth	0011_update_proxy_permissions	2026-02-19 10:37:49.040724+01
17	auth	0012_alter_user_first_name_max_length	2026-02-19 10:37:49.050224+01
18	sessions	0001_initial	2026-02-19 10:37:49.060748+01
19	core	0001_initial	2026-03-04 00:28:14.240279+01
20	django_celery_beat	0001_initial	2026-03-04 00:28:52.452086+01
21	django_celery_beat	0002_auto_20161118_0346	2026-03-04 00:28:52.477651+01
22	django_celery_beat	0003_auto_20161209_0049	2026-03-04 00:28:52.494344+01
23	django_celery_beat	0004_auto_20170221_0000	2026-03-04 00:28:52.503306+01
24	django_celery_beat	0005_add_solarschedule_events_choices	2026-03-04 00:28:52.512035+01
25	django_celery_beat	0006_auto_20180322_0932	2026-03-04 00:28:52.591503+01
26	django_celery_beat	0007_auto_20180521_0826	2026-03-04 00:28:52.62998+01
27	django_celery_beat	0008_auto_20180914_1922	2026-03-04 00:28:52.695352+01
28	django_celery_beat	0006_auto_20180210_1226	2026-03-04 00:28:52.740902+01
29	django_celery_beat	0006_periodictask_priority	2026-03-04 00:28:52.766451+01
30	django_celery_beat	0009_periodictask_headers	2026-03-04 00:28:52.798144+01
31	django_celery_beat	0010_auto_20190429_0326	2026-03-04 00:28:53.190178+01
32	django_celery_beat	0011_auto_20190508_0153	2026-03-04 00:28:53.2279+01
33	django_celery_beat	0012_periodictask_expire_seconds	2026-03-04 00:28:53.246189+01
34	django_celery_beat	0013_auto_20200609_0727	2026-03-04 00:28:53.275296+01
35	django_celery_beat	0014_remove_clockedschedule_enabled	2026-03-04 00:28:53.289265+01
36	django_celery_beat	0015_edit_solarschedule_events_choices	2026-03-04 00:28:53.297811+01
37	django_celery_beat	0016_alter_crontabschedule_timezone	2026-03-04 00:28:53.326397+01
38	django_celery_beat	0017_alter_crontabschedule_month_of_year	2026-03-04 00:28:53.347882+01
39	django_celery_beat	0018_improve_crontab_helptext	2026-03-04 00:28:53.365494+01
40	django_celery_beat	0019_alter_periodictasks_options	2026-03-04 00:28:53.371253+01
41	django_celery_results	0001_initial	2026-03-04 00:28:53.40328+01
42	django_celery_results	0002_add_task_name_args_kwargs	2026-03-04 00:28:53.422488+01
43	django_celery_results	0003_auto_20181106_1101	2026-03-04 00:28:53.430638+01
44	django_celery_results	0004_auto_20190516_0412	2026-03-04 00:28:53.496797+01
45	django_celery_results	0005_taskresult_worker	2026-03-04 00:28:53.507032+01
46	django_celery_results	0006_taskresult_date_created	2026-03-04 00:28:53.575564+01
47	django_celery_results	0007_remove_taskresult_hidden	2026-03-04 00:28:53.583563+01
48	django_celery_results	0008_chordcounter	2026-03-04 00:28:53.611176+01
49	django_celery_results	0009_groupresult	2026-03-04 00:28:53.820198+01
50	django_celery_results	0010_remove_duplicate_indices	2026-03-04 00:28:53.832515+01
51	django_celery_results	0011_taskresult_periodic_task_name	2026-03-04 00:28:53.839614+01
52	django_celery_results	0012_taskresult_date_started	2026-03-04 00:28:53.851856+01
53	django_celery_results	0013_taskresult_django_cele_periodi_1993cf_idx	2026-03-04 00:28:53.861949+01
54	django_celery_results	0014_alter_taskresult_status	2026-03-04 00:28:53.867928+01
55	core	0002_subscriptionplan_discount_12_months_and_more	2026-03-06 08:36:43.637495+01
56	core	0003_paymentlog	2026-03-06 19:35:39.721865+01
57	core	0004_client_business_description_errorlog	2026-03-12 11:21:11.405604+01
\.


ALTER TABLE public.django_migrations ENABLE TRIGGER ALL;

--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.django_session DISABLE TRIGGER ALL;

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
wh539zwqb4qrs8e2gplhrxzhdszdzo1z	eyJjbGllbnRfaWQiOjYsImNsaWVudF9uYW1lIjoiS2xhc3NpYyBIYWlycyJ9:1w0fHH:Fe_x6MENi1sTf8CD9dIPwZiySjOlT7gDSzd0wkAzyAY	2026-03-26 13:36:35.171457+01
\.


ALTER TABLE public.django_session ENABLE TRIGGER ALL;

--
-- Data for Name: email_campaigns_selected_clients; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.email_campaigns_selected_clients DISABLE TRIGGER ALL;

COPY public.email_campaigns_selected_clients (id, emailcampaign_id, client_id) FROM stdin;
\.


ALTER TABLE public.email_campaigns_selected_clients ENABLE TRIGGER ALL;

--
-- Data for Name: message_logs; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.message_logs DISABLE TRIGGER ALL;

COPY public.message_logs (id, client_id, sender_number, message_text, direction, "timestamp", whatsapp_message_id) FROM stdin;
13	6	2348103491026	hello	inbound	2026-03-10 13:14:05.690861	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDRDJDMDBGMzI3OTcyMDVGQjU3MzhGNENCQUQ2MkQxAA==
14	6	2348103491026	👋 Welcome to *Klassic Hairs*!\n\nWe're glad you reached out. Here's what we offer:\n\n1️⃣ Type *menu* - See all options\n2️⃣ Type *human* - Talk to an agent\n\nJust type any keyword above to get started! 😊	outbound	2026-03-10 13:14:09.429522	\N
15	6	2348103491026	do you guys have any product	inbound	2026-03-10 13:14:36.137629	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMTRCOTgyQjY3M0JDMUFFMUZEQzJEMTkzRDQ0NUE5AA==
16	6	2348103491026	Hey! 👋 Yes, we do! We have a range of hair products and services at Klassic Hairs.\n\nWhat are you looking for? I can help you find what you need — just let me know the product type or what you're interested in! 😊	outbound	2026-03-10 13:14:43.670818	\N
17	6	2348103491026	location	inbound	2026-03-10 13:52:34.056442	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDOTg1RjE4REI3RTZFM0M2MzVGOEVCOUJCOUQ2RTZEAA==
18	6	2348103491026	We are located at number 46 Thinkers Estate	outbound	2026-03-10 13:52:36.694938	\N
19	6	2348103491026	what courses do you offer	inbound	2026-03-10 13:52:49.427041	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDQzlDQkFEMjQwRkQ4NzREQTMxM0M3QUUyRkVDRDc3AA==
20	6	2348103491026	1.Full-stack web development 2. Data Analytics 3. Data Science	outbound	2026-03-10 13:52:52.270927	\N
21	6	2348103491026	how is important is web development	inbound	2026-03-10 13:53:20.017818	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMkY4REM1QzE3NUY0NTVFRDQ0RDgxNzlDRUNGOTBFAA==
22	6	2348103491026	Web development is super important! 💻 It's one of the most in-demand skills right now, and businesses need skilled developers everywhere.\n\nWe actually offer a **Full-stack web development course** that covers everything you need to get started. Interested in learning more? What would you like to know! 😊	outbound	2026-03-10 13:53:25.531567	\N
23	6	2348103491026	good evening	inbound	2026-03-10 14:57:23.046351	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDOTAyQkQxOEE1QTYwQUI4QjhDOTlGOEZCQzVBNkQxAA==
24	6	2348103491026	Good evening! 👋 Welcome to Klassic Hairs. How can I help you today?	outbound	2026-03-10 14:57:30.493192	\N
25	6	2348103491026	hello	inbound	2026-03-11 09:29:42.75207	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDNUFENzBBMzMxMjY3QkRGMTI0M0MwQ0M2M0JFMkU1AA==
26	6	2348103491026	Hey there! 👋 Welcome to Klassic Hairs! How can I help you today? \n\nFeel free to ask about our services, location, or anything else! 😊	outbound	2026-03-11 09:29:49.149994	\N
27	6	2348103491026	hello	inbound	2026-03-11 14:20:27.960048	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMUY2MjJBMEUzQzQ2MTFDQzFDNkYxQzQ2RTRGOENEAA==
28	6	2348103491026	Hey there! 👋 Welcome to Klassic Hairs! How can I help you today? Feel free to ask about our services, location, or anything else! 😊	outbound	2026-03-11 14:20:36.578419	\N
29	6	2348103491026	location	inbound	2026-03-11 14:20:47.468446	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDODU2NzkyODY3ODc0N0U1NUY5NEU5QkJBRDdFNEFCAA==
30	6	2348103491026	We are located at number 46 Thinkers Estate	outbound	2026-03-11 14:20:50.038612	\N
31	6	2348103491026	organization	inbound	2026-03-11 14:21:04.372351	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDNTUyMkZCOTc0QkI5OUQ3RTlCRERBMzAyQjZBNUNCAA==
32	6	2348103491026	We are government owned company	outbound	2026-03-11 14:21:07.35649	\N
33	6	2348103491026	what courses do you offer	inbound	2026-03-11 14:21:30.000072	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMDFFMTU2Q0U4RTVCQTI5MUVBQjNEODVGRjE5OUJDAA==
34	6	2348103491026	1.Full-stack web development 2. Data Analytics 3. Data Science	outbound	2026-03-11 14:21:32.218657	\N
35	6	2348103491026	what is the importance of web development	inbound	2026-03-11 14:21:49.614511	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMjVDMTYyRTNGRkMwNzU4MzUzNERGMUYyRTU3MDNFAA==
36	6	2348103491026	Hey! 👋 Web development is super important because it helps businesses build websites and apps that customers can use online. It's a skill that's always in demand!\n\nSpeaking of which, we actually offer a **Full-stack Web Development course** at Klassic Hairs if you're interested in learning more. Would you like details about it? 😊	outbound	2026-03-11 14:21:55.996279	\N
37	6	2348103491026	hello	inbound	2026-03-11 22:52:21.98903	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDMDk0RDY2M0QzMUIyQUJFNjFCNDExOUExMDBEMDdEAA==
38	6	2348103491026	Hello! 👋 Welcome to Klassic Hairs! \n\nHow can I help you today? Feel free to ask about our services, location, or anything else you'd like to know! 😊	outbound	2026-03-11 22:52:32.386961	\N
39	6	2348103491026	🕐 *We're currently closed.*\n\nOur team is not available right now but we'll get back to you as soon as we open.\n\nType *hours* to see our working hours.	outbound	2026-03-11 23:06:59.126337	wamid.HBgNMjM0ODEwMzQ5MTAyNhUCABIYIEFDNjYxMTVBNzZGOUE5RTg1MzEzMDBEQzcwNzg4MDY4AA==
40	6	2348141998390	is aki	inbound	2026-03-12 09:02:29.548264	wamid.HBgNMjM0ODE0MTk5ODM5MBUCABIYIEFDOEIwMjFENjZGOUQwOEQ4QzVFRUM3MkVCNUM5NDdCAA==
41	6	2348141998390	👋 Welcome to *Klassic Hairs*!\n\nWe're glad you reached out. Here's what we offer:\n\n1️⃣ Type *location* - We are located at number 46 Th\n2️⃣ Type *courses* - 1.Full-stack web development 2\n3️⃣ Type *organization* - We are government owned compan\n4️⃣ Type *menu* - See all options\n5️⃣ Type *human* - Talk to an agent\n\nJust type any keyword above to get started! 😊	outbound	2026-03-12 09:02:34.108997	\N
42	6	2348141998390	hi	inbound	2026-03-12 09:18:37.493883	wamid.HBgNMjM0ODE0MTk5ODM5MBUCABIYIEFDMTFCMkM4RUFEMjhCMTJFNzU1MEQxNkU2M0FBQTAxAA==
43	6	2348141998390	Hey! 👋 Welcome to Klassic Hairs! How can I help you today? Feel free to ask about our services, location, or anything else you'd like to know! 😊	outbound	2026-03-12 09:18:46.383286	\N
\.


ALTER TABLE public.message_logs ENABLE TRIGGER ALL;

--
-- Data for Name: message_templates; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.message_templates DISABLE TRIGGER ALL;

COPY public.message_templates (id, client_id, welcome_message, menu_message, closed_message, handoff_message, fallback_message, updated_at) FROM stdin;
3	6	\N	\N	\N	\N	\N	2026-03-12 01:38:03.126879
\.


ALTER TABLE public.message_templates ENABLE TRIGGER ALL;

--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.password_reset_tokens DISABLE TRIGGER ALL;

COPY public.password_reset_tokens (id, client_id, token, expires_at, used, created_at) FROM stdin;
\.


ALTER TABLE public.password_reset_tokens ENABLE TRIGGER ALL;

--
-- Data for Name: payment_logs; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.payment_logs DISABLE TRIGGER ALL;

COPY public.payment_logs (id, reference, amount_kobo, plan, months, is_renewal, subscription_start, subscription_end, paid_at, client_id) FROM stdin;
1	7uss6r0vx9	33600000	pro	12	f	2026-03-07	2027-03-07	2026-03-07 01:48:44.995078+01	6
2	tg0vms3r2r	17850000	pro	6	t	2026-03-07	2033-09-01	2026-03-07 02:36:18.139756+01	6
3	07ssj3kq0t	33600000	pro	12	t	2026-03-07	2034-09-01	2026-03-07 02:36:36.435357+01	6
4	tye8aud393	33600000	pro	12	f	2026-03-07	2027-03-07	2026-03-07 02:53:09.419851+01	6
5	e05nquszsy	33600000	pro	12	t	2026-03-07	2028-03-06	2026-03-07 02:54:34.970103+01	6
6	g9uwhjxjd5	33600000	pro	12	t	2026-03-07	2029-03-06	2026-03-07 02:54:40.098847+01	6
7	jwe8ezabti	3500000	pro	1	t	2026-03-11	2029-04-05	2026-03-11 13:30:35.059237+01	6
8	rkggo79utq	3500000	pro	1	t	2026-03-11	2029-05-05	2026-03-11 13:32:14.029599+01	6
\.


ALTER TABLE public.payment_logs ENABLE TRIGGER ALL;

--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.products DISABLE TRIGGER ALL;

COPY public.products (id, client_id, name, description, price, image_url, category, keyword, is_active, created_at, image_public_id) FROM stdin;
\.


ALTER TABLE public.products ENABLE TRIGGER ALL;

--
-- Data for Name: subscription_plans; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.subscription_plans DISABLE TRIGGER ALL;

COPY public.subscription_plans (id, name, display_name, price_kobo, description, is_active, created_at, updated_at, price_naira, discount_12_months, discount_3_months, discount_6_months) FROM stdin;
3	pro	Pro	3500000	Everything in Growth + unlimited AI + dedicated support	t	\N	2026-03-03 14:50:35.344918	35000	20	10	15
2	growth	Growth	2000000	Unlimited contacts, rules, products + broadcasts + AI replies	t	\N	2026-03-03 14:50:35.352151	20000	20	10	15
1	starter	Starter	900000	1 WhatsApp number, 500 contacts, 10 rules, 10 products	t	\N	2026-03-03 14:50:35.354468	9000	20	10	15
\.


ALTER TABLE public.subscription_plans ENABLE TRIGGER ALL;

--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 116, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, true);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: auto_reply_rules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auto_reply_rules_id_seq', 5, true);


--
-- Name: broadcasts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.broadcasts_id_seq', 1, false);


--
-- Name: business_hours_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.business_hours_id_seq', 7, true);


--
-- Name: campaign_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.campaign_logs_id_seq', 1, false);


--
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clients_id_seq', 6, true);


--
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contacts_id_seq', 3, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 23, true);


--
-- Name: django_celery_beat_clockedschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_clockedschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_crontabschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_crontabschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_intervalschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_intervalschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_periodictask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_periodictask_id_seq', 1, false);


--
-- Name: django_celery_beat_solarschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_solarschedule_id_seq', 1, false);


--
-- Name: django_celery_results_chordcounter_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_results_chordcounter_id_seq', 1, false);


--
-- Name: django_celery_results_groupresult_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_results_groupresult_id_seq', 1, false);


--
-- Name: django_celery_results_taskresult_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_results_taskresult_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 29, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 57, true);


--
-- Name: email_campaigns_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.email_campaigns_id_seq', 1, false);


--
-- Name: email_campaigns_selected_clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.email_campaigns_selected_clients_id_seq', 1, false);


--
-- Name: message_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.message_logs_id_seq', 43, true);


--
-- Name: message_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.message_templates_id_seq', 3, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: payment_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payment_logs_id_seq', 8, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: subscription_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subscription_plans_id_seq', 3, true);


--
-- PostgreSQL database dump complete
--

\unrestrict X6FWe5THTpOcXyo4ebfrUc5Wk86VziBvRUHzD2OQJCTBGvm3L6vcyQZRJmdbDVc

